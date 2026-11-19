"""Compose factual charts and editorial typography on one fixed-size canvas."""
import hashlib
import json
import math
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
from matplotlib.ticker import MaxNLocator, FuncFormatter
from PIL import Image

from .data import read_series, read_categories, step_window, annual_changes, rebase


def _json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _typography(brand):
    """Validate optional pixel sizes without changing legacy layout defaults."""
    values = brand.get('typography', {})
    if not isinstance(values, dict):
        raise ValueError('Brand typography must be an object of font sizes in pixels.')
    allowed = {'title_px', 'subtitle_px', 'axis_tick_px'}
    if set(values) - allowed:
        raise ValueError('Unknown typography setting; use title_px, subtitle_px or axis_tick_px.')
    for name, value in values.items():
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 0):
            raise ValueError(f'typography.{name} must be a positive finite number of pixels.')
    return dict(values)


def _load_brand(path):
    """Palettes inherit typography from their sibling brand.json, then override it."""
    path = Path(path).resolve()
    brand = _json(path)
    own = _typography(brand)
    shared_path = path.with_name('brand.json')
    shared, source = {}, None
    if shared_path != path and shared_path.is_file():
        shared = _typography(_json(shared_path))
        if shared:
            source = {'file': shared_path.name, 'sha256': _digest(shared_path)}
    brand['typography'] = {**shared, **own}
    brand['_typography_base'] = source
    return brand


def _required(obj, names, context):
    for key in names:
        if key not in obj or obj[key] in (None, '', []):
            raise ValueError(f'{context}: provide {key}.')


def _publish(staged, destination, files, post_id, *, language=None):
    """Replace managed outputs only, removing obsolete slides on a shorter rerender."""
    destination.mkdir(parents=True, exist_ok=True)
    manifest = destination / 'manifest.json'
    previous = set()
    if manifest.exists():
        old = _json(manifest)
        if old.get('project') != 'datenfutter' or old.get('post_id') != post_id:
            raise ValueError('Output directory belongs to another post; choose a new --out folder.')
        if language is not None and old.get('language') != language:
            raise ValueError('Output directory belongs to another or unknown language; choose a new --out folder.')
        for item in old.get('outputs', []):
            name = item['file']
            if not re.fullmatch(r'(\d{2}\.(png|svg)|caption\.md|alt-text\.md)', name):
                raise ValueError('Prior output manifest contains an unmanaged filename.')
            previous.add(name)
        previous.add('manifest.json')
    elif any(destination.iterdir()):
        raise ValueError('Nonempty output directory has no datenfutter manifest; choose a new --out folder.')
    current = {p.name for p in files}
    numbered = {p.name for p in destination.iterdir() if re.fullmatch(r'\d{2}\.(png|svg)', p.name)}
    if numbered - previous:
        raise ValueError('Output folder contains untracked slides; move them before rerendering.')
    if any((destination / name).exists() and name not in previous for name in current):
        raise ValueError('A generated filename conflicts with an unmanaged file.')
    for path in files:
        if path.name != 'manifest.json':
            path.replace(destination / path.name)
    for name in previous - current:
        (destination / name).unlink(missing_ok=True)
    (staged / 'manifest.json').replace(manifest)
    return [destination / p.name for p in files]


