import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree
from PIL import Image

from datenfutter.render import render_post

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/legacy'


class RenderTests(unittest.TestCase):
    def test_shorter_rerender_removes_only_obsolete_owned_slides(self):
        original = json.loads((FIXTURES / 'posts/ecb-2022-2025.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            spec = copy.deepcopy(original)
            spec['data_file'] = str(FIXTURES / 'data/ecb_deposit_facility.csv')
            spec['sources_file'] = str(FIXTURES / 'research/sources.json')
            path, out = Path(tmp) / 'spec.json', Path(tmp) / 'out'
            path.write_text(json.dumps(spec))
            render_post(path, out, ROOT / 'brand/brand.json')
            (out / 'editor-note.txt').write_text('keep this')
            spec['slides'] = spec['slides'][:1]
            path.write_text(json.dumps(spec))
            render_post(path, out, ROOT / 'brand/brand.json')
            self.assertFalse((out / '02.png').exists())
            self.assertFalse((out / '02.svg').exists())
            self.assertEqual((out / 'editor-note.txt').read_text(), 'keep this')

    def test_failed_rerender_preserves_previous_complete_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'out'
            render_post(FIXTURES / 'posts/ecb-2022-2025.json', out, ROOT / 'brand/brand.json')
            before = {p.name: p.read_bytes() for p in out.iterdir()}
            spec = json.loads((FIXTURES / 'posts/ecb-2022-2025.json').read_text())
            spec['data_file'] = str(FIXTURES / 'data/ecb_deposit_facility.csv')
            spec['sources_file'] = str(FIXTURES / 'research/sources.json')
            spec['slides'][1]['title'] = 'too long ' * 100
            path = Path(tmp) / 'invalid.json'
            path.write_text(json.dumps(spec))
            with self.assertRaises(ValueError):
                render_post(path, out, ROOT / 'brand/brand.json')
            self.assertEqual({p.name: p.read_bytes() for p in out.iterdir()}, before)

    def test_real_post_exports_exact_canvas_and_auditable_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'post'
            files = render_post(FIXTURES / 'posts/ecb-2022-2025.json', out, ROOT / 'brand/brand.json')
            self.assertEqual(len(list(out.glob('*.png'))), 2)
            self.assertEqual(len(list(out.glob('*.svg'))), 2)
            for p in out.glob('*.png'):
                with Image.open(p) as im:
                    self.assertEqual(im.size, (1080, 1350))
            for p in out.glob('*.svg'):
                self.assertTrue(ElementTree.parse(p).getroot().tag.endswith('svg'))
            manifest = json.loads((out / 'manifest.json').read_text())
            self.assertEqual(manifest['data']['sha256'], hashlib.sha256((FIXTURES / 'data/ecb_deposit_facility.csv').read_bytes()).hexdigest())
            self.assertEqual(manifest['slides'][1]['values'], [2.5, 2.0, -1.0, -1.0])
            self.assertIn('ecb.europa.eu', (out / 'caption.md').read_text())
            self.assertIn('percentage points', (out / 'alt-text.md').read_text())
            self.assertEqual(len(files), 7)

    def test_overlong_headline_and_unknown_chart_fail_before_export(self):
        original = json.loads((FIXTURES / 'posts/ecb-2022-2025.json').read_text())
        for change in ({'title': 'A very long headline ' * 30}, {'chart': {'type': 'mystery'}}):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                spec = copy.deepcopy(original)
                spec['data_file'] = str(FIXTURES / 'data/ecb_deposit_facility.csv')
                spec['sources_file'] = str(FIXTURES / 'research/sources.json')
                spec['slides'][0].update(change)
                path = Path(tmp) / 'spec.json'
                path.write_text(json.dumps(spec))
                with self.assertRaises(ValueError):
                    render_post(path, Path(tmp) / 'out', ROOT / 'brand/brand.json')
                self.assertFalse((Path(tmp) / 'out' / '01.png').exists())


if __name__ == '__main__':
    unittest.main()
