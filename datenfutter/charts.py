"""Reusable chart marks and auditable summaries, independent of page layout.

The caller owns metric definitions, source coverage and transformations. This
module only plots supplied values: it never rebases, interpolates, aggregates or
extends a step schedule beyond the supplied points. Dates outside a requested
window are excluded, and null observations remain gaps.
"""
import copy
import math
import re
from datetime import date
from numbers import Real

import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator


def _date(value, context):
    if type(value) is date:
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{context}: use an ISO date.') from exc


def _number(value, context):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f'{context}: use finite numbers or None for missing values.')
    return float(value)


def _prepare(chart, series):
    """Validate the complete request before adding any artists to the axes."""
    kind = chart.get('type')
    if kind not in ('line', 'step', 'bar'):
        raise ValueError('Supported chart types are line, step and bar.')
    if chart.get('transform') not in (None, 'none'):
        raise ValueError('Transform values before calling the generic chart renderer.')
    if not isinstance(series, (list, tuple)) or not series:
        raise ValueError('Provide at least one series.')
    if chart.get('label_mode', 'direct') not in ('direct', 'legend'):
        raise ValueError('Use direct or legend for label_mode.')
    if chart.get('x_label_format', 'auto') not in ('auto', 'year'):
        raise ValueError('Use auto or year for x_label_format.')
    decimals = chart.get('decimals', 1)
    if isinstance(decimals, bool) or not isinstance(decimals, int) or not 0 <= decimals <= 10:
        raise ValueError('decimals must be an integer between zero and ten.')
    if not isinstance(chart.get('suffix', ''), str):
        raise ValueError('suffix must be text.')
    if kind == 'bar':
        if chart.get('orientation', 'horizontal') not in ('horizontal', 'vertical'):
            raise ValueError('Use horizontal or vertical for bar orientation.')
        start = end = None
    else:
        start = _date(chart.get('start'), 'Chart start')
        end = _date(chart.get('end'), 'Chart end')
        if start >= end:
            raise ValueError('Chart start must precede chart end.')

    prepared, seen_ids = [], set()
    for item in series:
        if not isinstance(item, dict):
            raise ValueError('Each series must be an object.')
        for name in ('id', 'label'):
            if not isinstance(item.get(name), str) or not item[name].strip():
                raise ValueError(f'Every series requires a nonempty {name}.')
        identifier = item['id']
        if identifier in seen_ids:
            raise ValueError(f'Duplicate series id: {identifier}.')
        seen_ids.add(identifier)
        color = item.get('color')
        if not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?', color):
            raise ValueError(f'{identifier}: provide a literal hex color.')
        style = item.get('linestyle', '-')
        marker = item.get('marker', 'o' if chart.get('point_markers') else None)
        # Matplotlib validates style syntax without attaching anything to an Axes.
        Line2D([], [], color=color, linestyle=style, marker=marker)
        source_ids = item.get('source_ids', [])
        if (not isinstance(source_ids, (list, tuple))
                or any(not isinstance(s, str) or not s.strip() for s in source_ids)):
            raise ValueError(f'{identifier}: source_ids must be a list of identifiers.')
        raw_rows = item.get('rows')
        if not isinstance(raw_rows, (list, tuple)) or not raw_rows:
            raise ValueError(f'{identifier}: provide observation rows.')
        rows, keys = [], set()
        for row in raw_rows:
            if not isinstance(row, (list, tuple)) or len(row) != 2:
                raise ValueError(f'{identifier}: rows must be pairs of position and value.')
            key, value = row
            if kind == 'bar':
                if not isinstance(key, str) or not key.strip():
                    raise ValueError(f'{identifier}: categories must be nonempty text.')
            else:
                key = _date(key, identifier)
            if key in keys:
                raise ValueError(f'{identifier}: duplicate {"category" if kind == "bar" else "date"}: {key}.')
            keys.add(key)
            rows.append((key, _number(value, identifier)))
        if kind != 'bar':
            rows = sorted((d, v) for d, v in rows if start <= d <= end)
        if not any(value is not None for _, value in rows):
            raise ValueError(f'{identifier}: no numeric observations in the selected chart.')
        raw_breaks = item.get('break_dates', [])
        if not isinstance(raw_breaks, (list, tuple)):
            raise ValueError(f'{identifier}: break_dates must be a list of ISO dates.')
        if kind == 'bar' and raw_breaks:
            raise ValueError('Category bars do not support date breaks.')
        breaks = {_date(d, f'{identifier} break') for d in raw_breaks}
        if not breaks <= {d for d, v in rows if v is not None}:
            raise ValueError(f'{identifier}: each break must match a numeric observation in the window.')
        entry = {'id': identifier, 'label': item['label'], 'color': color,
                 'linestyle': style, 'marker': marker, 'rows': rows,
                 'break_dates': sorted(breaks), 'source_ids': list(source_ids)}
        if 'flags' in item:
            entry['flags'] = copy.deepcopy(item['flags'])
        prepared.append(entry)
    return kind, start, end, prepared


