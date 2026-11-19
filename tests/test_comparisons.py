"""Guard against dropped traces, misleading scales and lost input provenance."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from datetime import date
import matplotlib.pyplot as plt

from datenfutter.render import render_post, _fmt, Page, _comparison_line

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/legacy'


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        for name, values in [('a', '1\n2024-02-01,\n2024-03-01,2'),
                             ('b', '4\n2024-02-01,6\n2024-03-01,5'),
                             ('c', '-1\n2024-02-01,0\n2024-03-01,1')]:
            (self.base / f'{name}.csv').write_text('date,value\n2024-01-01,' + values + '\n')
        self.spec = json.loads((FIXTURES / 'posts/ecb-2022-2025.json').read_text())
        self.spec.update(data_file='a.csv', series_kind='observations', locale='de',
                         sources_file=str(FIXTURES / 'research/sources.json'))
        self.spec['slides'] = self.spec['slides'][:1]
        self.spec['slides'][0]['chart'] = {
            'type': 'line', 'start': '2024-01-01', 'end': '2024-03-01',
            'y_limits': [-2, 7], 'suffix': ' %',
            'series': [{'id': name, 'label': label, 'data_file': f'{name}.csv'}
                       for name, label in [('a', 'Alpha'), ('b', 'Beta'), ('c', 'Gamma')]]}

    def render(self):
        path = self.base / 'spec.json'
        path.write_text(json.dumps(self.spec))
        render_post(path, self.base / 'out', ROOT / 'brand/brand.json')
        return json.loads((self.base / 'out/manifest.json').read_text())

    def test_all_traces_and_gaps_survive_with_separate_hashes(self):
        result = self.render()
        self.assertIn('series', result['slides'][0], 'Multiple traces must not silently collapse to the default CSV')
        traces = result['slides'][0]['series']
        self.assertEqual([s['values'] for s in traces], [[1, None, 2], [4, 6, 5], [-1, 0, 1]])
        self.assertEqual({d['file'] for d in result['data_files']}, {'a.csv', 'b.csv', 'c.csv'})
        self.assertEqual(len({d['sha256'] for d in result['data_files']}), 3)
        svg = (self.base / 'out/01.svg').read_text()
        for label in ('Alpha', 'Beta', 'Gamma'):
            self.assertIn(label, svg)

    def test_scale_cannot_hide_a_secondary_trace(self):
        self.spec['slides'][0]['chart']['y_limits'] = [-2, 3]
        with self.assertRaises(ValueError):
            self.render()
        self.assertFalse((self.base / 'out/01.png').exists())

    def test_indexed_comparison_requires_common_actual_baseline(self):
        (self.base / 'b.csv').write_text('date,value\n2024-02-01,6\n2024-03-01,5\n')
        self.spec['slides'][0]['chart'].update(transform='index_100', y_limits=[-2, 300])
        with self.assertRaises(ValueError):
            self.render()

    def test_category_bars_use_source_categories_and_signed_values(self):
        (self.base / 'categories.csv').write_text('category,value\nAlpha,2.5\nBeta,-1.2\nGamma,0\n')
        self.spec['data_file'] = 'categories.csv'
        self.spec['slides'][0]['chart'] = {'type': 'category_bar', 'suffix': ' %'}
        try:
            result = self.render()
        except ValueError as exc:
            self.fail(f'Category CSV must be rendered as bars: {exc}')
        summary = result['slides'][0]
        self.assertEqual(summary['labels'], ['Alpha', 'Beta', 'Gamma'])
        self.assertEqual(summary['values'], [2.5, -1.2, 0])
        self.assertLessEqual(summary['x_limits'][0], -1.2)
        self.assertGreaterEqual(summary['x_limits'][1], 2.5)
        self.assertEqual(summary['baseline'], 0)

    def test_german_format_preserves_sign_and_precision(self):
        self.assertEqual(_fmt(-1.25, {'locale': 'de', 'decimals': 2, 'suffix': ' %'}), '−1,25 %')
        self.assertEqual(_fmt(3.2, {'locale': 'de', 'suffix': ' %'}, True), '+3,2 %')

    def test_fractional_scale_ticks_do_not_round_to_duplicate_integers(self):
        page = Page(json.loads((ROOT / 'brand/brand.json').read_text()))
        try:
            chart = {**self.spec['slides'][0]['chart'], 'y_limits': [0, 1], 'locale': 'de'}
            rows = [(date(2024, 1, 1), .2), (date(2024, 3, 1), .8)]
            _comparison_line(page, chart, [(item, rows) for item in chart['series'][:2]], self.spec)
            labels = [t.get_text() for t in page.fig.axes[0].get_yticklabels()]
            self.assertIn('0,2', labels)
            self.assertEqual(len(labels), len(set(labels)))
        finally:
            plt.close(page.fig)

    def test_isolated_observations_on_both_sides_of_gap_remain_visible(self):
        page = Page(json.loads((ROOT / 'brand/brand.json').read_text()))
        try:
            chart = self.spec['slides'][0]['chart']
            rows = [(date(2024, 1, 1), 1), (date(2024, 2, 1), None), (date(2024, 3, 1), 2)]
            _comparison_line(page, chart, [(item, rows) for item in chart['series'][:2]], self.spec)
            drawn = [line for line in page.fig.axes[0].lines if line.get_label() == 'Alpha']
            self.assertEqual([list(line.get_ydata()) for line in drawn], [[1], [2]])
            self.assertTrue(all(line.get_marker() == 'o' for line in drawn))
        finally:
            plt.close(page.fig)
