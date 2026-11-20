"""Protect the raw-only, offline production verification boundary."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'projects/unemployment-de-ch-dk-no'
MODULE_SPEC = importlib.util.spec_from_file_location('unemployment_verify', PROJECT / 'verify.py')
MODULE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(MODULE)


def snapshot(directory):
    return {path.relative_to(directory): path.read_bytes()
            for path in directory.rglob('*') if path.is_file()}


class UnemploymentVerifyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / 'projects' / PROJECT.name

    def minimal_project(self, prepare_body):
        (self.project / 'sources').mkdir(parents=True)
        (self.project / 'sources/evidence.txt').write_text('Synthetic test evidence.\n')
        (self.project / 'data/processed').mkdir(parents=True)
        (self.project / 'data/processed/saved.csv').write_text('date,value\n2025-01-01,1\n')
        (self.project / 'prepare.py').write_text(prepare_body)

    def test_current_production_files_reproduce_without_modifying_inputs(self):
        shutil.copytree(PROJECT, self.project, ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT / 'brand', self.root / 'brand')
        before_project = snapshot(self.project)
        before_brand = snapshot(self.root / 'brand')
        result = MODULE.verify(self.project)
        self.assertEqual(result, {'derived_files': 6, 'posts': 1, 'output_files': 5})
        self.assertEqual(snapshot(self.project), before_project)
        self.assertEqual(snapshot(self.root / 'brand'), before_brand)
        self.assertEqual(list((self.root / 'build').iterdir()), [])

    def test_full_file_comparison_rejects_missing_extra_and_changed_bytes(self):
        for label in ('data/processed', 'posts'):
            for difference in ('missing', 'extra', 'changed'):
                with self.subTest(label=label, difference=difference):
                    case = self.root / label / difference
                    rebuilt, current = case / 'rebuilt', case / 'current'
                    rebuilt.mkdir(parents=True)
                    current.mkdir()
                    for directory in (rebuilt, current):
                        (directory / 'first.txt').write_bytes(b'one\n')
                        (directory / 'second.txt').write_bytes(b'two\n')
                    if difference == 'missing':
                        (current / 'first.txt').unlink()
                    elif difference == 'extra':
                        (current / 'unexpected.txt').write_bytes(b'extra\n')
                    else:
                        (current / 'first.txt').write_bytes(b'changed\n')
                    before = snapshot(current)
                    with self.assertRaisesRegex(ValueError, difference + ':'):
                        MODULE._compare(rebuilt, current, label)
                    self.assertEqual(snapshot(current), before)

    def test_zero_output_sets_never_pass(self):
        rebuilt, current = self.root / 'rebuilt', self.root / 'current'
        rebuilt.mkdir()
        current.mkdir()
        with self.assertRaisesRegex(ValueError, 'empty output sets fail'):
            MODULE._compare(rebuilt, current, 'posts')
        (current / 'saved.txt').write_bytes(b'Existing outputs cannot fill an empty rebuild.')
        with self.assertRaisesRegex(ValueError, 'empty output sets fail'):
            MODULE._compare(rebuilt, current, 'data/processed')

    def test_noop_preparation_cannot_reuse_existing_processed_data(self):
        self.minimal_project(
            'def prepare(project_dir):\n'
            '    assert not (project_dir / "data").exists()\n'
            '    assert not (project_dir / "specs").exists()\n'
            '    assert not (project_dir / "posts").exists()\n'
            '    assert not (project_dir.parents[1] / "brand").exists()\n')
        before = snapshot(self.project)
        with self.assertRaisesRegex(ValueError, 'Missing verification directory'):
            MODULE.verify(self.project)
        self.assertEqual(snapshot(self.project), before)
        self.assertEqual(list((self.root / 'build').iterdir()), [])

    def test_preparation_network_attempts_are_blocked(self):
        bodies = {
            'connect': ('    with socket.socket() as connection:\n'
                        '        connection.connect(("127.0.0.1", 9))\n'),
            'connect_ex': ('    with socket.socket() as connection:\n'
                           '        connection.connect_ex(("127.0.0.1", 9))\n'),
            'create_connection': '    socket.create_connection(("127.0.0.1", 9))\n',
        }
        self.minimal_project('def prepare(project_dir):\n    pass\n')
        for operation, body in bodies.items():
            with self.subTest(operation=operation):
                (self.project / 'prepare.py').write_text(
                    'import socket\n\ndef prepare(project_dir):\n' + body)
                before = snapshot(self.project)
                with self.assertRaisesRegex(RuntimeError, 'Network access is disabled'):
                    MODULE.verify(self.project)
                self.assertEqual(snapshot(self.project), before)
                self.assertEqual(list((self.root / 'build').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