class Page:
    def __init__(self, brand):
        self.w, self.h, self.dpi = brand['width'], brand['height'], brand['dpi']
        if (self.w, self.h) != (1080, 1350):
            raise ValueError('This template supports 1080 x 1350; redesign its zones for other formats.')
        self.c = brand['colors']
        self.typography = _typography(brand)
        self.fig = plt.figure(figsize=(self.w / self.dpi, self.h / self.dpi), dpi=self.dpi,
                              facecolor=self.c['cream'])
        self.boxes = []
        self.editorial = False

    def rect(self, x, y, w, h, color):
        self.fig.add_artist(Rectangle((x / self.w, 1 - (y + h) / self.h), w / self.w, h / self.h,
                                     transform=self.fig.transFigure, color=color, linewidth=0))

    def text(self, x, y, content, px, color, width, height, bold=False, align='left'):
        artist = self.fig.text(x / self.w, 1 - y / self.h, str(content),
                               fontsize=px * 72 / self.dpi, color=color, va='top', ha=align,
                               weight='bold' if bold else 'normal', linespacing=1.3)
        self.boxes.append((artist, width, height, str(content)))
        return artist

    def check(self):
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        for artist, width, height, content in self.boxes:
            box = artist.get_window_extent(renderer)
            if box.width > width + 1 or box.height > height + 1:
                raise ValueError(f'Text exceeds its layout zone; shorten or rebreak: {content[:90]!r}.')
        for ax in self.fig.axes:
            xmin, xmax = sorted(ax.get_xlim())
            ymin, ymax = sorted(ax.get_ylim())
            # Locators also expose ticks outside the view; Matplotlib does not draw them.
            labels = [label for pos, label in zip(ax.get_xticks(), ax.get_xticklabels()) if xmin <= pos <= xmax]
            labels += [label for pos, label in zip(ax.get_yticks(), ax.get_yticklabels()) if ymin <= pos <= ymax]
            for artist in [*labels, *ax.texts]:
                if not artist.get_visible() or not artist.get_text():
                    continue
                box = artist.get_window_extent(renderer)
                top = self.h - (425 if self.editorial else 465)
                bottom = 245 if self.editorial else 350
                if box.x0 < 40 or box.x1 > self.w - 40 or box.y0 < bottom or box.y1 > top:
                    raise ValueError('Chart label exceeds chart area; simplify labels or adjust the chart.')


def _frame(page, brand, spec, slide, index, total):
    if spec.get('layout') == 'editorial':
        return _editorial_frame(page, spec, slide, index, total)
    if spec.get('layout', 'classic') != 'classic':
        raise ValueError('Unknown layout; use classic or editorial.')
    c = page.c
    page.rect(0, 0, 1080, 415, c['navy'])
    if spec.get('_logo_path'):
        with Image.open(spec['_logo_path']) as logo:
            page.fig.figimage(logo.convert('RGBA').resize((54, 54), Image.Resampling.LANCZOS),
                              xo=72, yo=page.h - 94, zorder=10)
        wordmark_x = 142
    else:
        for x, y, h in [(72, 68, 15), (85, 59, 24), (98, 50, 33)]:
            page.rect(x, y, 7, h, c['cream'])
        wordmark_x = 125
    page.text(wordmark_x, 47, brand['name'], 30, c['cream'], 450, 42, True)
    page.text(1008, 57, spec['edition'], 16, c['cream'], 370, 24, align='right')
    page.text(72, 129, slide['kicker'], 17, c['cream'], 936, 26, True)
    page.text(72, 174, slide['title'], page.typography.get('title_px', 57), c['cream'], 936, 139, True)
    page.text(72, 324, slide['subtitle'], page.typography.get('subtitle_px', 24), c['cream'], 936, 66)
    page.rect(72, 437, 32, 4, c['accent'])
    page.text(72, 462, slide['chart_label'], 18, c['muted'], 936, 30, True)
    page.text(72, 1010, slide['takeaway_label'], 17, c['accent'], 936, 26, True)
    page.text(72, 1049, slide['explanation'], 26, c['navy'], 936, 98)
    page.text(72, 1171, spec['source_credit'], 22, c['muted'], 936, 28)
    page.text(72, 1204, slide['note'], 21, c['muted'], 936, 28)
    checked = (f"Stand {spec['as_of']} · Daten bis {spec['coverage_end']}" if spec.get('locale') == 'de' else
               f"Source checked {spec['as_of']} · Data through {spec['coverage_end']}")
    page.text(72, 1237, checked, 18, c['muted'], 936, 25)
    page.rect(72, 1271, 936, 1, c['grid'])
    page.text(72, 1296, brand['tagline'], 17, c['navy'], 750, 27)
    page.text(1008, 1292, f'{index:02d} / {total:02d}', 20, c['navy'], 160, 31, True, 'right')


