import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from datenfutter.provenance import archive_retrieval


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'project'
        self.retrieved_at = '2020-03-01T10:30:00+01:00'
        self.metadata = {
            'source_id': 'official-table',
            'url': 'https://example.org/api/table?geo=DE&unit=PC',
            'query': {'geo': ['DE'], 'unit': 'PC'},
            'producer': 'National statistical office',
            'distributor': 'Official data portal',
            'dataset': 'official-table',
            'filters': {'geo': ['DE'], 'unit': 'PC'},
            'unit': 'percent',
            'coverage': {'start': '2016', 'end': '2019'},
            'vintage': '2020-02-29',
            'status': 'published estimates',
            'access_status': 'success',
            'http_status': 200,
            'transformations': ['scripts/prepare_example.py'],
        }

    def archive(self, **kwargs):
        options = {'metadata': self.metadata, 'retrieved_at': self.retrieved_at,
                   'raw': b'abc', 'filename': 'response.bin'}
        options.update(kwargs)
        return archive_retrieval(self.root, **options)

    def records(self):
        return [json.loads(line) for line in
                (self.root / 'sources/retrievals.jsonl').read_text().splitlines()]

    def test_preserves_raw_bytes_hash_and_original_retrieval_time(self):
        before = datetime.now(timezone.utc)
        record = self.archive(retrieval_id='original-retrieval')
        after = datetime.now(timezone.utc)
        self.assertEqual(record['retrieved_at'], '2020-03-01T10:30:00+01:00')
        self.assertLessEqual(before, datetime.fromisoformat(record['archived_at']))
        self.assertLessEqual(datetime.fromisoformat(record['archived_at']), after)
        self.assertEqual(record['raw'], {
            'path': 'sources/raw/original-retrieval/response.bin',
            'sha256': 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
            'size_bytes': 3,
        })
        self.assertEqual((self.root / record['raw']['path']).read_bytes(), b'abc')
        self.assertEqual(self.records(), [record])
        self.assertEqual(record['metadata'], self.metadata)

    def test_archives_a_local_path_without_changing_its_bytes(self):
        original = Path(self.tmp.name) / 'download.json'
        original.write_bytes(b'{"value":1}\r\n\x00')
        record = self.archive(raw=original, filename=None)
        self.assertEqual(Path(record['raw']['path']).name, 'download.json')
        self.assertEqual((self.root / record['raw']['path']).read_bytes(),
                         b'{"value":1}\r\n\x00')
        self.assertEqual(original.read_bytes(), b'{"value":1}\r\n\x00')

    def test_repeated_content_gets_distinct_ids_and_appends_without_rewriting(self):
        first = self.archive()
        log = self.root / 'sources/retrievals.jsonl'
        original_log = log.read_bytes()
        second = self.archive()
        self.assertNotEqual(first['retrieval_id'], second['retrieval_id'])
        self.assertNotEqual(first['raw']['path'], second['raw']['path'])
        self.assertTrue(log.read_bytes().startswith(original_log))
        self.assertEqual(self.records(), [first, second])

    def test_reused_id_cannot_overwrite_raw_or_existing_log(self):
        first = self.archive(retrieval_id='stable-id')
        log = self.root / 'sources/retrievals.jsonl'
        original_log = log.read_bytes()
        with self.assertRaises(FileExistsError):
            self.archive(retrieval_id='stable-id', raw=b'changed')
        self.assertEqual(log.read_bytes(), original_log)
        self.assertEqual((self.root / first['raw']['path']).read_bytes(), b'abc')

    def test_unsuccessful_access_is_logged_without_inventing_raw_data(self):
        metadata = {**self.metadata, 'access_status': 'blocked', 'http_status': 403}
        record = self.archive(metadata=metadata, raw=None, filename=None,
                              retrieval_id='blocked-request')
        self.assertIsNone(record['raw'])
        self.assertEqual(record['metadata']['access_status'], 'blocked')
        self.assertEqual(record['metadata']['http_status'], 403)
        self.assertEqual(self.records(), [record])
        original_log = (self.root / 'sources/retrievals.jsonl').read_bytes()
        with self.assertRaises(FileExistsError):
            self.archive(retrieval_id='blocked-request')
        self.assertEqual((self.root / 'sources/retrievals.jsonl').read_bytes(), original_log)

    def test_success_needs_raw_evidence_and_retrieval_time_needs_a_timezone(self):
        for options in ({'raw': None, 'filename': None},
                        {'retrieved_at': '2026-09-20'},
                        {'retrieved_at': '2026-09-20T10:00:00'},
                        {'retrieved_at': None}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.archive(**options)
        self.assertFalse(self.root.exists())

    def test_rejects_path_traversal_before_creating_output(self):
        for field in ('filename', 'retrieval_id'):
            for value in ('../escape', '/tmp/escape', 'sub/file', '..', r'sub\file'):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.archive(**{field: value})
        self.assertFalse(self.root.exists())

    def test_rejects_symlinked_output_directories_and_log(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        self.root.mkdir()
        sources = self.root / 'sources'
        sources.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.archive()
        sources.unlink()
        sources.mkdir()
        (sources / 'raw').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.archive()
        (sources / 'raw').unlink()
        outside_log = outside / 'external.jsonl'
        outside_log.write_bytes(b'keep this file unchanged\n')
        (sources / 'retrievals.jsonl').symlink_to(outside_log)
        with self.assertRaises(ValueError):
            self.archive()
        self.assertEqual(outside_log.read_bytes(), b'keep this file unchanged\n')
        self.assertEqual(list(outside.iterdir()), [outside_log])

    def test_hash_mismatch_cannot_be_published_as_an_archive(self):
        with self.assertRaises(ValueError):
            self.archive(expected_sha256='0' * 64)
        self.assertFalse(self.root.exists())
        record = self.archive(
            expected_sha256='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
        self.assertEqual((self.root / record['raw']['path']).read_bytes(), b'abc')

    def test_rejects_forged_generated_fields_and_credential_metadata(self):
        cases = [
            {'raw_sha256': '0' * 64},
            {'retrieved_at': '2026-09-20T00:00:00Z'},
            {'query': {'api_key': 'credential'}},
            {'url': 'https://example.org/api?access_token=credential'},
            {'url': 'https://user:credential@example.org/data'},
            {'url': 'https://example.org/data?X-Amz-Signature=credential'},
            {'url': 'https://example.org/data#access_token=credential'},
            {'query': 'dataset=table&token=credential'},
            {'query': ({'api_key': 'credential'},)},
        ]
        for extra in cases:
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.archive(metadata={**self.metadata, **extra})
        self.assertFalse(self.root.exists())

    def test_refuses_to_append_to_a_damaged_log(self):
        sources = self.root / 'sources'
        sources.mkdir(parents=True)
        log = sources / 'retrievals.jsonl'
        for damaged in (b'{"retrieval_id":"partial"}', b'not json\n'):
            log.write_bytes(damaged)
            with self.subTest(damaged=damaged), self.assertRaises(ValueError):
                self.archive()
            self.assertEqual(log.read_bytes(), damaged)
            self.assertFalse((sources / 'raw').exists())

    def test_parallel_retrievals_keep_complete_independent_log_records(self):
        with ThreadPoolExecutor(max_workers=4) as workers:
            records = list(workers.map(lambda _: self.archive(), range(8)))
        logged = self.records()
        self.assertEqual(len(logged), 8)
        self.assertEqual({r['retrieval_id'] for r in logged},
                         {r['retrieval_id'] for r in records})
        for record in logged:
            self.assertEqual((self.root / record['raw']['path']).read_bytes(), b'abc')


if __name__ == '__main__':
    unittest.main()
