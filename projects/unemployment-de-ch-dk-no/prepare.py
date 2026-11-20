"""Prepare the selected Eurostat unemployment snapshot without network access."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path


COUNTRIES = ('DE', 'CH', 'DK', 'NO')
YEARS = tuple(range(2016, 2026))
DIMENSIONS = {'freq': 'A', 'age': 'Y15-74', 'unit': 'PC_ACT', 'sex': 'T'}


def _categories(dataset, dimension, size):
    index = dataset['dimension'][dimension]['category']['index']
    if isinstance(index, list):
        index = {code: position for position, code in enumerate(index)}
    if (not isinstance(index, dict) or len(index) != size
            or any(type(position) is not int for position in index.values())
            or set(index.values()) != set(range(size))):
        raise ValueError(f'Invalid category indexes for {dimension}.')
    return index


def decode(dataset, selection):
    """Decode JSON-stat by dimension/category metadata, retaining source flags."""
    if (selection.get('countries') != list(COUNTRIES)
            or selection.get('years') != list(YEARS)
            or selection.get('dimensions') != DIMENSIONS):
        raise ValueError('Selection must match the documented countries, years and metric.')
    if (dataset.get('class') != 'dataset' or dataset.get('version') != '2.0'
            or dataset.get('extension', {}).get('id') != 'UNE_RT_A'):
        raise ValueError('Expected Eurostat UNE_RT_A JSON-stat 2.0 data.')
    dimensions, sizes = dataset['id'], dataset['size']
    expected = set(DIMENSIONS) | {'geo', 'time'}
    if (len(dimensions) != len(expected) or set(dimensions) != expected
            or len(sizes) != len(dimensions)
            or any(type(size) is not int or size < 1 for size in sizes)):
        raise ValueError('Unexpected dataset dimensions or sizes.')
    indexes = {dimension: _categories(dataset, dimension, size)
               for dimension, size in zip(dimensions, sizes)}
    for dimension, code in DIMENSIONS.items():
        if set(indexes[dimension]) != {code}:
            raise ValueError(f'Unexpected selection for {dimension}.')
    if set(indexes['geo']) != set(COUNTRIES):
        raise ValueError('Dataset must contain exactly the selected countries.')
    if not {str(year) for year in YEARS} <= indexes['time'].keys():
        raise ValueError('Dataset does not cover every selected year.')

    count = math.prod(sizes)

    def cells(name):
        values = dataset.get(name, {})
        if isinstance(values, list):
            if len(values) != count:
                raise ValueError(f'Unexpected {name} array length.')
            return {str(i): value for i, value in enumerate(values)}
        if (not isinstance(values, dict)
                or any(not key.isdecimal() or str(int(key)) != key
                       or not 0 <= int(key) < count for key in values)):
            raise ValueError(f'Invalid {name} cell indexes.')
        return values

    values, flags = cells('value'), cells('status')
    rows = []
    for country in COUNTRIES:
        for year in YEARS:
            coordinates = {**DIMENSIONS, 'geo': country, 'time': str(year)}
            position = 0
            for dimension, size in zip(dimensions, sizes):
                position = position * size + indexes[dimension][coordinates[dimension]]
            value = values.get(str(position))
            if (type(value) not in (int, float) or not math.isfinite(value)
                    or not 0 <= value <= 100):
                raise ValueError(f'Missing or invalid rate for {country} {year}.')
            flag = flags.get(str(position), '')
            if flag is None:
                flag = ''
            if not isinstance(flag, str):
                raise ValueError(f'Invalid observation flag for {country} {year}.')
            rows.append({'geo': country, 'year': year, 'rate': value, 'flag': flag})
    return rows


def _csv(fields, rows):
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer, lineterminator='\n')
    writer.writerow(fields)
    writer.writerows(rows)
    return buffer.getvalue()


def prepare(project_dir):
    """Rebuild all current tables from the registered, hash-verified raw response."""
    project = Path(project_dir).resolve()
    sources = project / 'sources'
    register = json.loads((sources / 'source-register.json').read_text(encoding='utf-8'))
    matches = [source for source in register['sources'] if source['id'] == 'eurostat-une-rt-a']
    if len(matches) != 1:
        raise ValueError('Expected one selected Eurostat unemployment source.')
    source = matches[0]
    raw = (sources / source['raw_file']).resolve()
    if not raw.is_relative_to((sources / 'raw').resolve()):
        raise ValueError('Selected evidence must be inside sources/raw/.')
    payload = raw.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != source['raw_sha256']:
        raise ValueError('Selected raw evidence SHA-256 mismatch.')
    dataset = json.loads(payload)
    rows = decode(dataset, register['selection'])
    output = {
        'unemployment.csv': _csv(['geo', 'year', 'rate', 'flag'],
                                [(r['geo'], r['year'], r['rate'], r['flag']) for r in rows]),
    }
    for country in COUNTRIES:
        output[f'{country.lower()}.csv'] = _csv(
            ['date', 'value', 'flag'],
            [(f"{r['year']}-01-01", r['rate'], r['flag'])
             for r in rows if r['geo'] == country])
    report = {
        'source_id': source['id'], 'raw_sha256': digest,
        'source_updated': dataset.get('updated'),
        'countries': list(COUNTRIES), 'years': list(YEARS), 'observations': len(rows),
        'missing_observations': 0, 'unit': DIMENSIONS['unit'],
        'breaks': [{'geo': r['geo'], 'year': r['year'], 'flag': r['flag']}
                   for r in rows if 'b' in r['flag'].split()],
        'flags': [{'geo': r['geo'], 'year': r['year'], 'flag': r['flag']}
                  for r in rows if r['flag']],
    }
    output['validation.json'] = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    destination = project / 'data' / 'processed'
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in output.items():
        (destination / name).write_text(content, encoding='utf-8', newline='')
    return report


if __name__ == '__main__':
    report = prepare(Path(__file__).resolve().parent)
    print(f"Prepared {report['observations']} annual observations from verified raw evidence.")