def _editorial_frame(page, spec, slide, index, total):
    """A reusable cream page with the requested quiet signature and navigation."""
    page.editorial = True
    c = page.c
    if not spec.get('_logo_path'):
        raise ValueError('Editorial layout requires a supplied logo_file.')
    ink = c.get('text', '#000000')
    page.rect(51, 130, 5, 118, c['navy'])
    page.text(72, 62, slide['kicker'], 20, ink, 800, 32, True)
    page.text(1008, 57, f'{index}/{total}', 24, c['navy'], 140, 34, bold=True, align='right')
    page.text(72, 127, slide['title'], page.typography.get('title_px', 57), ink, 936, 145, True)
    subtext = slide['subtitle']
    if slide.get('chart_label'):
        subtext += '\n' + slide['chart_label']
    page.text(72, 295, subtext, page.typography.get('subtitle_px', 26), ink, 936, 134)
    page.text(72, 1181, spec['source_credit'], 23, ink, 936, 32)
    page.text(72, 1218, slide['note'], 22, ink, 936, 33)
    de = spec.get('locale') == 'de'
    checked = date.fromisoformat(spec['as_of']).strftime('%d.%m.%Y') if de else spec['as_of']
    page.text(72, 1280, ('Stand: ' if de else 'As of: ') + checked, 22, ink, 750, 32)
    with Image.open(spec['_logo_path']) as logo:
        page.fig.figimage(logo.convert('RGBA').resize((66, 66), Image.Resampling.LANCZOS),
                          xo=942, yo=43, zorder=10)


def _axes(page):
    rect = [118 / 1080, 290 / 1350, 706 / 1080, 605 / 1350] if page.editorial else [120 / 1080, 425 / 1350, 824 / 1080, 402 / 1350]
    ax = page.fig.add_axes(rect)
    ax.set_facecolor(page.c['cream'])
    ax.set_axisbelow(True)
    for spine in ('top', 'right', 'left'):
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color(page.c['grid'])
    tick_color = page.c.get('text', '#000000') if page.editorial else page.c['muted']
    ax.tick_params(axis='both', colors=tick_color,
                   labelsize=page.typography.get('axis_tick_px', 21) * 72 / page.dpi, length=0, pad=12)
    return ax


def _fmt(value, chart, signed=False):
    text = f"{value:+.{chart.get('decimals', 1)}f}" if signed else f"{value:.{chart.get('decimals', 1)}f}"
    if chart.get('locale') == 'de':
        text = text.replace('.', ',').replace('-', '−')
    return text + chart.get('suffix', '')


def _tick_number(value, chart):
    text = f'{value:g}'
    return text.replace('.', ',').replace('-', '−') if chart.get('locale') == 'de' else text


