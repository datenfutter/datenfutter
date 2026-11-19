"""Project workflow tests; all new project data are explicitly synthetic."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_editorial
from datenfutter.projects import build_projects, check_projects, select_projects

ROOT = Path(__file__).resolve().parents[1]


def fixture(root, name='sample'):
    if not (root / 'brand').exists():
        shutil.copytree(ROOT / 'brand', root / 'brand')
    project = root / 'projects' / name
    project.mkdir(parents=True)
    path, spec = test_editorial.EditorialTests().fixture(project)
    (project / 'data/processed').mkdir(parents=True)
    (project / 'sources').mkdir()
    (project / 'specs/de').mkdir(parents=True)
    (project / 'values.csv').rename(project / 'data/processed/values.csv')
    (project / 'sources.json').rename(project / 'sources/source-register.json')
    spec['sources_file'] = '../../sources/source-register.json'
    spec['logo_file'] = '../../../../brand/df-circle-white.png'
    spec['slides'][0]['chart']['series'][0]['data_file'] = '../../data/processed/values.csv'
    path.unlink()
    path = project / 'specs/de/example.json'
    path.write_text(json.dumps(spec, ensure_ascii=False))
    return project, path, spec


class ProjectBuildTests(unittest.TestCase):
    def test_cli_builds_a_project_and_leaves_current_posts_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, _, _ = fixture(root)
            (project / 'posts').mkdir()
            (project / 'posts/current-note.txt').write_text('preserve')
            result = subprocess.run([sys.executable, '-m', 'datenfutter', '--root', str(root),
                                     'build', 'sample'], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / 'build/projects/sample/posts/de/example/01.png').is_file())
            self.assertEqual((project / 'posts/current-note.txt').read_text(), 'preserve')

    def test_all_selects_only_projects_with_canonical_specs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root, 'alpha')
            fixture(root, 'beta')
            (root / 'projects/notes').mkdir()
            names = select_projects(root, all_projects=True)
            self.assertEqual(names, ['alpha', 'beta'])
            self.assertEqual(len(build_projects(root, names)), 10)

    def test_preparation_runs_only_in_the_disposable_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, _, _ = fixture(root)
            data = project / 'data/processed/values.csv'
            before = data.read_bytes()
            prepared = 'category,value\nAlpha,3.0\nBeta,-1.2\n'
            (project / 'prepare.py').write_text(
                'from pathlib import Path\n'
                f'(Path(__file__).parent / "data/processed/values.csv").write_text({prepared!r})\n')
            build_projects(root, ['sample'])
            manifest = json.loads((root / 'build/projects/sample/posts/de/example/manifest.json').read_text())
            self.assertEqual(manifest['data_files'][0]['sha256'], hashlib.sha256(prepared.encode()).hexdigest())
            self.assertEqual(data.read_bytes(), before)

    def test_failed_render_or_preparation_preserves_previous_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, path, spec = fixture(root)
            files = build_projects(root, ['sample'])
            before = {p: p.read_bytes() for p in files}
            spec['slides'][0]['title'] = 'Too much title text ' * 100
            path.write_text(json.dumps(spec))
            with self.assertRaises(ValueError):
                build_projects(root, ['sample'])
            self.assertEqual({p: p.read_bytes() for p in files}, before)
            (project / 'prepare.py').write_text('raise RuntimeError("test failure")\n')
            with self.assertRaisesRegex(ValueError, 'Preparation failed'):
                build_projects(root, ['sample'])
            self.assertEqual({p: p.read_bytes() for p in files}, before)

    def test_empty_missing_and_ambiguous_selection_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for kwargs in ({'all_projects': True}, {'project': 'missing'},
                           {'project': '../outside'}, {'project': 'sample', 'all_projects': True}):
                with self.subTest(selection=kwargs), self.assertRaises(ValueError):
                    select_projects(root, **kwargs)

    def test_cli_reports_malformed_input_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, path, spec = fixture(root)
            spec['slides'][0]['chart']['type'] = 'unknown'
            path.write_text(json.dumps(spec))
            result = subprocess.run([sys.executable, '-m', 'datenfutter', '--root', str(root),
                                     'build', 'sample'], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('Error:', result.stderr)
            self.assertNotIn('Traceback', result.stderr)

    def test_preview_symlink_cannot_redirect_writes_to_current_posts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            (root / 'build').symlink_to(root / 'projects', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                build_projects(root, ['sample'])


class ProjectCheckTests(unittest.TestCase):
    def current_fixture(self, root):
        project, _, _ = fixture(root)
        built = build_projects(root, ['sample'])
        for path in built:
            destination = root / 'projects' / path.relative_to(root / 'build/projects')
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
        return project

    def test_matching_outputs_pass_without_overwriting_current_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self.current_fixture(root)
            before = {p: p.read_bytes() for p in (project / 'posts').rglob('*') if p.is_file()}
            self.assertEqual(check_projects(root, ['sample']), (['sample'], []))
            self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_missing_extra_and_changed_outputs_fail_without_being_repaired(self):
        for failure in ['missing', 'extra', 'changed']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                project = self.current_fixture(root)
                output = project / 'posts/de/example'
                if failure == 'missing':
                    (output / '01.svg').unlink()
                elif failure == 'extra':
                    (output / 'old-copy.png').write_bytes(b'not an image; synthetic test')
                else:
                    (output / 'caption.md').write_text('Changed synthetic test caption.')
                before = {p: p.read_bytes() for p in output.iterdir()}
                with self.assertRaisesRegex(ValueError, failure + ':'):
                    check_projects(root, ['sample'])
                self.assertEqual({p: p.read_bytes() for p in output.iterdir()}, before)

    def test_drafts_are_reported_but_an_empty_comparison_never_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root, 'draft')
            with self.assertRaisesRegex(ValueError, 'No current outputs'):
                check_projects(root, ['draft'], allow_drafts=True)
            self.current_fixture(root)
            self.assertEqual(check_projects(root, ['draft', 'sample'], allow_drafts=True),
                             (['sample'], ['draft']))

    def test_cli_check_fails_for_changed_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self.current_fixture(root)
            (project / 'posts/de/example/alt-text.md').write_text('changed')
            result = subprocess.run([sys.executable, '-m', 'datenfutter', '--root', str(root),
                                     'check', 'sample'], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('changed: sample/posts/de/example/alt-text.md', result.stderr)

    def test_current_output_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self.current_fixture(root)
            (root / 'unrelated.txt').write_text('unrelated')
            (project / 'posts/de/example/link.txt').symlink_to(root / 'unrelated.txt')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                check_projects(root, ['sample'])