def _limits(chart, series, zero):
    values = [value for item in series for _, value in item['rows'] if value is not None]
    low, high = min(values), max(values)
    if zero:
        low, high = min(low, 0), max(high, 0)
    requested = chart.get('y_limits')
    if requested is not None:
        if not isinstance(requested, (list, tuple)) or len(requested) != 2:
            raise ValueError('y_limits must contain two finite, increasing bounds.')
        limits = [_number(value, 'y_limits') for value in requested]
        if (None in limits or limits[0] >= limits[1]
                or low < limits[0] or high > limits[1]):
            raise ValueError('y_limits must contain every value and include zero for bars.')
        return limits
    pad = (high - low) * .14 if high != low else max(abs(high) * .1, .1)
    return [0.0 if zero and low == 0 else low - pad,
            0.0 if zero and high == 0 else high + pad] if low != high else [low - pad, high + pad]


def _numeric_label(value, language):
    text = f'{value:g}'
    return text.replace('.', ',') if language.startswith('de') else text


def _value_ticks(chart, limits):
    if 'value_ticks' not in chart:
        return None
    raw = chart['value_ticks']
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ValueError('value_ticks must be a nonempty array of numbers.')
    ticks = [_number(value, 'value_ticks') for value in raw]
    if (None in ticks or any(a >= b for a, b in zip(ticks, ticks[1:]))
            or ticks[0] < limits[0] or ticks[-1] > limits[1]):
        raise ValueError('value_ticks must be strictly increasing and inside the numeric scale.')
    return ticks


def _value_label(value, chart, language):
    text = f"{value:.{chart.get('decimals', 1)}f}"
    suffix = chart.get('suffix', '')
    if language.startswith('de'):
        text = text.replace('.', ',')
        if suffix.strip() == '%':
            suffix = ' %'
    return text + suffix


def _audit_series(item):
    result = {name: item[name] for name in ('id', 'label', 'color', 'linestyle', 'marker', 'source_ids')}
    if 'flags' in item:
        result['flags'] = copy.deepcopy(item['flags'])
    return result


def _segments(item):
    segments = [[]]
    breaks = set(item['break_dates'])
    for row in item['rows']:
        if row[0] in breaks and segments[-1]:
            segments.append([])
        segments[-1].append(row)
    return segments


def _legend(ax, handles, labels, theme):
    ax.legend(handles, labels, loc='upper left', bbox_to_anchor=(1.025, 1),
              borderaxespad=0, frameon=False, labelcolor=theme['navy'],
              fontsize=22 * 72 / theme['dpi'], handlelength=1.8, labelspacing=.8)


def _date_ticks(ax, chart, start, end, language):
    if chart.get('x_label_format', 'auto') == 'year' or (end - start).days >= 730:
        ticks = [date(year, 1, 1) for year in range(start.year, end.year + 1)
                 if start <= date(year, 1, 1) <= end]
        if not ticks or ticks[0].year != start.year:
            ticks.insert(0, start)
        if chart.get('x_label_format', 'auto') != 'year' and len(ticks) > 6:
            ticks = [ticks[round(i * (len(ticks) - 1) / 5)] for i in range(6)]
        ax.set_xticks(ticks)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    else:
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=5))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y' if language.startswith('de') else '%Y-%m-%d'))