def _comparison_line(page, chart, inputs, spec):
    """Plot independently identified observations on one validated common scale."""
    start, end = date.fromisoformat(chart['start']), date.fromisoformat(chart['end'])
    if start >= end or end > date.fromisoformat(spec['coverage_end']):
        raise ValueError('Comparison period exceeds verified data coverage.')
    if chart['type'] != 'line' or spec.get('series_kind') != 'observations':
        raise ValueError('Multiple series currently require observation line charts.')
    if not 2 <= len(inputs) <= 4:
        raise ValueError('Use two to four labelled series per comparison.')
    identities, prepared = set(), []
    for item, rows in inputs:
        _required(item, ['id', 'label', 'data_file'], 'Series')
        if item['id'] in identities:
            raise ValueError('Series IDs must be unique.')
        identities.add(item['id'])
        data = [(d, v) for d, v in rows if start <= d <= end]
        if len([v for _, v in data if v is not None]) < 2:
            raise ValueError('Each line needs at least two numeric observations.')
        prepared.append((item, data))
    if chart.get('transform') == 'index_100':
        if len({data[0][0] for _, data in prepared}) != 1:
            raise ValueError('Indexed comparisons require the same actual baseline date.')
        prepared = [(item, rebase(data)) for item, data in prepared]
    elif chart.get('transform') not in (None, 'none'):
        raise ValueError('Unknown comparison transform.')
    values = [v for _, rows in prepared for _, v in rows if v is not None]
    low, high = min(values), max(values)
    pad = max((high - low) * .15, .25)
    limits = chart.get('y_limits', [low - pad, high + pad])
    if (len(limits) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in limits)
            or limits[0] >= limits[1] or low < limits[0] or high > limits[1]):
        raise ValueError('Y limits must contain every observation in every series.')
    ax = _axes(page)
    # Reserve a right-hand lane for labels in either page composition.
    if not page.editorial:
        pos = ax.get_position()
        ax.set_position([pos.x0, pos.y0, 706 / 1080, pos.height])
    ax.set_ylim(*limits)
    ax.set_xlim(start, end)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=8, steps=[1, 2, 5, 10]))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _tick_number(v, chart)))
    ax.grid(axis='y', color=page.c['grid'], linewidth=.7)
    if limits[0] <= 0 <= limits[1]:
        ax.axhline(0, color=page.c['muted'], linewidth=1)
    span = (end - start).days
    ticks = [start] + [date(y, 1, 1) for y in range(start.year + 1, end.year)
                      if y % max(1, math.ceil((end.year - start.year) / 5)) == 0] + [end]
    ticks = [t for i, t in enumerate(ticks) if i in (0, len(ticks)-1) or min((t-start).days, (end-t).days) > span*.09]
    ax.set_xticks(ticks, [str(t.year) if span >= 365 else t.strftime('%m/%Y') for t in ticks])
    ax.get_xticklabels()[0].set_ha('left')
    ax.get_xticklabels()[-1].set_ha('right')
    palette = ['navy', 'accent', 'muted', 'navy']
    styles = ['-', '--', '-.', ':']
    endpoints, summaries = [], []
    for i, (item, rows) in enumerate(prepared):
        color = page.c.get(item.get('color', palette[i]), item.get('color', page.c[palette[i]]))
        linestyle = item.get('linestyle', styles[i])
        finite = [(d, v) for d, v in rows if v is not None]
        break_dates = item.get('break_dates', chart.get('break_dates', []))
        breaks = {date.fromisoformat(d) for d in break_dates}
        if not breaks <= {d for d, _ in finite}:
            raise ValueError('Break dates must match numeric observations.')
        segments = [[]]
        for row in rows:
            if row[1] is None:
                if segments[-1]:
                    segments.append([])
                continue
            if row[0] in breaks and segments[-1]:
                segments.append([])
            segments[-1].append(row)
        for segment in filter(None, segments):
            ax.plot([d for d, _ in segment], [math.nan if v is None else v for _, v in segment],
                    color=color, linestyle=linestyle, linewidth=2.5, label=item['label'],
                    marker='o' if len(segment) == 1 or chart.get('point_markers') else None,
                    markersize=4, solid_capstyle='round')
        d, v = finite[-1]
        ax.scatter(d, v, s=21, color=color, zorder=5)
        endpoints.append((v, d, item['label'], color))
        if chart.get('highlight_max'):
            pd, pv = max(finite, key=lambda row: row[1])
            ax.scatter(pd, pv, s=25, color=color, zorder=5)
            ax.annotate(_fmt(pv, chart), (pd, pv), xytext=(0, 12), textcoords='offset points',
                        ha='center', color=page.c['navy'] if page.editorial else color, weight='bold', fontsize=23 * 72 / page.dpi,
                        bbox={'facecolor': page.c['cream'], 'edgecolor': 'none', 'pad': 1.5})
        summaries.append({'id': item['id'], 'label': item['label'], 'data_file': item['data_file'],
                          'dates': [d.isoformat() for d, _ in rows], 'values': [v for _, v in rows],
                          'color': color, 'linestyle': linestyle, 'break_dates': sorted(break_dates)})
    # Move only the labels, with leaders anchored to the actual values.
    endpoints.sort()
    label_height = 90 if any((end - d).days > 35 for _, d, _, _ in endpoints) else 66
    gap = (limits[1] - limits[0]) * label_height / ax.bbox.height
    positions = []
    for v, *_ in endpoints:
        positions.append(max(v, positions[-1] + gap if positions else limits[0] + gap / 2))
    shift = max(0, positions[-1] - (limits[1] - gap / 2))
    for (v, d, label, color), position in zip(endpoints, positions):
        position -= shift
        label_text = f'{label}\n{_fmt(v, chart)}'
        if (end - d).days > 35:
            label_text += '\n' + d.strftime('%m/%Y')
        ax.annotate(label_text, xy=(d, v), xytext=(1.045, (position-limits[0])/(limits[1]-limits[0])),
                    textcoords='axes fraction', color=page.c['navy'] if page.editorial else color, fontsize=23 * 72 / page.dpi,
                    weight='bold', va='center', annotation_clip=False,
                    arrowprops={'arrowstyle':'-', 'color':color, 'lw':.85, 'connectionstyle':'angle,angleA=0,angleB=90,rad=0'})
    return {'type': 'line', 'series': summaries, 'y_limits': list(limits),
            'start': start.isoformat(), 'end': end.isoformat()}


