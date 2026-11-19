"""Archive local source evidence and append an honest retrieval receipt.

This module does not retrieve data or infer when a retrieval happened. Callers
must supply the actual, timezone-aware timestamp of the attempt. Old evidence
keeps its original retrieval timestamp when archived later.
"""

import fcntl
import hashlib
import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit
from uuid import uuid4


_REQUIRED_METADATA = {
    'source_id', 'producer', 'distributor', 'dataset', 'filters', 'unit',
    'coverage', 'vintage', 'status', 'access_status', 'transformations',
}
_GENERATED_FIELDS = {
    'schema_version', 'retrieval_id', 'retrieved_at', 'archived_at',
    'raw', 'raw_file', 'raw_sha256', 'raw_size', 'sha256', 'size_bytes',
}
_SECRET_KEYS = {
    'authorization', 'proxyauthorization', 'apikey', 'key', 'token',
    'accesstoken', 'refreshtoken', 'idtoken', 'password', 'passwd',
    'secret', 'clientsecret', 'cookie', 'setcookie', 'signature', 'sig',
    'credential', 'credentials', 'xamzcredential', 'xamzsignature',
    'xamzsecuritytoken', 'xgoogcredential', 'xgoogsignature',
}
_ACCESS_STATUSES = {'success', 'partial', 'blocked', 'unavailable', 'error'}


