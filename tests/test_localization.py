"""Exercise both publications through real exported files; data are synthetic tests."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import test_editorial
from datenfutter.render import render_post

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / 'brand/palette-a.json'


class LocalizationTests(unittest.TestCase):
    def fixture(self, root):
        path, spec = test_editorial.EditorialTests().fixture(root)
        spec.update(language='en', publication='datafodder', caption_title='Category comparison')
        block = lambda text: {'text': text, 'source_ids': ['sample']}
        spec['caption'] = [block('A neutral example.')]
        spec['caption_methods'] = [block('Synthetic values for software tests only.')]
        slide = spec['slides'][0]
        slide.update(kicker='EXAMPLE', title='Category comparison',
                     subtitle=block('Synthetic test values, in points.'),
                     note=block('Software test only.'),
                     alt_text=block('Alpha: 2.5 points; Beta: 1.2 points.'))
        slide['chart']['series'][0]['label'] = 'Example'
        slide['chart']['y_limits'] = [0, 4]
        (root / 'values.csv').write_text('category,value\nAlpha,2.5\nBeta,1.2\n')
        cards = json.loads((root / 'sources.json').read_text())
        cards['sources'][0].update(publisher='Test source', title='Example values',
                                  short_title='Example values',
                                  retrieved_at='2026-09-19T10:00:00+00:00')
        (root / 'sources.json').write_text(json.dumps(cards))
        path.write_text(json.dumps(spec))
        return path, spec

    def test_english_exports_localize_labels_dates_numbers_and_captions(self):
        # A wrong locale branch or untranslated generated label is observable in exports.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, spec = self.fixture(root)
            for stacked in (False, True):
                with self.subTest(stacked=stacked):
                    spec['slides'][0]['chart']['stacked'] = stacked
                    path.write_text(json.dumps(spec))
                    render_post(path, root / 'out', BRAND)
                    svg = (root / 'out/01.svg').read_text()
                    caption = (root / 'out/caption.md').read_text()
                    alt = (root / 'out/alt-text.md').read_text()
                    self.assertIn('As of: 20 Sep 2026', svg)
                    self.assertIn('Sources and methods: full URLs in the caption.', svg)
                    self.assertIn('2.5', svg)
                    self.assertNotIn('2,5', svg)
                    self.assertIn('**Sources**', caption)
                    self.assertIn('Retrieved: 19 Sep 2026.', caption)
                    self.assertIn('https://example.org/data\n', caption)
                    self.assertLess(caption.index('Category comparison'), caption.index('A neutral example.'))
                    self.assertLess(caption.index('A neutral example.'), caption.index('**Sources**'))
                    self.assertLess(caption.index('**Sources**'), caption.index('**Methods**'))
                    self.assertTrue(alt.startswith('Slide 1: Alpha: 2.5'))
                    for german in ('Stand:', 'Quellen', 'Methoden', 'Abruf:', 'Folie 1:'):
                        self.assertNotIn(german, svg + caption + alt)
                    manifest = json.loads((root / 'out/manifest.json').read_text())
                    self.assertEqual(manifest['publication'], 'datafodder')
                    self.assertEqual(manifest['language'], 'en')
                    self.assertEqual(manifest['project'], 'datenfutter')
                    self.assertEqual(manifest['logo']['sha256'],
                                     hashlib.sha256((ROOT / 'brand/df-circle-white.png').read_bytes()).hexdigest())
                    self.assertIn('localization.py', manifest['renderer_files'])

    def test_german_defaults_keep_labels_and_record_datenfutter_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, _ = test_editorial.EditorialTests().fixture(root)
            render_post(path, root / 'out', BRAND)
            manifest = json.loads((root / 'out/manifest.json').read_text())
            self.assertEqual(manifest['publication'], 'datenfutter')
            self.assertIn('Stand: 20.09.2026', (root / 'out/01.svg').read_text())
            self.assertIn('Abruf: 20.09.2026', (root / 'out/caption.md').read_text())
            self.assertTrue((root / 'out/alt-text.md').read_text().startswith('Folie 1:'))

    def test_english_without_publication_is_identified_as_datafodder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, spec = self.fixture(root)
            spec.pop('publication')
            path.write_text(json.dumps(spec))
            render_post(path, root / 'out', BRAND)
            self.assertEqual(json.loads((root / 'out/manifest.json').read_text())['publication'], 'datafodder')

    def test_invalid_language_or_publication_preserves_previous_files(self):
        # A mistyped locale or mismatched publication must never silently render in another language.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, original = test_editorial.EditorialTests().fixture(root)
            render_post(path, root / 'out', BRAND)
            before = {p.name: p.read_bytes() for p in (root / 'out').iterdir()}
            invalid = [{'language': value} for value in ('fr', 'en-US', 7, {}, ['en'])]
            invalid += [{'language': 'en', 'publication': 'datenfutter'},
                        {'language': 'de', 'publication': 'datafodder'},
                        {'publication': 'unknown'}, {'publication': []}]
            for update in invalid:
                with self.subTest(update=update):
                    spec = {**copy.deepcopy(original), **update}
                    path.write_text(json.dumps(spec))
                    with self.assertRaisesRegex(ValueError, 'language|publication'):
                        render_post(path, root / 'out', BRAND)
                    self.assertEqual({p.name: p.read_bytes() for p in (root / 'out').iterdir()}, before)

    def test_language_switch_cannot_overwrite_same_id_in_same_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, _ = test_editorial.EditorialTests().fixture(root)
            render_post(path, root / 'out', BRAND)
            before = {p.name: p.read_bytes() for p in (root / 'out').iterdir()}
            path, _ = self.fixture(root)
            with self.assertRaisesRegex(ValueError, 'language'):
                render_post(path, root / 'out', BRAND)
            self.assertEqual({p.name: p.read_bytes() for p in (root / 'out').iterdir()}, before)