def _category_bar(page, chart, rows):
    labels, values = zip(*rows)
    ax = _axes(page)
    pos = ax.get_position()
    ax.set_position([290 / 1080, pos.y0, 600 / 1080, pos.height])
    ax.barh(labels, values, height=.55, color=page.c['navy'])
    ax.invert_yaxis()
    ax.axvline(0, color=page.c['muted'], linewidth=1)
    ax.grid(axis='x', color=page.c['grid'], linewidth=.7)
    low, high = min(0, min(values)), max(0, max(values))
    pad = max((high-low)*.3, .5)
    ax.set_xlim(low-pad, high+pad)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _tick_number(v, chart)))
    for i, value in enumerate(values):
        ax.annotate(_fmt(value, chart), (value, i), xytext=(9 if value >= 0 else -9, 0),
                    textcoords='offset points', va='center', ha='left' if value >= 0 else 'right',
                    color=page.c['navy'], weight='bold', fontsize=24 * 72 / page.dpi)
    return {'type': 'category_bar', 'labels': list(labels), 'values': list(values),
            'x_limits': list(ax.get_xlim()), 'baseline': 0}


def _line(page, chart, rows, spec):
    start, end = date.fromisoformat(chart['start']), date.fromisoformat(chart['end'])
    if start >= end or end > date.fromisoformat(spec['coverage_end']):
        raise ValueError('Chart period is invalid or exceeds verified data coverage.')
    kind = chart['type']
    if kind == 'step':
        if spec.get('series_kind') != 'effective_date_schedule':
            raise ValueError('Step carry-forward requires an effective_date_schedule.')
        data = step_window(rows, start, end)
    else:
        data = [(d, v) for d, v in rows if start <= d <= end]
    if chart.get('transform') == 'index_100':
        if kind == 'step':
            raise ValueError('Rebasing rate schedules is not supported.')
        data = rebase(data)
    elif chart.get('transform') not in (None, 'none'):
        raise ValueError('Unknown line transform.')
    finite = [(d, v) for d, v in data if v is not None]
    if len(finite) < 2:
        raise ValueError('A line needs at least two numeric observations in the selected period.')
    ax = _axes(page)
    breaks = {date.fromisoformat(d) for d in chart.get('break_dates', [])}
    if breaks and kind != 'line':
        raise ValueError('Break dates are supported only for observation lines.')
    if not breaks <= {d for d, v in finite}:
        raise ValueError('Each break date must match a numeric observation in the window.')
    segments = [[]]
    for row in data:
        if row[0] in breaks and segments[-1]:
            segments.append([])
        segments[-1].append(row)
    for segment in segments:
        ds, vs = zip(*segment)
        ax.plot(ds, [math.nan if v is None else v for v in vs], color=page.c['navy'],
                linewidth=2.7, drawstyle='steps-post' if kind == 'step' else 'default',
                solid_capstyle='round', label='observations',
                marker='o' if chart.get('point_markers') or len(segment) == 1 else None,
                markersize=4)
    low, high = min(v for _, v in finite), max(v for _, v in finite)
    pad = max((high - low) * 0.15, 0.25)
    limits = chart.get('y_limits', [low - pad, high + pad])
    if (len(limits) != 2 or not all(isinstance(v, (float, int)) and math.isfinite(v) for v in limits)
            or limits[0] >= limits[1] or low < limits[0] or high > limits[1]):
        raise ValueError('Y limits must be finite, increasing and contain all observations.')
    ax.set_ylim(*limits)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]) if 'y_limits' in chart else MaxNLocator(nbins=5))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _tick_number(v, chart)))
    ax.grid(axis='y', color=page.c['grid'], linewidth=0.7)
    if low < 0 < high:
        ax.axhline(0, color=page.c['muted'], linewidth=0.8)
    left, right = data[0][0], data[-1][0]
    span = (right - left).days
    ax.set_xlim(mdates.date2num(left) - span * .015, mdates.date2num(right) + span * .14)
    # Endpoint-aware ticks. Long spans use calendar years; short spans use dates.
    ticks = [left] + [date(y, 1, 1) for y in range(left.year + 1, right.year + 1)
                     if (date(y, 1, 1) - left).days >= span * .17 and (right - date(y, 1, 1)).days >= span * .17] + [right]
    if len(ticks) > 5:
        ticks = [ticks[0], *ticks[1:-1:math.ceil((len(ticks) - 2) / 3)], ticks[-1]]
    tick_format = chart.get('x_label_format', 'auto')
    if tick_format not in ('auto', 'year'):
        raise ValueError('Use auto or year for x_label_format.')
    labels = [str(d.year) if tick_format == 'year' else
              d.strftime('%b %Y') if i in (0, len(ticks) - 1) or span < 365 else str(d.year)
              for i, d in enumerate(ticks)]
    ax.set_xticks(ticks, labels)
    ax.get_xticklabels()[0].set_ha('left')
    ax.get_xticklabels()[-1].set_ha('right')
    last_day, last = finite[-1]
    ax.scatter([last_day], [last], s=37, color=page.c['accent'], zorder=4)
    ax.annotate(_fmt(last, chart), (last_day, last), xytext=(10, 0), textcoords='offset points',
                va='center', color=page.c['navy'], weight='bold', fontsize=23 * 72 / page.dpi)
    if chart.get('highlight_max'):
        peak_day, peak = max(finite, key=lambda item: item[1])
        ax.scatter([peak_day], [peak], s=25, color=page.c['accent'], zorder=4)
        ax.annotate(_fmt(peak, chart), (peak_day, peak), xytext=(0, 13), textcoords='offset points',
                    ha='center', color=page.c['accent'], weight='bold', fontsize=21 * 72 / page.dpi)
    for day in sorted(breaks):
        ax.axvline(day, color=page.c['muted'], linestyle=':', linewidth=.9)
        ax.text(day, limits[1] - (limits[1] - limits[0]) * .04, 'Zeitreihenbruch' if chart.get('locale') == 'de' else 'Series break',
                ha='center', va='top', color=page.c['muted'], fontsize=20 * 72 / page.dpi,
                bbox={'facecolor': page.c['cream'], 'edgecolor': 'none', 'pad': 2.5})
    return {'type': kind, 'dates': [d.isoformat() for d, _ in data], 'values': [v for _, v in data],
            'y_limits': list(limits), 'break_dates': [d.isoformat() for d in sorted(breaks)]}