def _end_labels(ax, chart, series, limits, theme, language):
    """Separate end labels vertically; leader lines keep moved labels traceable."""
    ends = [(item, next((d, v) for d, v in reversed(item['rows']) if v is not None))
            for item in series]
    ranked = sorted(ends, key=lambda entry: entry[1][1])
    gap = 33 / ax.bbox.height
    margin = gap / 2
    positions = [min(1 - margin, max(margin, (row[1] - limits[0]) / (limits[1] - limits[0])))
                 for _, row in ranked]
    for i in range(1, len(positions)):
        positions[i] = max(positions[i], positions[i - 1] + gap)
    overflow = max(0, positions[-1] - (1 - margin))
    positions = [position - overflow for position in positions]
    for (item, (day, value)), position in zip(ranked, positions):
        ax.annotate('', xy=(day, value), xycoords='data', xytext=(1.018, position),
                    textcoords='axes fraction', annotation_clip=False,
                    arrowprops={'arrowstyle': '-', 'color': item['color'], 'lw': .8, 'alpha': .6})
        ax.text(1.028, position, f"{item['label']}  {_value_label(value, chart, language)}",
                transform=ax.transAxes, va='center', ha='left', color=theme['navy'],
                fontsize=22 * 72 / theme['dpi'], clip_on=False)


def _line(ax, chart, series, start, end, limits, theme, language):
    summaries, handles = [], []
    for item in series:
        segments = _segments(item)
        for segment in segments:
            ds, vs = zip(*segment)
            isolated = any(v is not None and (i == 0 or vs[i - 1] is None)
                           and (i == len(vs) - 1 or vs[i + 1] is None) for i, v in enumerate(vs))
            artist, = ax.plot(ds, [math.nan if value is None else value for value in vs],
                              color=item['color'], linestyle=item['linestyle'],
                              marker=item['marker'] or ('o' if isolated else None), markersize=4,
                              linewidth=2.5, solid_capstyle='round', label=item['label'],
                              clip_on=False,
                              drawstyle='steps-post' if chart['type'] == 'step' else 'default')
            if segment is segments[0]:
                handles.append(artist)
        result = _audit_series(item)
        result.update(dates=[day.isoformat() for day, _ in item['rows']],
                      values=[value for _, value in item['rows']],
                      break_dates=[day.isoformat() for day in item['break_dates']],
                      segments=[{'dates': [day.isoformat() for day, _ in segment],
                                 'values': [value for _, value in segment]} for segment in segments])
        summaries.append(result)
    ax.set_xlim(mdates.date2num(start), mdates.date2num(end))
    ax.set_ylim(*limits)
    _date_ticks(ax, chart, start, end, language)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: _numeric_label(value, language)))
    ax.grid(axis='y', color=theme['grid'], linewidth=.7)
    if limits[0] < 0 < limits[1]:
        ax.axhline(0, color=theme['muted'], linewidth=.8, label='_zero')
    # The page reserves space to the right. A legend handles more crowded sets.
    if chart.get('label_mode') == 'legend' or len(series) * 33 > ax.bbox.height * .9:
        _legend(ax, handles, [item['label'] for item in series], theme)
    else:
        _end_labels(ax, chart, series, limits, theme, language)
    return {'type': chart['type'], 'series': summaries,
            'scales': {'value_axis': 'y', 'value_limits': limits,
                       'date_window': [start.isoformat(), end.isoformat()],
                       'x_label_format': chart.get('x_label_format', 'auto'),
                       'includes_zero': limits[0] <= 0 <= limits[1]}}


