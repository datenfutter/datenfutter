"""German and English source-linked pages for schema 0.4 (0.3 alias retained).

The chart engine, project evidence, content and palette are separate inputs.
Rendering creates a reviewable local preview, never a Drive upload or approval.
"""
import csv
import json
import math
import tempfile
from datetime import date, datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image, ImageFont

from .charts import render_chart
from .data import read_series
from .localization import display_date, labels
from .render import Page, _digest, _json, _load_brand, _publish, _required


def _ids(ids, numbers):
    if not isinstance(ids, list) or not ids:
        raise ValueError('Every data series and factual text block requires source_ids.')
    if len(set(ids)) != len(ids) or any(s not in numbers for s in ids):
        raise ValueError('Source IDs must be unique and present in the post source register.')
    return ids


def _cited(block, numbers):
    _required(block, ['text', 'source_ids'], 'Factual text block')
    ids = _ids(block['source_ids'], numbers)
    return block['text'] + ' ' + ', '.join(f'[{numbers[s]}]' for s in ids)


def _categories(path):
    rows = []
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {'category', 'value'} <= set(reader.fieldnames):
            raise ValueError('Bar CSV requires category,value headers.')
        for row in reader:
            try:
                category, raw = row['category'].strip(), row['value'].strip()
                value = float(raw) if raw else None
            except (AttributeError, ValueError, TypeError) as exc:
                raise ValueError('Invalid category or number in bar CSV.') from exc
            if not category or (value is not None and not math.isfinite(value)):
                raise ValueError('Use nonempty categories and finite values; blank means missing.')
            rows.append((category, value))
    return rows


def _sources(spec, source_path):
    rows = _json(source_path)['sources']
    source_map = {row['id']: row for row in rows}
    if len(rows) != len(source_map):
        raise ValueError('Duplicate source ID in source register.')
    ids = spec['source_ids']
    if len(set(ids)) != len(ids) or any(s not in source_map for s in ids):
        raise ValueError('Post sources must be unique and present in the source register.')
    selected = [source_map[s] for s in ids]
    for source in selected:
        _required(source, ['publisher', 'title', 'short_title', 'url', 'retrieved_at'], 'Source')
        if not source['url'].startswith(('https://', 'http://')):
            raise ValueError('Source URL must be HTTP(S).')
        timestamp = datetime.fromisoformat(source['retrieved_at'])
        if timestamp.utcoffset() is None:
            raise ValueError('Source retrieval time must include its timezone.')
        if timestamp.date() > date.fromisoformat(spec['as_of']):
            raise ValueError('Post as_of cannot predate a cited retrieval.')
        if source.get('raw_file'):
            if not source.get('raw_sha256') or _digest(source_path.parent / source['raw_file']) != source['raw_sha256']:
                raise ValueError('Source evidence hash mismatch or missing hash.')
    return selected, {s: n for n, s in enumerate(ids, 1)}


def _caption(spec, sources, numbers):
    words = labels(spec['language'])
    paragraphs = []
    if 'caption_title' in spec:
        title = spec['caption_title']
        if not isinstance(title, str) or not title.strip():
            raise ValueError('caption_title must be nonempty text.')
        paragraphs.append(f'**{title.strip()}**')
    paragraphs.extend(_cited(block, numbers) for block in spec['caption'])
    paragraphs.append(f"**{words['sources']}**")
    for source in sources:
        checked = display_date(datetime.fromisoformat(source['retrieved_at']).date(), spec['language'])
        paragraphs.append(f"[{numbers[source['id']]}] {source['publisher']}: "
                          f"{source['title']}.\n{source['url']}\n{words['retrieved']}: {checked}.")
    methods = spec.get('caption_methods', [])
    if not isinstance(methods, list):
        raise ValueError('caption_methods must be a list of cited text blocks.')
    if methods:
        paragraphs.append(f"**{words['methods']}**")
        paragraphs.extend(_cited(block, numbers) for block in methods)
    return '\n\n'.join(paragraphs) + '\n'


def _check_page(page):
    """Check this layout's actual text extents before replacing any outputs."""
    page.fig.canvas.draw()
    renderer = page.fig.canvas.get_renderer()
    for artist, width, height, content in page.boxes:
        box = artist.get_window_extent(renderer)
        if box.width > width + 1 or box.height > height + 1:
            raise ValueError(f'Text exceeds its layout zone: {content[:90]!r}.')
        if box.x0 < 36 or box.x1 > page.w - 36 or box.y0 < 32 or box.y1 > page.h - 32:
            raise ValueError('Editorial text exceeds the page safe area.')
    for ax in page.fig.axes:
        xmin, xmax = sorted(ax.get_xlim())
        ymin, ymax = sorted(ax.get_ylim())
        labels = [a for p, a in zip(ax.get_xticks(), ax.get_xticklabels()) if xmin <= p <= xmax]
        labels += [a for p, a in zip(ax.get_yticks(), ax.get_yticklabels()) if ymin <= p <= ymax]
        labels += ax.texts
        if ax.get_legend() is not None:
            labels += [ax.get_legend()]
        for artist in labels:
            if not artist.get_visible():
                continue
            box = artist.get_window_extent(renderer)
            if box.x0 < 36 or box.x1 > page.w - 36 or box.y0 < 245 or box.y1 > page.h - 385:
                raise ValueError('Chart label exceeds its layout area; simplify labels or split the chart.')