def _bar(page, chart, rows, spec):
    if chart.get('transform') != 'annual_change' or spec.get('series_kind') != 'effective_date_schedule':
        raise ValueError('Starter bar charts require annual_change of an effective_date_schedule.')
    years = chart['years']
    if len(years) > 6 or date(max(years), 12, 31) > date.fromisoformat(spec['coverage_end']):
        raise ValueError('Use at most six years within verified coverage.')
    data = annual_changes(rows, years)
    labels, values = zip(*data)
    ax = _axes(page)
    ax.grid(axis='x', color=page.c['grid'], linewidth=0.7)
    ax.barh(labels, values, height=.52, color=[page.c['navy'] if v >= 0 else page.c['cream'] for v in values],
            edgecolor=page.c['navy'], linewidth=1.6)
    ax.invert_yaxis()
    ax.axvline(0, color=page.c['navy'], linewidth=1)
    low, high = min(0, min(values)), max(0, max(values))
    pad = max((high - low) * .25, .5)
    ax.set_xlim(low - pad, high + pad)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _tick_number(v, chart)))
    for i, value in enumerate(values):
        ax.annotate(_fmt(value, chart, True), (value, i), xytext=(10 if value >= 0 else -10, 0),
                    textcoords='offset points', va='center', ha='left' if value >= 0 else 'right',
                    color=page.c['navy'], weight='bold', fontsize=25 * 72 / page.dpi)
    return {'type': 'bar', 'labels': list(labels), 'values': list(values)}


