"""Verify configured type sizes in actual rendered SVGs, including both axes."""
import copy
import hashlib
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import test_editorial
from datenfutter.render import render_post

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/legacy'
SVG = '{http://www.w3.org/2000/svg}'


class TypographyTests(unittest.TestCase):
    def fixture(self, root):
        path, spec = test_editorial.EditorialTests().fixture(root)
        brand = json.loads((ROOT / 'brand/brand.json').read_text())
        brand.pop('typography', None)
        return path, spec, brand

    def assert_sizes(self, svg_path, title, subtitle, expected):
        document = ET.parse(svg_path)
        labels = {''.join(node.itertext()): node for node in document.iter(SVG + 'text')}
        def size(node):
            match = re.search(r'font-size:\s*([\d.]+)px', node.attrib['style'])
            return float(match.group(1))
        self.assertAlmostEqual(size(labels[title]), expected[0])
        self.assertAlmostEqual(size(labels[subtitle]), expected[1])
        for axis in ('xtick_', 'ytick_'):
            ticks = [text for group in document.iter(SVG + 'g')
                     if group.attrib.get('id', '').startswith(axis)
                     for text in group.iter(SVG + 'text')]
            self.assertTrue(ticks, axis)
            for tick in ticks:
                self.assertAlmostEqual(size(tick), expected[2])

    def test_explicit_sizes_reach_title_subtitle_and_both_chart_axes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, spec, brand = self.fixture(root)
            brand['typography'] = {'title_px': 50, 'subtitle_px': 22, 'axis_tick_px': 23}
            config = root / 'brand.json'
            config.write_text(json.dumps(brand))
            for orientation in ('horizontal', 'vertical'):
                spec['slides'][0]['chart']['orientation'] = orientation
                path.write_text(json.dumps(spec))
                render_post(path, root / 'out', config)
                self.assert_sizes(root / 'out/01.svg', 'Vergleich von Kategorien',
                                  'Synthetische Testdaten, in Punkten. [1]', (30, 13.2, 13.8))

    def test_palette_inherits_shared_sizes_and_can_override_one_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, spec, brand = self.fixture(root)
            palette = copy.deepcopy(brand)
            brand['typography'] = {'title_px': 50, 'subtitle_px': 22, 'axis_tick_px': 23}
            base = root / 'brand.json'
            base.write_text(json.dumps(brand))
            config = root / 'palette-b.json'
            for override, title_size in (({}, 30), ({'title_px': 54}, 32.4)):
                palette['typography'] = override
                config.write_text(json.dumps(palette))
                render_post(path, root / 'out', config)
                self.assert_sizes(root / 'out/01.svg', 'Vergleich von Kategorien',
                                  'Synthetische Testdaten, in Punkten. [1]', (title_size, 13.2, 13.8))
                manifest = json.loads((root / 'out/manifest.json').read_text())
                self.assertEqual(manifest['typography_base']['sha256'],
                                 hashlib.sha256(base.read_bytes()).hexdigest())
                self.assertEqual(manifest['typography']['axis_tick_px'], 23)

    def test_missing_typography_keeps_existing_editorial_sizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, spec, brand = self.fixture(root)
            config = root / 'standalone.json'
            config.write_text(json.dumps(brand))
            render_post(path, root / 'out', config)
            self.assert_sizes(root / 'out/01.svg', 'Vergleich von Kategorien',
                              'Synthetische Testdaten, in Punkten. [1]', (34.8, 15, 12.6))

    def test_legacy_renderer_uses_the_same_size_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, _, brand = self.fixture(root)
            brand['typography'] = {'title_px': 50, 'subtitle_px': 22, 'axis_tick_px': 23}
            config = root / 'brand.json'
            config.write_text(json.dumps(brand))
            path = FIXTURES / 'posts/ecb-2022-2025.json'
            slide = json.loads(path.read_text())['slides'][0]
            render_post(path, root / 'out', config)
            self.assert_sizes(root / 'out/01.svg', slide['title'].split('\n')[0],
                              slide['subtitle'].split('\n')[0], (30, 13.2, 13.8))

    def test_invalid_sizes_do_not_replace_an_existing_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, spec, brand = self.fixture(root)
            config = root / 'brand.json'
            config.write_text(json.dumps(brand))
            render_post(path, root / 'out', config)
            before = {p.name: p.read_bytes() for p in (root / 'out').iterdir()}
            invalid = [None, [], {'unknown_px': 25}]
            invalid += [{'axis_tick_px': value} for value in (0, -1, True, '21', None, float('nan'), float('inf'))]
            for typography in invalid:
                with self.subTest(typography=typography):
                    brand['typography'] = typography
                    config.write_text(json.dumps(brand))
                    with self.assertRaisesRegex(ValueError, 'typography'):
                        render_post(path, root / 'out', config)
                    self.assertEqual({p.name: p.read_bytes() for p in (root / 'out').iterdir()}, before)