def _frame(page, spec, slide, index, sources, numbers, logo):
    words = labels(spec['language'])
    c = page.c
    ink = c.get('text', '#000000')
    page.rect(54, 135, 5, 120, c['navy'])
    page.text(76, 66, slide['kicker'], 21, ink, 770, 30, True)
    page.text(1004, 62, f"{index}/{len(spec['slides'])}", 27, c['navy'], 125, 40, bold=True, align='right')
    page.text(76, 132, slide['title'], page.typography.get('title_px', 58), ink, 928, 149, True)
    page.text(76, 303, _cited(slide['subtitle'], numbers), page.typography.get('subtitle_px', 25), ink, 928, 96)
    if slide.get('end_label_heading'):
        page.text(808, 398, _cited(slide['end_label_heading'], numbers), 21, c['navy'], 230, 28, True)
    page.text(76, 1123, _cited(slide['note'], numbers), 22, ink, 928, 60)
    slide_ids = {s for block in ('subtitle', 'note', 'alt_text') for s in slide[block]['source_ids']}
    slide_ids.update(s for item in slide['chart']['series'] for s in item['source_ids'])
    if slide.get('end_label_heading'):
        slide_ids.update(slide['end_label_heading']['source_ids'])
    credit = ' · '.join(f"[{numbers[s['id']]}] {s['publisher']}: {s['short_title']}" for s in sources if s['id'] in slide_ids)
    if slide['chart'].get('stacked'):
        font_path = font_manager.findfont(font_manager.FontProperties(family=page.fig.texts[0].get_fontfamily()))
        font = ImageFont.truetype(font_path, 21)
        lines = ['']
        for item in credit.split(' · '):
            candidate = (lines[-1] + ' · ' if lines[-1] else '') + item
            if font.getlength(candidate) > 920 and lines[-1]:
                lines.append(item)
            else:
                lines[-1] = candidate
        credit = '\n'.join(lines)
        page.text(76, 1187, credit, 21, ink, 928, 54)
        page.text(76, 1243, words['source_note'], 20, ink, 825, 28)
    else:
        page.text(76, 1200, credit, 21, ink, 928, 28)
        page.text(76, 1231, words['source_note'], 20, ink, 825, 28)
    date_text = words['as_of'] + ': ' + display_date(date.fromisoformat(spec['as_of']), spec['language'])
    page.text(76, 1293, date_text, 22, ink, 710, 30)
    with Image.open(logo) as image:
        if image.width != image.height:
            raise ValueError('The df logo asset must have a square canvas.')
        page.fig.figimage(image.convert('RGBA').resize((76, 76), Image.Resampling.LANCZOS),
                          xo=932, yo=31, zorder=10)