def render_post(spec_path: str | Path, output_dir: str | Path, brand_path: str | Path) -> list[Path]:
    """Validate the complete post before exporting its two formats and audit files."""
    spec_path, out, brand_path = Path(spec_path).resolve(), Path(output_dir), Path(brand_path).resolve()
    spec, brand = _json(spec_path), _load_brand(brand_path)
    if spec.get('schema_version') in ('0.3', '0.4'):
        from .editorial import render_editorial_post
        return render_editorial_post(spec_path, out, brand_path)
    _required(spec, ['id', 'edition', 'topic', 'data_file', 'sources_file', 'source_ids', 'source_credit',
                     'as_of', 'coverage_end', 'slides', 'caption_intro'], 'Post')
    date.fromisoformat(spec['as_of'])
    coverage = date.fromisoformat(spec['coverage_end'])
    data_path = (spec_path.parent / spec['data_file']).resolve()
    data_inputs = {spec['data_file']: data_path}
    if spec.get('logo_file'):
        spec['_logo_path'] = (spec_path.parent / spec['logo_file']).resolve()
    sources_path = (spec_path.parent / spec['sources_file']).resolve()
    source_map = {s['id']: s for s in _json(sources_path)['sources']}
    sources = []
    for source_id in spec['source_ids']:
        if source_id not in source_map:
            raise ValueError(f'Unknown source ID: {source_id}.')
        source = source_map[source_id]
        _required(source, ['publisher', 'title', 'url', 'retrieved_at', 'coverage_end', 'metric', 'unit', 'method'], 'Source')
        if not source['url'].startswith(('https://', 'http://')):
            raise ValueError('Source URL must be an HTTP(S) address.')
        if coverage > date.fromisoformat(source['coverage_end']):
            raise ValueError('Post coverage exceeds its source register.')
        sources.append(source)
    row_cache = {}
    try:
        font_manager.findfont(font_manager.FontProperties(family=brand['font']), fallback_to_default=False)
    except ValueError as exc:
        raise ValueError(f"Brand font {brand['font']!r} is not installed; install it before rendering.") from exc
    pages, summaries, exported = [], [], []
    if len(spec['slides']) > 10:
        raise ValueError('Keep a post to at most ten slides in this starter.')
    style = {'font.family': brand['font'], 'svg.fonttype': 'none', 'axes.unicode_minus': True,
             'text.parse_math': False}
    destination = out
    destination.parent.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(style), tempfile.TemporaryDirectory(prefix='.datenfutter-', dir=destination.parent) as temp:
        out = Path(temp)
        try:
            for index, slide in enumerate(spec['slides'], 1):
                _required(slide, ['kicker', 'title', 'subtitle', 'chart_label', 'chart', 'takeaway_label',
                                  'explanation', 'note', 'alt_text'], f'Slide {index}')
                kind = slide['chart'].get('type')
                if kind not in ('line', 'step', 'bar', 'category_bar'):
                    raise ValueError(f'Unsupported chart type: {kind}.')
                page = Page(brand)
                pages.append(page)
                _frame(page, brand, spec, slide, index, len(spec['slides']))
                file_name = slide.get('data_file', spec['data_file'])
                slide_path = (spec_path.parent / file_name).resolve()
                data_inputs[file_name] = slide_path
                chart = {**slide['chart'], 'locale': spec.get('locale', 'en')}
                if 'series' in chart:
                    inputs = []
                    for item in chart['series']:
                        _required(item, ['id', 'label', 'data_file'], 'Series')
                        series_path = (spec_path.parent / item['data_file']).resolve()
                        data_inputs[item['data_file']] = series_path
                        if series_path not in row_cache:
                            row_cache[series_path] = read_series(series_path)
                        inputs.append((item, row_cache[series_path]))
                    summary = _comparison_line(page, chart, inputs, spec)
                elif kind == 'category_bar':
                    summary = _category_bar(page, chart, read_categories(slide_path))
                else:
                    if slide_path not in row_cache:
                        row_cache[slide_path] = read_series(slide_path)
                    rows = row_cache[slide_path]
                    summary = _bar(page, chart, rows, spec) if kind == 'bar' else _line(page, chart, rows, spec)
                summary['data_file'] = file_name
                summaries.append(summary)
                page.check()
            out.mkdir(parents=True, exist_ok=True)
            for index, page in enumerate(pages, 1):
                for extension in ('png', 'svg'):
                    path = out / f'{index:02d}.{extension}'
                    page.fig.savefig(path, dpi=brand['dpi'], facecolor=brand['colors']['cream'],
                                     metadata={'Title': spec['slides'][index - 1]['title'].replace('\n', ' ')})
                    exported.append(path)
            de = spec.get('locale') == 'de'
            credit = '\n'.join(f"- {s['publisher']}: {s['title']}. {s['url']} ({'abgerufen' if de else 'checked'} {s['retrieved_at']})" for s in sources)
            caption = f"# {spec['topic']}\n\n{spec['caption_intro']}\n\n" + '\n\n'.join(s['explanation'].replace('\n', ' ') for s in spec['slides'])
            caption += ('\n\nMethode: ' if de else '\n\nMethod: ') + ' '.join(dict.fromkeys(s['method'] for s in sources))
            caption += f"\n\n{'Quellen' if de else 'Sources'}:\n{credit}\n"
            alt = '\n\n'.join(f"{'Folie' if de else 'Slide'} {i}: {s['alt_text']}" for i, s in enumerate(spec['slides'], 1)) + '\n'
            for name, content in [('caption.md', caption), ('alt-text.md', alt)]:
                path = out / name
                path.write_text(content, encoding='utf-8')
                exported.append(path)
            manifest = {
                'project': 'datenfutter', 'version': '0.3.0', 'post_id': spec['id'],
                'rendered_at_utc': datetime.now(timezone.utc).isoformat(),
                'matplotlib_version': matplotlib.__version__, 'font': brand['font'],
                'typography': {'title_px': 57, 'subtitle_px': 26 if spec.get('layout') == 'editorial' else 24,
                               'axis_tick_px': 21, **brand['typography']},
                'typography_base': brand['_typography_base'],
                'renderer_sha256': _digest(__file__),
                'canvas': [brand['width'], brand['height']],
                'data': {'file': spec['data_file'], 'sha256': _digest(data_path)},
                'data_files': [{'file': name, 'sha256': _digest(path)} for name, path in data_inputs.items()],
                'logo': {'file': spec['logo_file'], 'sha256': _digest(spec['_logo_path'])} if spec.get('logo_file') else None,
                'spec_sha256': _digest(spec_path), 'brand_sha256': _digest(brand_path),
                'sources_sha256': _digest(sources_path), 'sources': sources, 'slides': summaries,
                'outputs': [{'file': p.name, 'sha256': _digest(p)} for p in exported]
            }
            path = out / 'manifest.json'
            path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            exported.append(path)
            exported = _publish(out, destination, exported, spec['id'])
        finally:
            for page in pages:
                plt.close(page.fig)
    return exported