def _bar(ax, chart, series, limits, theme, language):
    orientation = chart.get('orientation', 'horizontal')
    horizontal = orientation == 'horizontal'
    categories = list(dict.fromkeys(category for item in series for category, _ in item['rows']))
    thickness = .8 / len(series)
    summaries, handles = [], []
    for index, item in enumerate(series):
        by_category = dict(item['rows'])
        values = [by_category.get(category) for category in categories]
        positions = [i + (index - (len(series) - 1) / 2) * thickness
                     for i, value in enumerate(values) if value is not None]
        numbers = [value for value in values if value is not None]
        kwargs = {'color': item['color'], 'edgecolor': item['color'], 'label': item['label']}
        bars = (ax.barh(positions, numbers, height=thickness * .88, **kwargs) if horizontal
                else ax.bar(positions, numbers, width=thickness * .88, **kwargs))
        handles.append(bars)
        for position, value in zip(positions, numbers):
            positive = value >= 0
            ax.annotate(_value_label(value, chart, language),
                        xy=(value, position) if horizontal else (position, value),
                        xytext=((5 if positive else -5), 0) if horizontal else (0, (5 if positive else -5)),
                        textcoords='offset points',
                        ha=('left' if positive else 'right') if horizontal else 'center',
                        va='center' if horizontal else ('bottom' if positive else 'top'),
                        color=theme['navy'], fontsize=20 * 72 / theme['dpi'], annotation_clip=False)
        result = _audit_series(item)
        result.update(categories=list(categories), values=values,
                      reported_categories=[category for category, _ in item['rows']],
                      missing_categories=[category for category, value in zip(categories, values) if value is None],
                      break_dates=[])
        summaries.append(result)
    if horizontal:
        ax.set_yticks(range(len(categories)), categories)
        ax.set_ylim(len(categories) - .5, -.5)
        ax.set_xlim(*limits)
        value_axis = ax.xaxis
        ax.axvline(0, color=theme['muted'], linewidth=.8, label='_zero')
    else:
        ax.set_xticks(range(len(categories)), categories)
        ax.set_xlim(-.5, len(categories) - .5)
        ax.set_ylim(*limits)
        value_axis = ax.yaxis
        ax.axhline(0, color=theme['muted'], linewidth=.8, label='_zero')
    value_axis.set_major_locator(MaxNLocator(nbins=5))
    value_axis.set_major_formatter(FuncFormatter(lambda value, _: _numeric_label(value, language)))
    ax.grid(axis='x' if horizontal else 'y', color=theme['grid'], linewidth=.7)
    if len(series) > 1:
        _legend(ax, handles, [item['label'] for item in series], theme)
    return {'type': 'bar', 'orientation': orientation, 'categories': categories, 'series': summaries,
            'scales': {'value_axis': 'x' if horizontal else 'y', 'value_limits': limits,
                       'category_axis': 'y' if horizontal else 'x', 'includes_zero': True}}


def _stacked_values(chart, series):
    """Require complete nonnegative compositions; never turn missing into zero."""
    if chart.get('orientation', 'horizontal') != 'horizontal':
        raise ValueError('Stacked bars currently support horizontal orientation.')
    categories = [key for key, _ in series[0]['rows']]
    matrices = []
    for item in series:
        by_category = dict(item['rows'])
        if set(by_category) != set(categories):
            raise ValueError('Every stacked component must report every category.')
        values = [by_category[key] for key in categories]
        if any(value is None or value < 0 for value in values):
            raise ValueError('Stacked components require nonnegative values; missing is not zero.')
        matrices.append(values)
    totals = [round(math.fsum(values), 9) for values in zip(*matrices)]
    expected = chart.get('expected_total')
    if expected is not None:
        expected = _number(expected, 'expected_total')
        if expected <= 0 or any(not math.isclose(value, expected, rel_tol=0, abs_tol=1e-6) for value in totals):
            raise ValueError('Stacked components do not sum to expected_total.')
    return categories, matrices, totals


