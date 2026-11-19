import tempfile
import unittest
from datetime import date
from pathlib import Path

from datenfutter.data import read_series, step_window, annual_changes, rebase


class DataTests(unittest.TestCase):
    def csv(self, content):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / 'data.csv'
        path.write_text(content, encoding='utf-8')
        return path

    def test_sorts_dates_and_keeps_missing_observations(self):
        rows = read_series(self.csv('date,value\n2022-02-01,\n2022-01-01,100\n2022-03-01,120\n'))
        self.assertEqual(rows, [(date(2022, 1, 1), 100.0), (date(2022, 2, 1), None), (date(2022, 3, 1), 120.0)])

    def test_rejects_duplicates_and_nonfinite_values(self):
        for content in ('date,value\n2022-01-01,1\n2022-01-01,2\n',
                        'date,value\n2022-01-01,inf\n',
                        'date,value\n2022-01-01,NaN\n',
                        'date,value\n2022-13-01,1\n',
                        'date,value\n', 'date,value\n2022-01-01,\n'):
            with self.subTest(content=content), self.assertRaises(ValueError):
                read_series(self.csv(content))

    def test_step_window_carries_only_an_established_rate(self):
        rows = [(date(2019, 9, 18), -0.5), (date(2022, 7, 27), 0.0)]
        self.assertEqual(step_window(rows, date(2022, 1, 1), date(2022, 12, 31)),
                         [(date(2022, 1, 1), -0.5), (date(2022, 7, 27), 0.0), (date(2022, 12, 31), 0.0)])
        with self.assertRaises(ValueError):
            step_window(rows, date(2018, 1, 1), date(2022, 12, 31))
        with self.assertRaises(ValueError):
            step_window([(date(2022, 1, 1), None)], date(2022, 1, 1), date(2022, 12, 31))

    def test_annual_rate_changes_are_percentage_point_differences(self):
        rows = [(date(2019, 9, 18), -0.5), (date(2022, 12, 21), 2.0),
                (date(2023, 9, 20), 4.0), (date(2024, 12, 18), 3.0), (date(2025, 6, 11), 2.0)]
        self.assertEqual(annual_changes(rows, [2022, 2023, 2024, 2025]),
                         [('2022', 2.5), ('2023', 2.0), ('2024', -1.0), ('2025', -1.0)])

    def test_rebase_keeps_gaps_and_rejects_undefined_baseline(self):
        rows = [(date(2022, 1, 1), 50.0), (date(2022, 2, 1), None), (date(2022, 3, 1), 60.0)]
        self.assertEqual([v for _, v in rebase(rows)], [100.0, None, 120.0])
        for v in (None, 0.0, -1.0):
            with self.subTest(v=v), self.assertRaises(ValueError):
                rebase([(date(2022, 1, 1), v), (date(2022, 2, 1), 50.0)])


if __name__ == '__main__':
    unittest.main()