def render_editorial_post(spec_path, out, brand_path):
    spec_path, out, brand_path = Path(spec_path), Path(out), Path(brand_path)
    spec, brand = _json(spec_path), _load_brand(brand_path)
    _required(spec, ['id', 'language', 'as_of', 'coverage_end', 'sources_file', 'source_ids',
                     'logo_file', 'slides', 'caption'], 'Post')
    words = labels(spec['language'])
    publication = spec.get('publication', words['publication'])
    if publication != words['publication']:
        raise ValueError('The publication must match its language: datenfutter=de, datafodder=en.')
    if not 1 <= len(spec['slides']) <= 10:
        raise ValueError('Provide one to ten slides.')
    coverage = date.fromisoformat(spec['coverage_end'])
    source_path = (spec_path.parent / spec['sources_file']).resolve()
    sources, numbers = _sources(spec, source_path)
    source_map = {s['id']: s for s in sources}
    logo = (spec_path.parent / spec['logo_file']).resolve()
    caption = _caption(spec, sources, numbers)
    font_manager.findfont(font_manager.FontProperties(family=brand['font']), fallback_to_default=False)
    theme = {**brand['colors'], 'dpi': brand['dpi'], 'language': spec['language']}
    style = {'font.family': brand['font'], 'svg.fonttype': 'none', 'svg.hashsalt': 'datenfutter', 'axes.unicode_minus': True,
             'text.parse_math': False}
    pages, summaries, inputs = [], [], {}
    out.parent.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(style), tempfile.TemporaryDirectory(prefix='.datenfutter-', dir=out.parent) as tmp:
        staged, files = Path(tmp), []
        try:
            for index, slide in enumerate(spec['slides'], 1):
                _required(slide, ['kicker', 'title', 'subtitle', 'note', 'alt_text', 'chart'], 'Slide')
                for field in ('subtitle', 'note', 'alt_text'):
                    _cited(slide[field], numbers)
                chart = slide['chart']
                _required(chart, ['type', 'series'], 'Chart')
                if chart['type'] != 'bar' and date.fromisoformat(chart['end']) > coverage:
                    raise ValueError('Chart window exceeds verified post coverage.')
                prepared = []
                for item in chart['series']:
                    _required(item, ['id', 'label', 'data_file', 'color_role', 'source_ids'], 'Series')
                    for sid in _ids(item['source_ids'], numbers):
                        source = source_map[sid]
                        _required(source, ['coverage_end', 'metric', 'unit', 'method'], 'Data source')
                        if coverage > date.fromisoformat(source['coverage_end']):
                            raise ValueError('Post coverage exceeds a data source.')
                    path = (spec_path.parent / item['data_file']).resolve()
                    rows = _categories(path) if chart['type'] == 'bar' else read_series(path)
                    inputs[item['data_file']] = path
                    prepared.append({**item, 'rows': rows, 'color': theme[item['color_role']]})
                page = Page(brand)
                pages.append(page)
                _frame(page, spec, slide, index, sources, numbers, logo)
                # A compact plot leaves room for direct labels; the page checker
                # rejects overflow instead of silently shrinking type or clipping.
                bounds = ([250 / 1080, 300 / 1350, 745 / 1080, 530 / 1350]
                          if chart.get('stacked') else
                          [130 / 1080, 300 / 1350, 660 / 1080, 620 / 1350])
                ax = page.fig.add_axes(bounds)
                ax.set_facecolor(theme['cream'])
                for side in ('top', 'right', 'left'):
                    ax.spines[side].set_visible(False)
                ax.spines['bottom'].set_color(theme['grid'])
                ax.tick_params(axis='both', colors=theme.get('text', '#000000'), length=0, pad=12,
                               labelsize=page.typography.get('axis_tick_px', 21) * 72 / theme['dpi'])
                summary = render_chart(ax, chart, prepared, theme)
                summary['data_files'] = [item['data_file'] for item in chart['series']]
                summary['statements'] = {field: slide[field] for field in ('subtitle', 'note', 'alt_text')}
                if slide.get('end_label_heading'):
                    summary['statements']['end_label_heading'] = slide['end_label_heading']
                summaries.append(summary)
                _check_page(page)
                for extension in ('png', 'svg'):
                    path = staged / f'{index:02d}.{extension}'
                    page.fig.savefig(path, dpi=brand['dpi'], facecolor=brand['colors']['cream'],
                                     metadata={'Title': slide['title'].replace('\n', ' '),
                                               **({'Date': None} if extension == 'svg' else {})})
                    files.append(path)
            alt = '\n\n'.join(f"{words['slide']} {i}: {_cited(s['alt_text'], numbers)}" for i, s in enumerate(spec['slides'], 1)) + '\n'
            for name, content in [('caption.md', caption), ('alt-text.md', alt)]:
                path = staged / name
                path.write_text(content, encoding='utf-8')
                files.append(path)
            manifest = {
                'project': 'datenfutter', 'version': '0.4.0', 'post_id': spec['id'],
                'review_status': 'preview', 'language': spec['language'],
                'publication': publication,
                'matplotlib_version': matplotlib.__version__, 'font': brand['font'],
                'typography': {'title_px': 58, 'subtitle_px': 25, 'axis_tick_px': 21, **brand['typography']},
                'typography_base': brand['_typography_base'],
                'palette_id': brand.get('palette_id'), 'palette_status': brand.get('status'),
                'canvas': [brand['width'], brand['height']],
                'data_files': [{'file': name, 'sha256': _digest(path)} for name, path in inputs.items()],
                'logo': {'file': spec['logo_file'], 'sha256': _digest(logo)},
                'spec_sha256': _digest(spec_path), 'brand_sha256': _digest(brand_path),
                'sources_sha256': _digest(source_path), 'sources': sources, 'citations': numbers,
                'renderer_files': {name: _digest(Path(__file__).parent / name) for name in ('editorial.py', 'charts.py', 'render.py', 'data.py', 'localization.py')},
                'slides': summaries,
                'outputs': [{'file': p.name, 'sha256': _digest(p)} for p in files],
            }
            path = staged / 'manifest.json'
            path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            files.append(path)
            return _publish(staged, out, files, spec['id'], language=spec['language'])
        finally:
            for page in pages:
                plt.close(page.fig)
