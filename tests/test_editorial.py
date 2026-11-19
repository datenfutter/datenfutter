import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from datenfutter.render import render_post

ROOT = Path(__file__).resolve().parents[1]


class EditorialTests(unittest.TestCase):
    def test_caption_orders_title_synopsis_sources_then_cited_methods(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            path,spec=self.fixture(root)
            spec['caption_title']='Ein Vergleich mit Kontext'
            spec['caption_methods']=[{'text':'Die Werte sind synthetisch.', 'source_ids':['sample']}]
            path.write_text(json.dumps(spec))
            render_post(path,root/'out',ROOT/'brand/palette-a.json')
            caption=(root/'out/caption.md').read_text()
            self.assertTrue(caption.startswith('**Ein Vergleich mit Kontext**\n\n'))
            self.assertLess(caption.index('Ein neutraler Beispieltext.'),caption.index('**Quellen**'))
            self.assertLess(caption.index('https://example.org/data'),caption.index('**Methoden**'))
            self.assertIn('Die Werte sind synthetisch. [1]',caption)
            before=(root/'out/caption.md').read_bytes()
            spec['caption_methods'][0]['source_ids']=['unknown']
            path.write_text(json.dumps(spec))
            with self.assertRaises(ValueError):
                render_post(path,root/'out',ROOT/'brand/palette-a.json')
            self.assertEqual((root/'out/caption.md').read_bytes(),before)

    def fixture(self, root):
        (root / 'values.csv').write_text('category,value\nAlpha,2.5\nBeta,-1.2\n', encoding='utf-8')
        (root / 'sources.json').write_text(json.dumps({'sources': [{
            'id': 'sample', 'publisher': 'Testquelle', 'title': 'Beispielwerte',
            'short_title': 'Beispielwerte', 'url': 'https://example.org/data',
            'retrieved_at': '2026-09-20T10:00:00+00:00',
            'coverage_end': '2025-12-31', 'metric': 'Beispiel', 'unit': 'Punkte',
            'method': 'Synthetische Werte ausschließlich für Tests.'}]}))
        block = lambda text: {'text': text, 'source_ids': ['sample']}
        spec = {
            'schema_version': '0.4', 'id': 'general-example', 'language': 'de',
            'as_of': '2026-09-20', 'coverage_end': '2025-12-31',
            'sources_file': 'sources.json', 'source_ids': ['sample'],
            'logo_file': str(ROOT / 'brand/df-circle-white.png'),
            'caption': [block('Ein neutraler Beispieltext.')],
            'slides': [{
                'kicker': 'BEISPIEL', 'title': 'Vergleich von Kategorien',
                'subtitle': block('Synthetische Testdaten, in Punkten.'),
                'note': block('Nur ein technischer Test.'),
                'alt_text': block('Balken: Alpha 2,5 und Beta −1,2 Punkte.'),
                'chart': {'type': 'bar', 'orientation': 'horizontal',
                    'y_limits': [-2, 4], 'suffix': '', 'series': [{
                        'id': 'first', 'label': 'Beispiel', 'data_file': 'values.csv',
                        'color_role': 'series_1', 'source_ids': ['sample']}]} }]
        }
        path = root / 'post.json'
        path.write_text(json.dumps(spec, ensure_ascii=False))
        return path, spec

    def test_export_links_citations_and_tracks_every_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, spec = self.fixture(root)
            render_post(path, root / 'out', ROOT / 'brand/palette-a.json')
            out = root / 'out'
            caption = (out / 'caption.md').read_text()
            self.assertIn('Ein neutraler Beispieltext. [1]', caption)
            self.assertIn('Quellen', caption)
            self.assertIn('https://example.org/data', caption)
            self.assertNotIn('](https://', caption)
            self.assertNotIn('Sources:', caption)
            manifest = json.loads((out / 'manifest.json').read_text())
            self.assertEqual(manifest['slides'][0]['scales']['value_axis'], 'x')
            self.assertEqual(manifest['data_files'][0]['sha256'], hashlib.sha256((root / 'values.csv').read_bytes()).hexdigest())
            self.assertEqual(manifest['review_status'], 'preview')
            self.assertEqual(manifest['citations']['sample'], 1)
            with Image.open(out / '01.png') as image:
                self.assertEqual(image.size, (1080, 1350))
            svg = (out / '01.svg').read_text()
            self.assertIn('1/1', svg)
            self.assertIn('Stand: 20.09.2026', svg)
            self.assertNotIn('A little more perspective', svg)

    def test_unknown_or_missing_citation_cannot_replace_good_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, original = self.fixture(root)
            out = root / 'out'
            render_post(path, out, ROOT / 'brand/palette-a.json')
            before = {p.name: p.read_bytes() for p in out.iterdir()}
            for invalid in ('unknown', 'missing'):
                spec = copy.deepcopy(original)
                if invalid == 'unknown':
                    spec['caption'][0]['source_ids'] = ['nonexistent']
                else:
                    spec['slides'][0]['chart']['series'][0]['source_ids'] = []
                path.write_text(json.dumps(spec))
                with self.assertRaises(ValueError):
                    render_post(path, out, ROOT / 'brand/palette-a.json')
                self.assertEqual({p.name: p.read_bytes() for p in out.iterdir()}, before)

    def test_page_count_follows_spec_and_old_extra_slides_are_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, spec = self.fixture(root)
            spec['slides'] *= 2
            path.write_text(json.dumps(spec))
            out = root / 'out'
            render_post(path, out, ROOT / 'brand/palette-a.json')
            self.assertIn('2/2', (out / '02.svg').read_text())
            spec['slides'] = spec['slides'][:1]
            path.write_text(json.dumps(spec))
            render_post(path, out, ROOT / 'brand/palette-a.json')
            self.assertFalse((out / '02.png').exists())
            self.assertIn('1/1', (out / '01.svg').read_text())

    def test_stand_and_source_retrieval_dates_remain_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, spec = self.fixture(root)
            cards = json.loads((root / 'sources.json').read_text())
            cards['sources'][0]['retrieved_at'] = '2026-09-19T10:00:00+00:00'
            (root / 'sources.json').write_text(json.dumps(cards))
            render_post(path, root / 'out', ROOT / 'brand/palette-a.json')
            self.assertIn('Stand: 20.09.2026', (root / 'out/01.svg').read_text())
            self.assertIn('Abruf: 19.09.2026', (root / 'out/caption.md').read_text())