def _safe_name(value, label):
    if not isinstance(value, str) or not re.fullmatch(
            r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', value):
        raise ValueError(f'{label} must be a simple filename or identifier, without paths')
    return value


def _secret_key(value):
    return re.sub(r'[^a-z0-9]', '', value.lower()) in _SECRET_KEYS


def _check_public_metadata(value):
    """Reject common credential fields; never echo their values in errors."""
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError('Metadata keys must be strings')
            if _secret_key(key):
                raise ValueError('Remove credentials from metadata before archiving')
            _check_public_metadata(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _check_public_metadata(item)
    elif isinstance(value, str):
        decoded = unquote(value)
        for key in re.findall(r'(?:^|[?#&;\s])([\w-]+)\s*[:=]', decoded):
            if _secret_key(key):
                raise ValueError('Remove credentials from metadata before archiving')
        if re.search(r'\bBearer\s+\S+', decoded, flags=re.IGNORECASE):
            raise ValueError('Remove credentials from metadata before archiving')
        for url in re.findall(r'https?://[^\s]+', decoded):
            parts = urlsplit(url)
            if parts.username is not None or parts.password is not None:
                raise ValueError('Remove URL credentials before archiving')
            if any(_secret_key(key) for key, _ in parse_qsl(parts.query)):
                raise ValueError('Remove signed or credential-bearing URLs before archiving')


def _metadata_copy(metadata):
    if not isinstance(metadata, dict):
        raise ValueError('metadata must be a dictionary')
    if _REQUIRED_METADATA - metadata.keys():
        missing = ', '.join(sorted(_REQUIRED_METADATA - metadata.keys()))
        raise ValueError(f'Missing retrieval metadata: {missing}')
    if _GENERATED_FIELDS & metadata.keys():
        raise ValueError('Generated receipt fields cannot be supplied in metadata')
    for field in ('source_id', 'producer', 'distributor', 'dataset'):
        if not isinstance(metadata[field], str) or not metadata[field].strip():
            raise ValueError(f'{field} must identify the source or explicitly state unknown')
    if not metadata.get('url') and not metadata.get('query'):
        raise ValueError('A public URL or exact credential-free query is required')
    if metadata['access_status'] not in _ACCESS_STATUSES:
        raise ValueError('Unsupported access_status')
    if not isinstance(metadata['transformations'], list):
        raise ValueError('transformations must be a list of references; use [] when none')
    _check_public_metadata(metadata)
    try:
        return json.loads(json.dumps(metadata, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ValueError('Metadata must contain finite JSON values') from exc


def _directory(path):
    if path.is_symlink():
        raise ValueError('Archive output directories must not be symlinks')
    path.mkdir(exist_ok=True)
    if not path.is_dir():
        raise ValueError('Archive output must be a directory')


def _existing_ids(log):
    log.seek(0)
    content = log.read()
    if content and not content.endswith(b'\n'):
        raise ValueError('Retrieval log has an incomplete final record; preserve it for review')
    ids = set()
    for line in content.splitlines():
        try:
            record = json.loads(line)
            retrieval_id = _safe_name(record['retrieval_id'], 'retrieval_id')
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError('Retrieval log is invalid; do not rewrite its history') from exc
        if retrieval_id in ids:
            raise ValueError('Retrieval log already contains a duplicate retrieval_id')
        ids.add(retrieval_id)
    return ids


def archive_retrieval(project_dir, *, metadata, retrieved_at, raw=None,
                      filename=None, retrieval_id=None, expected_sha256=None):
    """Preserve raw bytes/path and append one record to sources/retrievals.jsonl.

    ``retrieved_at`` is the actual attempt time as an ISO 8601 string with a
    timezone, supplied from the retrieval or its original receipt. It is never
    replaced with the current time. ``archived_at`` records this local archive.

    ``metadata`` identifies producer, distributor, dataset, filters, unit,
    coverage, vintage, source status, access status and transformation references.
    Unknown vintage/status/coverage may be explicit JSON null. An unsuccessful
    attempt may have ``raw=None``; a successful/partial extract must retain bytes.
    Raw bytes are not cleaned, parsed or inspected for secrets: supply only
    suitable source response content, never credential-bearing request envelopes.

    New IDs are generated for repeated content. Explicit reused IDs, unsafe
    paths, supplied hashes that disagree with the bytes, and damaged logs fail
    without replacing existing evidence. Concurrent Linux writers serialize on
    the log. No existing log record or raw file is edited by this function.
    """
    if not isinstance(retrieved_at, str):
        raise ValueError('An explicit actual retrieved_at timestamp is required')
    try:
        actual_time = datetime.fromisoformat(retrieved_at)
    except ValueError as exc:
        raise ValueError('retrieved_at must be an ISO 8601 timestamp with timezone') from exc
    if actual_time.utcoffset() is None:
        raise ValueError('retrieved_at must include its actual timezone')
    metadata = _metadata_copy(metadata)
    retrieval_id = _safe_name(retrieval_id if retrieval_id is not None else uuid4().hex,
                              'retrieval_id')
    if isinstance(raw, (str, os.PathLike)):
        source = Path(raw)
        payload = source.read_bytes()
        if filename is None:
            filename = source.name
    elif isinstance(raw, bytes) or raw is None:
        payload = raw
    else:
        raise ValueError('raw must be bytes, a local file path, or None')
    if payload is None:
        if metadata['access_status'] in {'success', 'partial'}:
            raise ValueError('Successful or partial retrievals require archived raw bytes')
        if filename is not None or expected_sha256 is not None:
            raise ValueError('An attempt without raw bytes cannot have a filename or hash')
        raw_record = None
    else:
        filename = _safe_name(filename if filename is not None else 'response.bin', 'filename')
        digest = hashlib.sha256(payload).hexdigest()
        if expected_sha256 is not None and expected_sha256 != digest:
            raise ValueError('Raw bytes do not match expected_sha256; nothing was archived')
        raw_record = {
            'path': f'sources/raw/{retrieval_id}/{filename}',
            'sha256': digest,
            'size_bytes': len(payload),
        }

    root = Path(project_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    sources = root / 'sources'
    _directory(sources)
    raw_root = sources / 'raw'
    log_path = sources / 'retrievals.jsonl'
    if raw_root.is_symlink() or log_path.is_symlink():
        raise ValueError('Archive output paths must not be symlinks')
    fd = os.open(log_path, os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, 'a+b') as log:
        file_stat = os.fstat(log.fileno())
        if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
            raise ValueError('The retrieval log must be a regular file without hard links')
        fcntl.flock(log.fileno(), fcntl.LOCK_EX)
        if retrieval_id in _existing_ids(log) or (raw_root / retrieval_id).exists():
            raise FileExistsError('retrieval_id already exists; existing evidence is unchanged')
        if payload is not None:
            _directory(raw_root)
            retrieval_dir = raw_root / retrieval_id
            retrieval_dir.mkdir()
            with (retrieval_dir / filename).open('xb') as archived:
                archived.write(payload)
                archived.flush()
                os.fsync(archived.fileno())
        record = {
            'schema_version': 1,
            'retrieval_id': retrieval_id,
            'retrieved_at': retrieved_at,
            'archived_at': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata,
            'raw': raw_record,
        }
        log.write((json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8'))
        log.flush()
        os.fsync(log.fileno())
        return record