def _stacked_bar(ax, chart, series, stack, limits, theme, language):
    categories, matrices, totals = stack
    left = [0.0] * len(categories)
    summaries, handles = [], []
    for item, values in zip(series, matrices):
        bars = ax.barh(range(len(categories)), values, left=left, height=.65,
                       color=item['color'], edgecolor=theme['cream'], linewidth=.8,
                       label=item['label'])
        handles.append(bars)
        channels = [int(item['color'][i:i+2], 16)/255 for i in (1,3,5)]
        linear = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in channels]
        luminance = sum(c*w for c,w in zip(linear,[.2126,.7152,.0722]))
        text_color = '#FFFFFF' if luminance < .179 else theme.get('text','#000000')
        for i, value in enumerate(values):
            if value > 0:
                center = left[i]+value/2
                label = ax.text(center, i, _value_label(value, chart, language),
                                va='center', ha='center', color=text_color,
                                fontsize=21*72/theme['dpi'])
                label_width = label.get_window_extent(ax.figure.canvas.get_renderer()).width
                segment_width = value / (limits[1]-limits[0]) * ax.bbox.width
                if label_width + 8 > segment_width:
                    label.set_position((center, i+.38))
                    label.set_verticalalignment('top')
                    label.set_color(theme['navy'])
                    ax.plot([center, center], [i+.325, i+.365],
                            color=theme['navy'], linewidth=.6, clip_on=False)
        record = _audit_series(item)
        record.update(categories=list(categories), values=list(values), offsets=list(left),
                      reported_categories=[key for key,_ in item['rows']], missing_categories=[])
        summaries.append(record)
        left = [a+b for a,b in zip(left, values)]
    ax.set_yticks(range(len(categories)), categories)
    ax.set_ylim(len(categories)-.5,-.5)
    ax.set_xlim(*limits)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value,_:_numeric_label(value,language)))
    ax.grid(axis='x',color=theme['grid'],linewidth=.7)
    ax.legend(handles,[item['label'] for item in series],loc='lower left',
              bbox_to_anchor=(0,1.06),borderaxespad=0,frameon=False,ncol=2,
              fontsize=21*72/theme['dpi'],labelcolor=theme.get('text','#000000'),
              handlelength=1.1,columnspacing=1.3,labelspacing=.65)
    return {'type':'bar','stacked':True,'orientation':'horizontal','categories':categories,
            'totals':totals,'series':summaries,
            'scales':{'value_axis':'x','value_limits':limits,'category_axis':'y','includes_zero':True}}


def render_chart(ax, chart, series, theme):
    """Draw on a caller-styled Axes and return a JSON-safe evidence summary.

    Series require id, label, rows and a literal hex color. Rows are (date,
    number-or-None) for line/step, or (category, number-or-None) for bar. Optional
    linestyle, marker, break_dates, source_ids and flags retain series identity.
    Missing bar categories remain missing, and category order is first-seen.

    Date charts require ISO start/end and support x_label_format auto/year.
    y_limits always means the numeric value domain, including horizontal bars
    (which draw values on x). Every value must fit, and bars must include zero.
    Optional value_ticks supplies finite, strictly increasing tick positions
    inside that domain; the applied positions are retained in scales.value_ticks.
    The caller must pre-window effective-date schedules if boundary carry is
    needed, after verifying coverage; this function never carries values.

    Reserve space to the right of the Axes for direct line labels or grouped-bar
    legends. label_mode='legend' optionally uses a legend for date charts.
    Theme requires cream/navy/muted/grid and dpi; language defaults to de.
    """
    kind, start, end, prepared = _prepare(chart, series)
    stacked = chart.get('stacked', False)
    if not isinstance(stacked, bool) or (stacked and kind != 'bar'):
        raise ValueError('stacked is a boolean option for bars only.')
    stack = _stacked_values(chart, prepared) if stacked else None
    limit_series = [{'rows':list(zip(stack[0],stack[2]))}] if stacked else prepared
    limits = _limits(chart, limit_series, kind == 'bar')
    ticks = _value_ticks(chart, limits)
    language = str(theme.get('language', 'de')).lower()
    for token in ('cream', 'navy', 'muted', 'grid'):
        if token not in theme:
            raise ValueError(f'Theme requires {token}.')
    dpi = _number(theme.get('dpi'), 'Theme dpi')
    if dpi is None or dpi <= 0:
        raise ValueError('Theme dpi must be positive.')
    ax.grid(False)
    ax.set_axisbelow(True)
    if stacked:
        summary = _stacked_bar(ax, chart, prepared, stack, limits, theme, language)
    elif kind == 'bar':
        summary = _bar(ax, chart, prepared, limits, theme, language)
    else:
        summary = _line(ax, chart, prepared, start, end, limits, theme, language)
    if ticks is not None:
        axis = ax.xaxis if summary['scales']['value_axis'] == 'x' else ax.yaxis
        axis.set_ticks(ticks)
        summary['scales']['value_ticks'] = ticks
    return summary
