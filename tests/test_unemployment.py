"""Check fresh Eurostat decoding and raw-only unemployment preparation."""
import copy
import hashlib
import importlib.util
import itertools
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1] / 'projects/unemployment-de-ch-dk-no'
MODULE_SPEC = importlib.util.spec_from_file_location('unemployment_prepare', PROJECT / 'prepare.py')
MODULE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(MODULE)


class UnemploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        shutil.copytree(PROJECT / 'sources', self.project / 'sources')
        self.register_path = self.project / 'sources/source-register.json'
        self.register = json.loads(self.register_path.read_text())
        self.source = next(s for s in self.register['sources'] if s['id'] == 'eurostat-une-rt-a')
        self.raw = self.project / 'sources' / self.source['raw_file']
        self.dataset = json.loads(self.raw.read_bytes())

    def replace_data(self, dataset):
        payload = json.dumps(dataset).encode()
        self.raw.write_bytes(payload)
        self.source['raw_sha256'] = hashlib.sha256(payload).hexdigest()
        self.register_path.write_text(json.dumps(self.register))

    def outputs(self):
        return {p.name: p.read_bytes() for p in (self.project / 'data/processed').iterdir()}

    def test_observed_country_year_values_and_breaks_are_preserved(self):
        rows = MODULE.decode(self.dataset, self.register['selection'])
        self.assertEqual(len(rows), 40)
        self.assertEqual(len({(r['geo'], r['year']) for r in rows}), 40)
        latest = {r['geo']: r['rate'] for r in rows if r['year'] == 2025}
        self.assertEqual(latest, {'DE': 3.8, 'CH': 4.9, 'DK': 6.4, 'NO': 4.5})
        earliest = {r['geo']: r['rate'] for r in rows if r['year'] == 2016}
        self.assertEqual(earliest, {'DE': 3.9, 'CH': 5.0, 'DK': 6.0, 'NO': 4.9})
        self.assertEqual({(r['geo'], r['year'], r['flag']) for r in rows if r['flag']},
                         {('DE', 2020, 'b'), ('DK', 2016, 'b'),
                          ('DK', 2017, 'b'), ('DK', 2023, 'b')})

    def test_dimension_and_category_permutations_do_not_change_observations(self):
        original = self.dataset
        changed = copy.deepcopy(original)
        changed['id'] = list(reversed(original['id']))
        for dimension in changed['id']:
            old = original['dimension'][dimension]['category']['index']
            changed['dimension'][dimension]['category']['index'] = {
                code: len(old) - position - 1 for code, position in old.items()}
        changed['size'] = list(reversed(original['size']))
        changed['value'], changed['status'] = {}, {}

        def flat(dataset, coordinates):
            return sum(dataset['dimension'][dimension]['category']['index'][coordinates[dimension]]
                       * math.prod(dataset['size'][i + 1:])
                       for i, dimension in enumerate(dataset['id']))

        categories = [original['dimension'][d]['category']['index'] for d in original['id']]
        for codes in itertools.product(*categories):
            coordinates = dict(zip(original['id'], codes))
            before, after = str(flat(original, coordinates)), str(flat(changed, coordinates))
            changed['value'][after] = original['value'][before]
            if before in original['status']:
                changed['status'][after] = original['status'][before]
        self.assertEqual(MODULE.decode(changed, self.register['selection']),
                         MODULE.decode(original, self.register['selection']))

    def test_missing_selected_observation_cannot_become_zero(self):
        del self.dataset['value']['12']  # Germany, 2016 in the retained source.
        self.replace_data(self.dataset)
        with self.assertRaisesRegex(ValueError, 'Missing or invalid rate for DE 2016'):
            MODULE.prepare(self.project)
        self.assertFalse((self.project / 'data/processed').exists())

    def test_nonfinite_and_out_of_range_observations_are_rejected(self):
        for value in (float('nan'), float('inf'), -0.1, 100.1, True):
            with self.subTest(value=value):
                dataset = copy.deepcopy(self.dataset)
                dataset['value']['12'] = value
                with self.assertRaisesRegex(ValueError, 'Missing or invalid rate'):
                    MODULE.decode(dataset, self.register['selection'])

    def test_changed_metric_missing_country_and_duplicate_indexes_are_rejected(self):
        datasets = []
        dataset = copy.deepcopy(self.dataset)
        dataset['dimension']['unit']['category']['index'] = {'PC_POP': 0}
        datasets.append(dataset)
        dataset = copy.deepcopy(self.dataset)
        dataset['dimension']['geo']['category']['index']['CH'] = 2
        datasets.append(dataset)
        dataset = copy.deepcopy(self.dataset)
        dataset['dimension']['geo']['category']['index']['SE'] = (
            dataset['dimension']['geo']['category']['index'].pop('CH'))
        datasets.append(dataset)
        dataset = copy.deepcopy(self.dataset)
        dataset['extension']['id'] = 'OTHER'
        datasets.append(dataset)
        for dataset in datasets:
            with self.subTest(dataset=dataset['extension']['id']), self.assertRaises(ValueError):
                MODULE.decode(dataset, self.register['selection'])

    def test_corrupt_raw_bytes_and_scope_changes_are_rejected(self):
        self.raw.write_bytes(self.raw.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            MODULE.prepare(self.project)
        selection = copy.deepcopy(self.register['selection'])
        selection['countries'][-1] = 'DE'
        with self.assertRaisesRegex(ValueError, 'Selection must match'):
            MODULE.decode(self.dataset, selection)

    def test_raw_only_rebuild_is_deterministic_and_preserves_inputs(self):
        before = {p.relative_to(self.project): p.read_bytes()
                  for p in (self.project / 'sources').rglob('*') if p.is_file()}
        self.assertFalse((self.project / 'data').exists())
        report = MODULE.prepare(self.project)
        first = self.outputs()
        self.assertEqual(set(first), {'unemployment.csv', 'de.csv', 'ch.csv',
                                      'dk.csv', 'no.csv', 'validation.json'})
        self.assertEqual(report['observations'], 40)
        self.assertIn(b'2020-01-01,3.6,b\n', first['de.csv'])
        shutil.rmtree(self.project / 'data')
        MODULE.prepare(self.project)
        self.assertEqual(first, self.outputs())
        self.assertEqual(before, {p.relative_to(self.project): p.read_bytes()
                                 for p in (self.project / 'sources').rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
