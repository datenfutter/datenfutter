"""Strict input handling; no implicit interpolation or financial adjustments."""
import csv
import math
from datetime import date
from pathlib import Path

Series = list[tuple[date, float | None]]


def read_categories(path: str | Path) -> list[tuple[str, float]]:
    """Read explicit category,value inputs, retaining order and rejecting ambiguity."""
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {'category', 'value'} <= set(reader.fieldnames):
            raise ValueError('Category CSV requires category,value headers.')
        rows, seen = [], set()
        for row in reader:
            label = (row['category'] or '').strip()
            try:
                value = float(row['value'])
            except (ValueError, TypeError) as exc:
                raise ValueError('Category bars require explicit numeric values; missing is not zero.') from exc
            if not label or label in seen or not math.isfinite(value):
                raise ValueError('Category names must be unique and values finite.')
            seen.add(label)
            rows.append((label, value))
    if not 1 <= len(rows) <= 8:
        raise ValueError('Use one to eight categories per slide.')
    return rows


def read_series(path: str | Path) -> Series:
    """Read date,value CSV; sort dates, preserve blanks, reject ambiguous input."""
    rows = []
    seen = set()
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {'date', 'value'} <= set(reader.fieldnames):
            raise ValueError('CSV requires date,value headers.')
        for number, row in enumerate(reader, 2):
            try:
                day = date.fromisoformat(row['date'].strip())
                raw = row['value'].strip()
                value = float(raw) if raw else None
            except (ValueError, AttributeError, TypeError) as exc:
                raise ValueError(f'Invalid date or number at CSV row {number}.') from exc
            if day in seen:
                raise ValueError(f'Duplicate date: {day}.')
            if value is not None and not math.isfinite(value):
                raise ValueError(f'Non-finite value at {day}; use a blank for missing data.')
            seen.add(day)
            rows.append((day, value))
    if not rows or not any(v is not None for _, v in rows):
        raise ValueError('CSV contains no numeric observations.')
    return sorted(rows)


def _schedule(rows: Series) -> None:
    if not rows or any(v is None or not math.isfinite(v) for _, v in rows):
        raise ValueError('An effective-date schedule cannot contain missing values.')
    if any(a[0] >= b[0] for a, b in zip(rows, rows[1:])):
        raise ValueError('Schedule dates must be strictly increasing.')


def _at(rows: Series, day: date) -> float:
    preceding = [v for d, v in rows if d <= day]
    if not preceding:
        raise ValueError(f'No established value on or before {day}.')
    return preceding[-1]


def step_window(rows: Series, start: date, end: date) -> Series:
    """Clip an effective-date schedule; preserve its carried boundary values.

    Caller must verify the source's coverage through end; the last effective
    date alone is not evidence that there were no later changes.
    """
    _schedule(rows)
    if start >= end:
        raise ValueError('Start must be before end.')
    clipped = [(start, _at(rows, start))]
    clipped.extend((d, v) for d, v in rows if start < d <= end)
    if clipped[-1][0] < end:
        clipped.append((end, _at(rows, end)))
    return clipped


def annual_changes(rows: Series, years: list[int]) -> list[tuple[str, float]]:
    """Year-end minus prior year-end; rates in percent yield percentage points."""
    _schedule(rows)
    if not years or len(set(years)) != len(years):
        raise ValueError('Provide distinct calendar years.')
    return [(str(y), _at(rows, date(y, 12, 31)) - _at(rows, date(y - 1, 12, 31))) for y in years]


def rebase(rows: Series) -> Series:
    """Index a positive first observation to 100 without filling gaps."""
    if not rows or rows[0][1] is None or rows[0][1] <= 0:
        raise ValueError('Rebasing requires a positive first observation.')
    base = rows[0][1]
    return [(d, None if v is None else v / base * 100) for d, v in rows]
