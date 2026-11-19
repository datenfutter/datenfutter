"""Layout contracts using explicitly synthetic project inputs and output bytes."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from datenfutter.layout import check_layout
from test_projects import ROOT, fixture


def current_post(project):
    output = project / 'posts/de/example'
    output.mkdir(parents=True)
    for name in ('01.png', '01.svg', 'caption.md', 'alt-text.md', 'manifest.json'):
        (output / name).write_text('Synthetic layout fixture; not a production output.')
    return output


class LayoutTests(unittest.TestCase):
    def test_drafts_and_current_posts_have_distinct_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, _, _ = fixture(root)
            self.assertEqual(check_layout(root), (1, 0))
            current_post(project)
            fixture(root, 'draft')
            (root / 'projects/evidence-only/sources/raw').mkdir(parents=True)
            self.assertEqual(check_layout(root), (3, 1))

    def test_raw_archives_dates_and_source_images_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, _, _ = fixture(root)
            raw = project / 'sources/raw/2020-01-01/archives'
            raw.mkdir(parents=True)
            for name in ('source.zip', 'source.pdf', 'source.png', 'source.bak'):
                (raw / name).write_bytes(b'explicitly synthetic source fixture')
            self.assertEqual(check_layout(root), (1, 0))

    def test_obsolete_exports_and_stray_artifacts_fail(self):
        cases = [('outputs/old.png', 'Noncanonical root artifact'),
                 ('posts/legacy/01.png', 'Noncanonical root artifact'),
                 ('projects/sample/previews-2020-01-01/old.png', 'Obsolete output directory'),
                 ('projects/sample/plot.png', 'Artifact outside canonical'),
                 ('projects/sample/delivery.zip', 'Artifact outside canonical'),
                 ('projects/sample/specs/de/example.json.bak', 'Backup file')]
        for relative, message in cases:
            with self.subTest(path=relative), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                fixture(root)
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'explicitly synthetic obsolete artifact')
                with self.assertRaisesRegex(ValueError, message):
                    check_layout(root)

    def test_missing_extra_and_orphan_current_outputs_fail(self):
        for case in ('missing', 'extra', 'orphan'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                project, _, _ = fixture(root)
                output = current_post(project)
                if case == 'missing':
                    (output / '01.svg').unlink()
                elif case == 'extra':
                    (output / '02.png').write_bytes(b'synthetic obsolete slide')
                else:
                    output.rename(output.with_name('old-post'))
                with self.assertRaisesRegex(ValueError, 'output set|no canonical specification'):
                    check_layout(root)

    def test_noncanonical_specs_and_output_symlinks_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project, path, _ = fixture(root)
            path.rename(project / 'specs/post.json')
            with self.assertRaisesRegex(ValueError, 'Noncanonical specification'):
                check_layout(root)
            (project / 'specs/post.json').rename(path)
            (project / 'posts').symlink_to(root / 'build', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                check_layout(root)

    def test_cli_distinguishes_layout_from_reproduction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            result = subprocess.run([sys.executable, '-m', 'datenfutter', '--root', str(root),
                                     'layout'], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('1 project(s), 0 current post(s)', result.stdout)
            self.assertIn('Reproduction is checked separately', result.stdout)
            with self.assertRaisesRegex(ValueError, 'Not a Datenfutter root'):
                check_layout(root / 'missing')
