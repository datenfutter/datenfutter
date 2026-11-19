"""Protect comparisons from silently reusing data or changing scales."""
import copy
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
import matplotlib.pyplot as plt

from datenfutter.render import Page, _line, render_post

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/legacy'


class CarouselTests(unittest.TestCase):
    def test_slide_uses_its_own_csv_and_records_every_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'a.csv').write_text('date,value\n2016-01-01,3.9\n2025-01-01,3.8\n')
            (base / 'b.csv').write_text('date,value\n2016-01-01,5.0\n2025-01-01,4.9\n')
            spec = json.loads((FIXTURES / 'posts/ecb-2022-2025.json').read_text())
            spec.update(data_file='a.csv', series_kind='observations',
                        sources_file=str(FIXTURES / 'research/sources.json'))
            slide = spec['slides'][0]
            slide['chart'] = {'type': 'line', 'start': '2016-01-01', 'end': '2025-12-31',
                              'y_limits': [0, 6], 'x_label_format': 'year'}
            spec['slides'] = [slide, copy.deepcopy(slide)]
            spec['slides'][1]['data_file'] = 'b.csv'
            path = base / 'spec.json'
            path.write_text(json.dumps(spec))
            render_post(path, base / 'out', ROOT / 'brand/brand.json')
            result = json.loads((base / 'out/manifest.json').read_text())
            self.assertEqual([s['values'] for s in result['slides']], [[3.9, 3.8], [5.0, 4.9]])
            self.assertEqual({d['file'] for d in result['data_files']}, {'a.csv', 'b.csv'})

    def test_shared_scale_and_annual_ticks_are_honoured(self):
        page = Page(json.loads((ROOT / 'brand/brand.json').read_text()))
        try:
            _line(page, {'type': 'line', 'start': '2016-01-01', 'end': '2025-01-01',
                         'y_limits': [0, 6], 'x_label_format': 'year'},
                  [(date(2016, 1, 1), 3.9), (date(2025, 1, 1), 3.8)],
                  {'coverage_end': '2025-12-31'})
            ax = page.fig.axes[0]
            self.assertEqual(ax.get_ylim(), (0, 6))
            self.assertEqual(ax.get_xticklabels()[0].get_text(), '2016')
            self.assertEqual(ax.get_xticklabels()[-1].get_text(), '2025')
        finally:
            plt.close(page.fig)

    def test_explicit_scale_cannot_hide_observations(self):
        page = Page(json.loads((ROOT / 'brand/brand.json').read_text()))
        try:
            with self.assertRaises(ValueError):
                _line(page, {'type': 'line', 'start': '2016-01-01', 'end': '2025-01-01',
                             'y_limits': [0, 4]},
                      [(date(2016, 1, 1), 5.0), (date(2025, 1, 1), 4.9)],
                      {'coverage_end': '2025-12-31'})
        finally:
            plt.close(page.fig)

    def test_break_keeps_observation_but_does_not_connect_across_it(self):
        page = Page(json.loads((ROOT / 'brand/brand.json').read_text()))
        try:
            summary = _line(page, {'type': 'line', 'start': '2019-01-01', 'end': '2021-01-01',
                                  'break_dates': ['2020-01-01']},
                            [(date(2019, 1, 1), 2.9), (date(2020, 1, 1), 3.6),
                             (date(2021, 1, 1), 3.6)], {'coverage_end': '2025-12-31'})
            self.assertEqual(summary['values'], [2.9, 3.6, 3.6])
            lines = [list(line.get_ydata()) for line in page.fig.axes[0].lines
                     if line.get_label() == 'observations']
            self.assertEqual(lines, [[2.9], [3.6, 3.6]])
        finally:
            plt.close(page.fig)
