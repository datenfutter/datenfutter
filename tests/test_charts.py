"""Protect the generic chart API's values, gaps, alignment and scales."""
import copy
import json
import math
import unittest
from datetime import date

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from datenfutter.charts import render_chart


THEME = {'cream': '#FAF8EF', 'navy': '#1C2D57', 'muted': '#626C80',
         'grid': '#DDDCD3', 'dpi': 120, 'language': 'de'}
WINDOW = {'type': 'line', 'start': '2020-01-01', 'end': '2023-01-01',
          'x_label_format': 'year', 'decimals': 1, 'suffix': '%'}


def dated(values):
    return [(date(2020 + i, 1, 1), value) for i, value in enumerate(values)]


def series(identifier, values, color='#1C2D57', **options):
    return {'id': identifier, 'label': identifier, 'rows': dated(values),
            'color': color, 'source_ids': ['test-source'], **options}


class ChartTests(unittest.TestCase):
    def test_explicit_year_axis_labels_every_year_in_the_window(self):
        chart={**WINDOW,'start':'2019-01-01','end':'2026-08-01'}
        values=[{'id':'sample','label':'Sample','color':'#1C2D57',
                 'rows':[(date(2019,1,1),1),(date(2026,8,1),2)]}]
        render_chart(self.ax,chart,values,THEME)
        self.fig.canvas.draw()
        self.assertEqual([t.get_text() for t in self.ax.get_xticklabels()],
                         ['2019','2020','2021','2022','2023','2024','2025','2026'])

    def setUp(self):
        self.fig = plt.figure(figsize=(9, 6), dpi=120)
        self.ax = self.fig.add_axes([.12, .18, .60, .65])
        self.addCleanup(plt.close, self.fig)

    def test_three_series_keep_their_own_values_on_one_scale(self):
        inputs = [series('Alpha', [1, 2, 3, 4]),
                  series('Beta', [4, 3, 2, 1], '#626C80', linestyle='--'),
                  series('Gamma', [2, 2.5, 2, 2.5], '#000000', linestyle=':')]
        before = copy.deepcopy(inputs)
        result = render_chart(self.ax, {**WINDOW, 'y_limits': [0, 5]}, inputs, THEME)
        self.assertEqual([s['values'] for s in result['series']],
                         [[1, 2, 3, 4], [4, 3, 2, 1], [2, 2.5, 2, 2.5]])
        self.assertEqual(self.ax.get_ylim(), (0, 5))
        self.assertEqual(result['scales']['value_axis'], 'y')
        self.assertEqual(result['scales']['value_limits'], [0, 5])
        self.assertEqual([line.get_linestyle() for line in self.ax.lines
                          if line.get_label() in ('Alpha', 'Beta', 'Gamma')], ['-', '--', ':'])
        self.assertEqual([s['source_ids'] for s in result['series']],
                         [['test-source'], ['test-source'], ['test-source']])
        self.assertTrue(any('Gamma' in t.get_text() and '2,5 %' in t.get_text()
                            for t in self.ax.texts))
        self.assertEqual(inputs, before)
        json.dumps(result, allow_nan=False)

    def test_missing_observations_and_breaks_never_connect(self):
        inputs = [series('Alpha', [1, None, 3, 4], break_dates=['2023-01-01'])]
        result = render_chart(self.ax, WINDOW, inputs, THEME)
        lines = [line for line in self.ax.lines if line.get_label() == 'Alpha']
        self.assertEqual(len(lines), 2)
        self.assertTrue(math.isnan(lines[0].get_ydata()[1]))
        self.assertEqual(list(lines[1].get_ydata()), [4])
        self.assertNotIn(lines[1].get_marker(), (None, '', 'None'))
        self.assertEqual(result['series'][0]['values'], [1, None, 3, 4])
        self.assertEqual(result['series'][0]['break_dates'], ['2023-01-01'])
        self.assertEqual(result['series'][0]['segments'], [
            {'dates': ['2020-01-01', '2021-01-01', '2022-01-01'], 'values': [1, None, 3]},
            {'dates': ['2023-01-01'], 'values': [4]}])

    def test_break_belongs_to_its_series_and_requires_a_numeric_point(self):
        render_chart(self.ax, WINDOW,
                     [series('Alpha', [1, 2, 3, 4], break_dates=['2022-01-01']),
                      series('Beta', [4, 3, 2, 1], '#626C80')], THEME)
        self.assertEqual(len([line for line in self.ax.lines if line.get_label() == 'Alpha']), 2)
        self.assertEqual(len([line for line in self.ax.lines if line.get_label() == 'Beta']), 1)
        for bad_break in ('2019-01-01', '2021-01-01'):
            with self.subTest(break_date=bad_break), self.assertRaises(ValueError):
                render_chart(self.ax, WINDOW,
                             [series('Alpha', [1, None, 3, 4], break_dates=[bad_break])], THEME)

    def test_date_window_clips_each_series_without_inventing_points(self):
        inputs = [series('Alpha', [1, None, 3, 4])]
        result = render_chart(self.ax, {**WINDOW, 'start': '2021-01-01', 'end': '2022-12-31'},
                              inputs, THEME)
        self.assertEqual(result['series'][0]['dates'], ['2021-01-01', '2022-01-01'])
        self.assertEqual(result['series'][0]['values'], [None, 3])
        self.assertEqual(result['scales']['date_window'], ['2021-01-01', '2022-12-31'])

    def test_steps_preserve_supplied_gaps_and_do_not_extrapolate(self):
        result = render_chart(self.ax, {**WINDOW, 'type': 'step', 'end': '2024-01-01'},
                              [series('Alpha', [1, None, 3, 4])], THEME)
        line = next(line for line in self.ax.lines if line.get_label() == 'Alpha')
        self.assertEqual(line.get_drawstyle(), 'steps-post')
        self.assertTrue(math.isnan(line.get_ydata()[1]))
        self.assertEqual(result['series'][0]['dates'][-1], '2023-01-01')
        self.assertEqual(result['series'][0]['values'], [1, None, 3, 4])

    def test_endpoint_labels_remain_separate_when_three_values_match(self):
        render_chart(self.ax, {**WINDOW, 'y_limits': [0, 5]},
                     [series('Alpha', [1, 2, 3, 3]), series('Beta', [2, 2, 3, 3], '#626C80'),
                      series('Gamma', [4, 3, 3, 3], '#000000')], THEME)
        self.fig.canvas.draw()
        labels = [text for text in self.ax.texts
                  if any(name in text.get_text() for name in ('Alpha', 'Beta', 'Gamma'))]
        self.assertEqual(len(labels), 3)
        boxes = [text.get_window_extent() for text in labels]
        for i, box in enumerate(boxes):
            for other in boxes[i + 1:]:
                self.assertFalse(box.overlaps(other))

    def test_category_bars_align_by_name_and_missing_values_do_not_become_zero(self):
        inputs = [dict(series('Alpha', []), rows=[('Oslo', 2), ('Bern', None)]),
                  dict(series('Beta', [], '#626C80'), rows=[('Bern', 5), ('Oslo', 3), ('Warsaw', None)])]
        result = render_chart(self.ax, {'type': 'bar'}, inputs, THEME)
        self.assertEqual(result['categories'], ['Oslo', 'Bern', 'Warsaw'])
        self.assertEqual([s['values'] for s in result['series']], [[2, None, None], [3, 5, None]])
        self.assertEqual([s['categories'] for s in result['series']],
                         [['Oslo', 'Bern', 'Warsaw'], ['Oslo', 'Bern', 'Warsaw']])
        self.assertEqual(len(self.ax.patches), 3)
        self.assertEqual([patch.get_width() for patch in self.ax.patches], [2, 3, 5])
        centers = [patch.get_y() + patch.get_height() / 2 for patch in self.ax.patches]
        self.assertLess(abs(centers[0]), .5)
        self.assertLess(abs(centers[1]), .5)
        self.assertLess(abs(centers[2] - 1), .5)
        self.assertNotEqual(centers[0], centers[1])
        self.assertEqual([label.get_text() for label in self.ax.get_yticklabels()],
                         ['Oslo', 'Bern', 'Warsaw'])
        self.assertLessEqual(self.ax.get_xlim()[0], 0)
        self.assertEqual(result['scales']['value_axis'], 'x')
        self.assertEqual([text.get_text() for text in self.ax.get_legend().get_texts()], ['Alpha', 'Beta'])

    def test_vertical_bars_preserve_signed_values_with_a_zero_baseline(self):
        result = render_chart(self.ax, {'type': 'bar', 'orientation': 'vertical'},
                              [dict(series('Alpha', []), rows=[('A', -2), ('B', 6), ('C', 0)])], THEME)
        self.assertEqual([patch.get_height() for patch in self.ax.patches], [-2, 6, 0])
        self.assertLessEqual(self.ax.get_ylim()[0], -2)
        self.assertGreaterEqual(self.ax.get_ylim()[1], 6)
        self.assertEqual(result['scales']['value_axis'], 'y')
        self.assertTrue(result['scales']['includes_zero'])

    def test_limits_cannot_hide_any_series_or_remove_bar_zero(self):
        for chart, inputs in [
            ({**WINDOW, 'y_limits': [0, 4]}, [series('Alpha', [1, 2, 3, 4]), series('Beta', [5, 5, 5, 5])]),
            ({'type': 'bar', 'y_limits': [1, 5]}, [dict(series('Alpha', []), rows=[('A', 2)])]),
            ({'type': 'bar', 'orientation': 'vertical', 'y_limits': [-1, 5]},
             [dict(series('Alpha', []), rows=[('A', -2)])]),
            ({**WINDOW, 'y_limits': [0, math.inf]}, [series('Alpha', [1, 2, 3, 4])]),
        ]:
            with self.subTest(chart=chart), self.assertRaises(ValueError):
                render_chart(self.ax, chart, inputs, THEME)
        self.assertEqual(len(self.ax.lines), 0)
        self.assertEqual(len(self.ax.patches), 0)

    def test_value_ticks_use_numeric_axis_and_reject_invalid_ticks_before_drawing(self):
        ticks = [0, .5, 2, 5]
        for chart, inputs, axis_name in [
            (WINDOW, [series('Alpha', [1, 2, 3, 4])], 'yaxis'),
            ({'type': 'bar'}, [dict(series('Alpha', []), rows=[('A', 1), ('B', 4)])], 'xaxis'),
            ({'type': 'bar', 'orientation': 'vertical'},
             [dict(series('Alpha', []), rows=[('A', 1), ('B', 4)])], 'yaxis'),
        ]:
            with self.subTest(chart=chart):
                self.ax.clear()
                result = render_chart(self.ax, {**chart, 'y_limits': [0, 5], 'value_ticks': ticks},
                                      inputs, THEME)
                self.assertEqual(list(getattr(self.ax, axis_name).get_majorticklocs()), [0, .5, 2, 5])
                self.assertEqual(result['scales']['value_ticks'], [0, .5, 2, 5])
        for invalid in ([], [0, 2, 2], [3, 1], [None, 2], [0, 6], [0, math.nan], [False, 2], '0,2,5'):
            with self.subTest(ticks=invalid):
                self.ax.clear()
                with self.assertRaises(ValueError):
                    render_chart(self.ax, {**WINDOW, 'y_limits': [0, 5], 'value_ticks': invalid},
                                 [series('Alpha', [1, 2, 3, 4])], THEME)
                self.assertEqual(len(self.ax.lines), 0)
                self.assertEqual(len(self.ax.patches), 0)

    def test_duplicate_or_nonfinite_input_fails_before_drawing(self):
        for chart, inputs in [
            (WINDOW, [dict(series('Alpha', []), rows=[(date(2020, 1, 1), 1), (date(2020, 1, 1), 2)])]),
            ({'type': 'bar'}, [dict(series('Alpha', []), rows=[('A', 1), ('A', 2)])]),
            (WINDOW, [series('Alpha', [1, math.nan, 3, 4])]),
            (WINDOW, [series('Alpha', [1, 2, 3, 4]), series('Alpha', [4, 3, 2, 1])]),
            (WINDOW, [series('Alpha', [None, None, None, None])]),
        ]:
            with self.subTest(inputs=inputs), self.assertRaises(ValueError):
                render_chart(self.ax, chart, inputs, THEME)
        self.assertEqual(len(self.ax.lines), 0)
        self.assertEqual(len(self.ax.patches), 0)


if __name__ == '__main__':
    unittest.main()
