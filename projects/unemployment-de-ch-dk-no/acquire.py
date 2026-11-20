"""Retrieve a new Eurostat candidate; never change the selected snapshot."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from datenfutter.provenance import archive_retrieval


def acquire(project=None):
    project = Path(project or Path(__file__).resolve().parent)
    register = json.loads((project / 'sources/source-register.json').read_text())
    source = next(s for s in register['sources'] if s['id'] == 'eurostat-une-rt-a')
    metadata = {
        'source_id': source['id'],
        'producer': 'National statistical institutes (EU-LFS)',
        'distributor': 'Eurostat', 'dataset': 'une_rt_a',
        'url': source['download_url'],
        'filters': {**register['selection']['dimensions'],
                    'geo': register['selection']['countries'],
                    'sinceTimePeriod': '2015', 'untilTimePeriod': '2025'},
        'unit': '% of labour force', 'coverage': '2015–2025',
        'vintage': None, 'status': 'Candidate; not yet selected or reviewed',
        'access_status': 'error', 'transformations': ['prepare.py'],
    }
    raw = None
    try:
        request = Request(source['download_url'], headers={'Accept': 'application/json'})
        with urlopen(request, timeout=45) as response:
            raw = response.read(2_000_001)
            metadata['http_status'] = response.status
        if len(raw) > 2_000_000:
            raise ValueError('Response exceeds this bounded four-country query.')
        payload = json.loads(raw)
        if payload.get('class') != 'dataset' or payload.get('extension', {}).get('id') != 'UNE_RT_A':
            raise ValueError('Unexpected Eurostat response; inspect the new receipt.')
        metadata.update(access_status='success', vintage=payload.get('updated'))
    except Exception as exc:
        metadata['failure_type'] = type(exc).__name__
        archive_retrieval(project, metadata=metadata,
                          retrieved_at=datetime.now(timezone.utc).isoformat(),
                          raw=raw, filename='response.json' if raw is not None else None)
        raise
    record = archive_retrieval(project, metadata=metadata,
                               retrieved_at=datetime.now(timezone.utc).isoformat(),
                               raw=raw, filename='une_rt_a.json')
    print(json.dumps(record, ensure_ascii=False, indent=2))
    print('Candidate archived. Review values/flags before updating source-register.json and the specification.')
    return record


if __name__ == '__main__':
    acquire()
