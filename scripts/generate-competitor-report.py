#!/usr/bin/env python3
"""
generate-competitor-report.py

Generates a self-contained competitor-report.html with two tabs:
  Tab 1 — Market Insights  (rendered from market-insights.md)
  Tab 2 — Competitor Report (card grid from competitors.json)

Usage:
  python3 scripts/generate-competitor-report.py --niche personalized-gift-for-dad
"""

import json, argparse, datetime, re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def niche_to_title(niche: str) -> str:
    return niche.replace('-', ' ').title()


# ── Markdown → HTML (for market-insights.md) ──────────────────────────────────

def inline(text, lookup=None):
    """Inline markdown: source tags, bold, code, links, listing ID chips."""
    text = re.sub(r'`(\[our data[^\]]*\])`',
                  lambda m: '<span class="src-tag src-our-data" title="' + m.group(1) + '">' + m.group(1) + '</span>', text)
    text = re.sub(r'`(\[inferred[^\]]*\])`',
                  lambda m: '<span class="src-tag src-inferred" title="' + m.group(1) + '">' + m.group(1) + '</span>', text)
    text = re.sub(r'`(\[market knowledge[^\]]*\])`',
                  lambda m: '<span class="src-tag src-market" title="' + m.group(1) + '">' + m.group(1) + '</span>', text)
    text = re.sub(r'`([^`]+)`', r'<code class="mi-code">\1</code>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    if lookup:
        def replace_id(m):
            item = lookup.get(m.group(1))
            if not item:
                return m.group(0)
            reviews = f'{item["reviews"]:,}&#9733;' if item.get('reviews') else ''
            tip = item['title'][:80] + (' · ' + f'{item["reviews"]:,} reviews' if item.get('reviews') else '') + ' · ' + item.get('price', '')
            return (
                '<a href="' + item['url'] + '" class="li-ref" title="' + tip + '" target="_blank">'
                + '<img class="li-ref-img" src="' + item['image_url'] + '" alt="" loading="lazy">'
                + ('<span class="li-ref-label">' + reviews + '</span>' if reviews else '')
                + '</a>'
            )
        text = re.sub(r'\b(\d{10,13})\b', replace_id, text)
    return text


def build_table(lines, lookup=None):
    rows = [l for l in lines if not re.match(r'^\|[\s\-:|]+\|', l.strip())]
    if not rows:
        return ''
    html = '<div class="mi-table-wrap"><table class="mi-table">'
    for ri, row in enumerate(rows):
        cells = [c.strip() for c in row.strip('|').split('|')]
        tag = 'th' if ri == 0 else 'td'
        html += '<tr>' + ''.join('<' + tag + '>' + inline(c, lookup) + '</' + tag + '>' for c in cells) + '</tr>'
    html += '</table></div>'
    return html


def md_to_html(md_text, lookup=None):
    """Parse market-insights.md → (page_title, body_html)."""
    lines = md_text.split('\n')
    parts = []
    i = 0
    page_title = 'Market Insights'
    meta_lines = []

    if lines and lines[0].startswith('# '):
        page_title = lines[0][2:].strip()
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            s = lines[i].strip()
            if s:
                meta_lines.append(s)
            i += 1

    if meta_lines:
        meta_html = ' &nbsp;·&nbsp; '.join(inline(m, lookup) for m in meta_lines)
        parts.append('<div class="mi-meta">' + meta_html + '</div>')

    while i < len(lines):
        line = lines[i]

        if line.startswith('## '):
            parts.append('<h2 class="mi-h2">' + inline(line[3:].strip(), lookup) + '</h2>')
            i += 1

        elif line.startswith('### '):
            parts.append('<h3 class="mi-h3">' + inline(line[4:].strip(), lookup) + '</h3>')
            i += 1

        elif line.strip() == '---':
            parts.append('<div class="mi-hr"></div>')
            i += 1

        elif line.startswith('|'):
            tbl = []
            while i < len(lines) and lines[i].startswith('|'):
                tbl.append(lines[i])
                i += 1
            parts.append(build_table(tbl, lookup))

        elif re.match(r'^[-*] ', line):
            items = []
            while i < len(lines) and re.match(r'^[-*] ', lines[i]):
                items.append(lines[i][2:])
                i += 1
            parts.append('<ul class="mi-list">' +
                         ''.join('<li>' + inline(x, lookup) + '</li>' for x in items) +
                         '</ul>')

        elif re.match(r'^\d+\. ', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\. ', lines[i]):
                items.append(re.sub(r'^\d+\. ', '', lines[i]))
                i += 1
            parts.append('<ol class="mi-list">' +
                         ''.join('<li>' + inline(x, lookup) + '</li>' for x in items) +
                         '</ol>')

        elif line.strip() == '':
            i += 1

        else:
            parts.append('<p class="mi-p">' + inline(line, lookup) + '</p>')
            i += 1

    return page_title, '\n'.join(parts)


# ── HTML builder ───────────────────────────────────────────────────────────────

def build_top_strip(comp_data):
    """Horizontal scrollable strip of top shirts by review count."""
    top = sorted(
        [e for e in comp_data if e.get('image_url')],
        key=lambda e: e.get('reviews', 0), reverse=True
    )[:8]
    if not top:
        return ''
    cards = ''
    for item in top:
        reviews = f'{item["reviews"]:,} reviews' if item.get('reviews') else 'No reviews'
        title = item['title'][:55] + ('…' if len(item['title']) > 55 else '')
        cards += (
            '<a class="mi-top-card" href="' + item['url'] + '" target="_blank">'
            + '<img class="mi-top-card-img" src="' + item['image_url'] + '" alt="" loading="lazy">'
            + '<div class="mi-top-card-body">'
            + '<div class="mi-top-card-title">' + title + '</div>'
            + '<div class="mi-top-card-meta">' + reviews + ' &middot; ' + item.get('price', '') + '</div>'
            + '</div></a>'
        )
    return (
        '<div class="mi-top-strip">'
        + '<div class="mi-top-strip-label">Top performing listings in this niche</div>'
        + '<div class="mi-top-scroll">' + cards + '</div>'
        + '</div>'
    )


def build_html(niche, comp_data, insights_md, date_str):
    niche_title = niche_to_title(niche)
    shirt_count = sum(1 for e in comp_data if e.get('is_shirt'))
    total = len(comp_data)
    data_json = json.dumps(comp_data, separators=(',', ':'))
    lookup = {e['id']: e for e in comp_data if e.get('id')}
    top_strip = build_top_strip(comp_data)

    if insights_md:
        insights_title, insights_body = md_to_html(insights_md, lookup)
    else:
        insights_title = 'Market Insights'
        insights_body = '<p class="mi-p" style="color:var(--text-muted)">No market-insights.md found for this project.</p>'

    head = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>POD Research — {niche_title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --coral:       #E76741;
    --coral-light: #FDF1ED;
    --coral-mid:   #F5C4B4;
    --bg:          #F9F9F7;
    --surface:     #FFFFFF;
    --border:      #E8E8E4;
    --border-dark: #D0CFC9;
    --text-primary:   #1A1A18;
    --text-secondary: #6B6B63;
    --text-muted:     #9E9E94;
    --green:       #198754;
    --green-light: #D6F0E0;
    --blue:        #2563EB;
    --blue-light:  #DBEAFE;
    --purple:      #7C3AED;
    --purple-light:#EDE9FE;
    --amber:       #B45309;
    --amber-light: #FEF3C7;
    --topbar-h: 56px;
    --tabnav-h: 44px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text-primary);
    font-size: 14px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}

  /* ── Top bar ── */
  .topbar {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 32px;
    display: flex; align-items: center;
    height: var(--topbar-h);
    gap: 12px;
    position: sticky; top: 0; z-index: 200;
  }}
  .topbar-logo {{
    width: 28px; height: 28px;
    background: var(--coral); border-radius: 6px;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }}
  .topbar-logo svg {{ width: 16px; height: 16px; fill: white; }}
  .topbar-title {{ font-size: 14px; font-weight: 600; }}
  .topbar-sub {{ font-size: 13px; color: var(--text-muted); }}
  .topbar-sep {{ color: var(--border-dark); margin: 0 4px; }}

  /* ── Tab nav ── */
  .tab-nav {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 32px;
    display: flex; align-items: center;
    height: var(--tabnav-h);
    gap: 2px;
    position: sticky; top: var(--topbar-h); z-index: 199;
  }}
  .tab-btn {{
    padding: 10px 18px;
    border: none; border-bottom: 2px solid transparent;
    background: none;
    font-family: inherit; font-size: 13px; font-weight: 500;
    color: var(--text-muted);
    cursor: pointer; transition: all 0.12s;
    margin-bottom: -1px;
  }}
  .tab-btn:hover {{ color: var(--text-secondary); }}
  .tab-btn.active {{ color: var(--coral); border-bottom-color: var(--coral); font-weight: 600; }}

  /* ── Tab panels ── */
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}

  /* ══ MARKET INSIGHTS TAB ══ */
  .mi-outer {{ max-width: 880px; margin: 0 auto; padding: 36px 32px 72px; }}
  .mi-page-header {{
    margin-bottom: 28px; padding-bottom: 20px;
    border-bottom: 2px solid var(--coral-light);
  }}
  .mi-page-header h1 {{
    font-size: 22px; font-weight: 700; letter-spacing: -0.4px;
  }}
  .mi-meta {{ margin-top: 8px; font-size: 12px; color: var(--text-secondary); }}
  .mi-legend {{
    display: flex; align-items: center; flex-wrap: wrap; gap: 5px 10px;
    margin-top: 10px; font-size: 12px; color: var(--text-muted);
  }}
  .mi-legend-label {{ font-weight: 600; color: var(--text-secondary); flex-shrink: 0; }}
  .mi-legend-def {{ color: var(--text-muted); }}
  .mi-legend-sep {{ color: var(--border-dark); }}
  .mi-legend-toggle {{
    margin-left: auto; background: none; border: 1px solid var(--border-dark);
    border-radius: 999px; padding: 2px 11px;
    font-size: 11px; font-weight: 600; font-family: inherit;
    color: var(--text-secondary); cursor: pointer; transition: all 0.12s;
  }}
  .mi-legend-toggle:hover {{ border-color: var(--coral); color: var(--coral); }}
  .mi-h2 {{
    font-size: 16px; font-weight: 700;
    margin: 36px 0 12px; letter-spacing: -0.2px;
    padding: 10px 14px; border-radius: 8px;
    background: var(--coral-light); color: var(--text-primary);
    border-left: 3px solid var(--coral);
  }}
  .mi-h3 {{
    font-size: 14px; font-weight: 600;
    color: var(--text-primary); margin: 20px 0 8px;
  }}
  .mi-p {{ color: var(--text-secondary); line-height: 1.65; margin: 8px 0; }}
  .mi-hr {{ height: 1px; background: var(--border); margin: 22px 0; }}
  .mi-list {{ margin: 10px 0 10px 22px; color: var(--text-secondary); line-height: 1.65; }}
  .mi-list li {{ margin-bottom: 5px; }}
  .mi-table-wrap {{ overflow-x: auto; margin: 14px 0; }}
  .mi-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .mi-table th {{
    background: var(--bg); color: var(--text-primary); font-weight: 600;
    text-align: left; padding: 8px 12px; border: 1px solid var(--border);
    white-space: nowrap;
  }}
  .mi-table td {{
    padding: 8px 12px; border: 1px solid var(--border);
    color: var(--text-secondary); vertical-align: top; line-height: 1.5;
  }}
  .mi-table tr:nth-child(even) td {{ background: var(--bg); }}
  .mi-code {{
    font-family: 'Menlo', 'Monaco', monospace; font-size: 12px;
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 4px; padding: 1px 5px; color: var(--text-secondary);
  }}

  /* Source label tags — dot mode (default) */
  .src-tag {{
    display: inline-block;
    width: 10px; height: 10px; border-radius: 50%;
    font-size: 0; padding: 0; margin: 0 2px;
    vertical-align: middle; flex-shrink: 0; cursor: default;
  }}
  .src-our-data {{ background: #198754; }}
  .src-inferred  {{ background: #2563EB; }}
  .src-market    {{ background: #9CA3AF; }}

  /* Expanded pill mode — toggled by .labels-expanded on <body> */
  body.labels-expanded .src-tag {{
    width: auto; height: auto; border-radius: 999px;
    font-size: 11px; font-weight: 600;
    padding: 1px 8px; line-height: 1.9; white-space: nowrap;
    font-family: 'Menlo', 'Monaco', monospace; margin: 0 2px;
  }}
  body.labels-expanded .src-our-data {{ background: var(--green-light); color: #0D5C2E; border: 1px solid #A8D8BB; }}
  body.labels-expanded .src-inferred  {{ background: var(--blue-light);  color: #1E40AF; border: 1px solid #BFDBFE; }}
  body.labels-expanded .src-market    {{ background: #F3F4F6;            color: #6B7280; border: 1px solid #D1D5DB; }}

  /* Top performers strip */
  .mi-top-strip {{ margin: 0 0 32px; }}
  .mi-top-strip-label {{
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.6px; color: var(--text-muted); margin-bottom: 10px;
  }}
  .mi-top-scroll {{
    display: flex; gap: 10px; overflow-x: auto; padding-bottom: 6px;
    scrollbar-width: thin; scrollbar-color: var(--border-dark) transparent;
  }}
  .mi-top-card {{
    flex-shrink: 0; width: 148px; border-radius: 10px;
    background: var(--surface); border: 1px solid var(--border);
    text-decoration: none; color: inherit; display: block;
    transition: box-shadow 0.15s, border-color 0.15s; overflow: hidden;
  }}
  .mi-top-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-color: var(--coral); }}
  .mi-top-card-img {{ width: 100%; height: 110px; object-fit: cover; display: block; background: var(--bg); }}
  .mi-top-card-body {{ padding: 8px 10px; }}
  .mi-top-card-title {{
    font-size: 11px; font-weight: 600; line-height: 1.4; color: var(--text-primary);
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    overflow: hidden; margin-bottom: 4px;
  }}
  .mi-top-card-meta {{ font-size: 11px; color: var(--text-muted); }}

  /* Inline listing reference chips */
  .li-ref {{
    display: inline-flex; align-items: center; gap: 3px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 5px; padding: 1px 5px 1px 2px;
    text-decoration: none; color: var(--text-secondary);
    font-size: 11px; font-weight: 500; vertical-align: middle;
    transition: border-color 0.12s, color 0.12s;
  }}
  .li-ref:hover {{ border-color: var(--coral); color: var(--coral); }}
  .li-ref-img {{ width: 18px; height: 18px; object-fit: cover; border-radius: 3px; flex-shrink: 0; }}
  .li-ref-label {{ white-space: nowrap; }}

  /* ══ COMPETITOR REPORT TAB ══ */
  .page-header {{ padding: 32px 32px 0; max-width: 1600px; margin: 0 auto; }}
  .page-header h1 {{ font-size: 22px; font-weight: 700; letter-spacing: -0.4px; }}
  .page-header-meta {{
    margin-top: 6px; font-size: 13px; color: var(--text-secondary);
    display: flex; gap: 16px; flex-wrap: wrap; align-items: center;
  }}
  .meta-pill {{
    display: inline-flex; align-items: center; gap: 4px;
    background: var(--coral-light); color: var(--coral);
    border: 1px solid var(--coral-mid);
    font-size: 12px; font-weight: 600; padding: 2px 10px; border-radius: 999px;
  }}
  .controls {{
    display: flex; align-items: center; gap: 8px;
    padding: 20px 32px 0; max-width: 1600px; margin: 0 auto; flex-wrap: wrap;
  }}
  .controls-label {{
    font-size: 12px; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.6px; margin-right: 4px;
  }}
  .filter-btn {{
    padding: 5px 14px; border-radius: 999px; border: 1px solid var(--border-dark);
    background: var(--surface); cursor: pointer; font-size: 13px; font-weight: 500;
    font-family: inherit; color: var(--text-secondary); transition: all 0.12s;
  }}
  .filter-btn:hover {{ border-color: var(--coral); color: var(--coral); }}
  .filter-btn.active-all       {{ background: var(--text-primary); border-color: var(--text-primary); color: white; }}
  .filter-btn.active-shirts    {{ background: var(--green);        border-color: var(--green);        color: white; }}
  .filter-btn.active-hats      {{ background: var(--purple);       border-color: var(--purple);       color: white; }}
  .filter-btn.active-drinkware {{ background: #0369A1;             border-color: #0369A1;             color: white; }}
  .filter-btn.active-kitchen   {{ background: var(--amber);        border-color: var(--amber);        color: white; }}
  .filter-btn.active-home      {{ background: #475569;             border-color: #475569;             color: white; }}
  .filter-btn.active-bags      {{ background: #92400E;             border-color: #92400E;             color: white; }}
  .filter-btn.active-novelty   {{ background: var(--coral);        border-color: var(--coral);        color: white; }}
  .sort-select {{
    margin-left: auto; padding: 5px 12px; border: 1px solid var(--border-dark);
    border-radius: 8px; font-size: 13px; font-family: inherit;
    background: var(--surface); color: var(--text-secondary); cursor: pointer;
  }}
  .sort-select:focus {{ outline: 2px solid var(--coral); outline-offset: 1px; }}
  .visible-count {{ font-size: 12px; color: var(--text-muted); margin-left: 8px; }}
  .grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(268px, 1fr));
    gap: 14px; padding: 20px 32px 48px; max-width: 1600px; margin: 0 auto;
  }}
  .section-header {{
    grid-column: 1 / -1; display: flex; align-items: center; gap: 10px; padding: 16px 0 4px;
  }}
  .section-header-label {{
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.8px; color: var(--text-muted); white-space: nowrap;
  }}
  .section-header-label.shirts {{ color: var(--green); }}
  .section-header-line {{ flex: 1; height: 1px; background: var(--border); }}
  .section-header-line.shirts {{ background: var(--green-light); }}
  .section-header-count {{ font-size: 11px; font-weight: 500; color: var(--text-muted); white-space: nowrap; }}
  .card {{
    background: var(--surface); border-radius: 12px; border: 1px solid var(--border);
    overflow: hidden; display: flex; flex-direction: column;
    transition: box-shadow 0.15s, border-color 0.15s;
  }}
  .card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.08); border-color: var(--border-dark); }}
  .card.is-shirt {{ border-color: #A8D8BB; }}
  .card.is-shirt:hover {{ border-color: var(--green); box-shadow: 0 4px 16px rgba(25,135,84,0.12); }}
  .card-img {{
    height: 148px; display: flex; align-items: center; justify-content: center;
    position: relative; overflow: hidden;
  }}
  .card-img img {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }}
  .card-img-label {{
    font-size: 12px; font-weight: 500; color: rgba(255,255,255,0.85);
    background: rgba(0,0,0,0.25); padding: 5px 12px; border-radius: 6px;
    text-align: center; max-width: 90%; backdrop-filter: blur(4px);
  }}
  .bg-shirt    {{ background: linear-gradient(140deg, #1B3F6E 0%, #2563EB 100%); }}
  .bg-hat      {{ background: linear-gradient(140deg, #2E1B5E 0%, #7C3AED 100%); }}
  .bg-mug      {{ background: linear-gradient(140deg, #0F3D26 0%, #16A34A 100%); }}
  .bg-glass    {{ background: linear-gradient(140deg, #0D2B2B 0%, #0F766E 100%); }}
  .bg-board    {{ background: linear-gradient(140deg, #3D1F00 0%, #B45309 100%); }}
  .bg-sign     {{ background: linear-gradient(140deg, #1C1C1C 0%, #4B5563 100%); }}
  .bg-jewelry  {{ background: linear-gradient(140deg, #1C1200 0%, #CA8A04 100%); }}
  .bg-frame    {{ background: linear-gradient(140deg, #0F172A 0%, #475569 100%); }}
  .bg-other    {{ background: linear-gradient(140deg, #1E1B4B 0%, #4338CA 100%); }}
  .shirt-badge {{
    position: absolute; top: 10px; left: 10px;
    background: var(--green); color: white;
    font-size: 10px; font-weight: 700; padding: 3px 8px;
    border-radius: 4px; letter-spacing: 0.3px; text-transform: uppercase;
  }}
  .reviews-badge {{
    position: absolute; top: 10px; right: 10px;
    background: rgba(0,0,0,0.5); color: white;
    font-size: 11px; font-weight: 600; padding: 3px 8px;
    border-radius: 4px; backdrop-filter: blur(4px);
  }}
  .reviews-badge .star {{ color: #FCD34D; }}
  .demand-signal {{
    display: inline-flex; align-items: center; gap: 4px;
    background: #FFF7ED; color: #C2410C; border: 1px solid #FED7AA;
    font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 4px;
  }}
  .card-body {{ padding: 14px 16px; flex: 1; display: flex; flex-direction: column; gap: 10px; }}
  .card-title {{
    font-size: 13px; font-weight: 600; line-height: 1.45;
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
  }}
  .card-price-row {{ display: flex; align-items: baseline; gap: 8px; }}
  .price {{ font-size: 16px; font-weight: 700; }}
  .reviews-text {{ font-size: 12px; color: var(--text-muted); }}
  .reviews-text strong {{ color: var(--text-secondary); }}
  .tags {{ display: flex; flex-wrap: wrap; gap: 4px; }}
  .tag {{ font-size: 11px; font-weight: 500; padding: 2px 7px; border-radius: 4px; line-height: 1.6; }}
  .tag-shirt       {{ background: var(--green-light);  color: #0D5C2E; }}
  .tag-type        {{ background: var(--bg);           color: var(--text-secondary); border: 1px solid var(--border); }}
  .tag-dtg         {{ background: var(--blue-light);   color: #1E40AF; }}
  .tag-htv         {{ background: #FCE7F3;             color: #9D174D; }}
  .tag-embroidery  {{ background: var(--purple-light); color: #4C1D95; }}
  .tag-sublimation {{ background: var(--amber-light);  color: #92400E; }}
  .design-style {{ font-size: 12px; color: var(--text-secondary); line-height: 1.5; }}
  .key-phrases {{ display: flex; flex-wrap: wrap; gap: 4px; }}
  .phrase {{
    font-size: 11px; color: var(--text-muted); background: var(--bg);
    border: 1px solid var(--border); padding: 2px 7px; border-radius: 4px;
  }}
  .shop-row {{ font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 5px; margin-top: auto; }}
  .card-footer {{ padding: 10px 14px 14px; }}
  .open-btn {{
    display: block; width: 100%; text-align: center; padding: 7px 12px;
    background: var(--bg); border: 1px solid var(--border-dark); border-radius: 8px;
    font-size: 12px; font-weight: 600; font-family: inherit; color: var(--text-secondary);
    text-decoration: none; transition: all 0.12s; cursor: pointer;
  }}
  .open-btn:hover {{ background: var(--coral); border-color: var(--coral); color: white; }}
  .card.is-shirt .open-btn:hover {{ background: var(--green); border-color: var(--green); }}
  .notes-row {{
    font-size: 11px; color: var(--text-muted); line-height: 1.45;
    border-top: 1px solid var(--border); padding: 8px 16px 0; margin: 0 0 10px;
  }}
</style>
</head>
<body>"""

    topbar = f"""
<div class="topbar">
  <div class="topbar-logo">
    <svg viewBox="0 0 16 16"><path d="M8 2L10.5 6.5H13.5L11 9.5L12 13.5L8 11L4 13.5L5 9.5L2.5 6.5H5.5Z"/></svg>
  </div>
  <span class="topbar-title">POD Research</span>
  <span class="topbar-sep">/</span>
  <span class="topbar-sub">{niche_title}</span>
</div>

<div class="tab-nav">
  <button class="tab-btn active" onclick="switchTab('insights',this)">📊 Market Insights</button>
  <button class="tab-btn" onclick="switchTab('competitors',this)">🔍 Competitor Report</button>
</div>"""

    insights_tab = (
        '\n<div id="tab-insights" class="tab-panel active">'
        '\n  <div class="mi-outer">'
        '\n    <div class="mi-page-header">'
        '\n      <h1>' + insights_title + '</h1>'
        '\n      <div class="mi-meta">Generated ' + date_str + '</div>'
        '\n      <div class="mi-legend">'
        '\n        <span class="mi-legend-label">Source key:</span>'
        '\n        <span class="src-tag src-our-data" title="[our data]">[our data]</span>'
        '\n        <span class="mi-legend-def">scraped listings &amp; eRank</span>'
        '\n        <span class="mi-legend-sep">&middot;</span>'
        '\n        <span class="src-tag src-inferred" title="[inferred]">[inferred]</span>'
        '\n        <span class="mi-legend-def">logical conclusion from data</span>'
        '\n        <span class="mi-legend-sep">&middot;</span>'
        '\n        <span class="src-tag src-market" title="[market knowledge]">[market knowledge]</span>'
        '\n        <span class="mi-legend-def">AI training data, unverified</span>'
        '\n        <button class="mi-legend-toggle" onclick="toggleLabels(this)">Show labels</button>'
        '\n      </div>'
        '\n    </div>'
        '\n' + top_strip +
        '\n' + insights_body +
        '\n  </div>'
        '\n</div>'
    )

    competitors_tab = f"""
<div id="tab-competitors" class="tab-panel">

<div class="page-header">
  <h1>Competitor Research</h1>
  <div class="page-header-meta">
    <span>Niche: <strong>{niche_title}</strong></span>
    <span class="meta-pill">{shirt_count} shirts found</span>
    <span>{total} total listings &middot; Etsy best-sellers &middot; US only &middot; {date_str}</span>
  </div>
</div>

<div class="controls">
  <span class="controls-label">Show</span>
  <button class="filter-btn" onclick="setFilter('all',this)">All <span id="cnt-all"></span></button>
  <button class="filter-btn active-shirts" onclick="setFilter('shirts',this)">&#128085; Apparel <span id="cnt-shirts"></span></button>
  <button class="filter-btn" onclick="setFilter('hats',this)">&#129282; Hats <span id="cnt-hats"></span></button>
  <button class="filter-btn" onclick="setFilter('drinkware',this)">&#129347; Drinkware <span id="cnt-drinkware"></span></button>
  <button class="filter-btn" onclick="setFilter('kitchen',this)">&#129379; Kitchen <span id="cnt-kitchen"></span></button>
  <button class="filter-btn" onclick="setFilter('home',this)">&#127968; Home &amp; Decor <span id="cnt-home"></span></button>
  <button class="filter-btn" onclick="setFilter('bags',this)">&#128092; Bags <span id="cnt-bags"></span></button>
  <button class="filter-btn" onclick="setFilter('novelty',this)">&#127873; Novelty <span id="cnt-novelty"></span></button>
  <span class="visible-count" id="visible-count"></span>
  <select class="sort-select" onchange="setSort(this.value)">
    <option value="reviews">Sort: Most Reviews</option>
    <option value="price-asc">Price: Low &rarr; High</option>
    <option value="price-desc">Price: High &rarr; Low</option>
    <option value="rating">Highest Rated</option>
  </select>
</div>

<div class="grid" id="grid"></div>
</div>"""

    script = """
<script>
function switchTab(tabId, btn) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + tabId).classList.add('active');
  btn.classList.add('active');
}

function toggleLabels(btn) {
  const expanded = document.body.classList.toggle('labels-expanded');
  btn.textContent = expanded ? 'Hide labels' : 'Show labels';
}

const DATA = """ + data_json + """;
let filter = 'shirts', sort = 'reviews';

function getCategory(e) {
  const pt = (e.product_type||'').toLowerCase();
  if (e.is_shirt || ['pajama','socks','apron'].some(x=>pt.includes(x))) return 'shirts';
  if (pt.includes('hat') && !pt.includes('holder') && !pt.includes('organizer')) return 'hats';
  if (['mug','whiskey','glass','tumbler','decanter'].some(x=>pt.includes(x))) return 'drinkware';
  if (['cutting board','charcuterie','grill','serving','platter','burger press'].some(x=>pt.includes(x))) return 'kitchen';
  if (pt.includes('bag')) return 'bags';
  if (['frame','sign','plaque','night light','box','blanket','music box','desk mat','hat holder','organizer'].some(x=>pt.includes(x))) return 'home';
  return 'novelty';
}

const CATEGORIES = [
  { key:'shirts',    label:'Apparel',             labelClass:'shirts' },
  { key:'hats',      label:'Hats',                labelClass:'' },
  { key:'drinkware', label:'Drinkware',            labelClass:'' },
  { key:'kitchen',   label:'Kitchen & BBQ',        labelClass:'' },
  { key:'home',      label:'Home & Decor',          labelClass:'' },
  { key:'bags',      label:'Bags & Leather',        labelClass:'' },
  { key:'novelty',   label:'Novelty & Accessories', labelClass:'' },
];

function getBg(item) {
  if (item.is_shirt) return 'bg-shirt';
  const t = (item.product_type||'').toLowerCase();
  if (t.includes('hat')||t.includes('cap')) return 'bg-hat';
  if (t.includes('mug')||t.includes('tumbler')) return 'bg-mug';
  if (t.includes('glass')||t.includes('decanter')) return 'bg-glass';
  if (t.includes('board')||t.includes('tray')||t.includes('platter')) return 'bg-board';
  if (t.includes('sign')||t.includes('plaque')||t.includes('frame')) return 'bg-sign';
  if (t.includes('bracelet')||t.includes('jewelry')||t.includes('bag')||t.includes('kit')) return 'bg-jewelry';
  return 'bg-other';
}

function printTag(m) {
  if (!m||m==='unknown') return '';
  if (m==='DTG') return '<span class="tag tag-dtg">DTG</span>';
  if (m==='HTV') return '<span class="tag tag-htv">HTV</span>';
  if (m==='embroidery') return '<span class="tag tag-embroidery">Embroidery</span>';
  if (m==='sublimation') return '<span class="tag tag-sublimation">Sublimation</span>';
  return '<span class="tag tag-type">' + m + '</span>';
}

function parsePrice(p) { return parseFloat((p||'0').replace(/[^0-9.]/g,''))||0; }

function card(item) {
  const shirt = item.is_shirt;
  const revBadge = item.reviews > 0
    ? '<div class="reviews-badge"><span class="star">&#9733;</span> ' + item.reviews.toLocaleString() + '</div>' : '';
  const shirtBadge = shirt ? '<div class="shirt-badge">Shirt</div>' : '';
  const revLine = item.reviews > 0
    ? '<span class="reviews-text"><strong>' + item.reviews.toLocaleString() + '</strong> reviews &middot; &#9733; ' + item.rating + '</span>'
    : '<span class="reviews-text" style="color:var(--text-muted)">No reviews yet &middot; &#9733; ' + item.rating + '</span>';
  const phrases = (item.key_phrases||[]).map(p=>'<span class="phrase">'+p+'</span>').join('');
  const demandHtml = (item.demand_signals||[]).length > 0
    ? (item.demand_signals||[]).map(s=>'<span class="demand-signal">&#128293; '+s+'</span>').join(' ')
    : '';
  const imgInner = item.image_url
    ? '<img src="' + item.image_url + '" alt="" loading="lazy">'
    : '<div class="card-img-label">' + item.product_type + '</div>';
  return '<div class="card' + (shirt?' is-shirt':'') + '">'
    + '<div class="card-img ' + getBg(item) + '">'
    + shirtBadge + revBadge + imgInner
    + '</div>'
    + '<div class="card-body">'
    + '<div class="card-title">' + item.title + '</div>'
    + '<div class="card-price-row"><span class="price">' + item.price + '</span>' + revLine + '</div>'
    + '<div class="tags">'
    + (shirt ? '<span class="tag tag-shirt">&#128085; Apparel</span>' : '')
    + '<span class="tag tag-type">' + item.product_type + '</span>'
    + printTag(item.print_method)
    + (item.blank ? '<span class="tag tag-type">' + item.blank + '</span>' : '')
    + '</div>'
    + '<div class="design-style">' + item.design_style + '</div>'
    + (phrases ? '<div class="key-phrases">' + phrases + '</div>' : '')
    + (demandHtml ? '<div>' + demandHtml + '</div>' : '')
    + '<div class="shop-row"><svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="7" width="12" height="8" rx="1"/><path d="M5 7V5a3 3 0 116 0v2"/></svg>'
    + (item.shop_name||'—') + '</div>'
    + '</div>'
    + (item.notes ? '<div class="notes-row">' + item.notes + '</div>' : '')
    + '<div class="card-footer"><a class="open-btn" href="' + item.url + '" target="_blank">Open on Etsy &#8599;</a></div>'
    + '</div>';
}

function render() {
  let items = [...DATA];
  if (sort==='reviews') items.sort((a,b)=>b.reviews-a.reviews);
  else if (sort==='price-asc') items.sort((a,b)=>parsePrice(a.price)-parsePrice(b.price));
  else if (sort==='price-desc') items.sort((a,b)=>parsePrice(b.price)-parsePrice(a.price));
  else if (sort==='rating') items.sort((a,b)=>(b.rating||0)-(a.rating||0));

  document.getElementById('cnt-all').textContent='('+DATA.length+')';
  CATEGORIES.forEach(cat => {
    const el = document.getElementById('cnt-'+cat.key);
    if (el) el.textContent='('+DATA.filter(i=>getCategory(i)===cat.key).length+')';
  });

  let visible = 0, html = '';
  if (filter === 'all') {
    CATEGORIES.forEach(cat => {
      const group = items.filter(i=>getCategory(i)===cat.key);
      if (!group.length) return;
      html += '<div class="section-header">'
        + '<span class="section-header-label '+cat.labelClass+'">'+cat.label+'</span>'
        + '<div class="section-header-line '+cat.labelClass+'"></div>'
        + '<span class="section-header-count">'+group.length+' listings</span>'
        + '</div>';
      group.forEach(i=>{ html+=card(i); visible++; });
    });
  } else {
    const group = items.filter(i=>getCategory(i)===filter);
    const cat = CATEGORIES.find(c=>c.key===filter);
    if (group.length) {
      html += '<div class="section-header">'
        + '<span class="section-header-label '+(cat?.labelClass||'')+'">'+( cat?.label||filter)+'</span>'
        + '<div class="section-header-line '+(cat?.labelClass||'')+'"></div>'
        + '<span class="section-header-count">'+group.length+' listings</span>'
        + '</div>';
      group.forEach(i=>{ html+=card(i); visible++; });
    }
  }

  document.getElementById('visible-count').textContent = 'Showing ' + visible + ' listings';
  document.getElementById('grid').innerHTML = html || '<div style="grid-column:1/-1;text-align:center;padding:60px;color:var(--text-muted)">No results</div>';
}

function setFilter(f, btn) {
  filter = f;
  document.querySelectorAll('.filter-btn').forEach(b=>b.className='filter-btn');
  btn.className = 'filter-btn active-' + f;
  render();
}

function setSort(v) { sort=v; render(); }

render();
</script>
</body>
</html>"""

    return head + topbar + insights_tab + competitors_tab + script


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--niche', required=True, help='Niche folder name, e.g. personalized-gift-for-dad')
    args = parser.parse_args()

    json_path     = BASE_DIR / 'projects' / args.niche / '01-research' / 'competitors.json'
    insights_path = BASE_DIR / 'projects' / args.niche / '01-research' / 'market-insights.md'
    out_path      = BASE_DIR / 'projects' / args.niche / '01-research' / 'competitor-report.html'

    if not json_path.exists():
        print(f"✗ Not found: {json_path}")
        return

    comp_data   = json.load(open(json_path))
    insights_md = insights_path.read_text() if insights_path.exists() else None
    date_str    = datetime.date.today().isoformat()

    html = build_html(args.niche, comp_data, insights_md, date_str)
    out_path.write_text(html)

    shirt_count = sum(1 for e in comp_data if e.get('is_shirt'))
    print(f"✓ Generated {out_path}")
    print(f"  {len(comp_data)} listings · {shirt_count} shirts · {date_str}")
    print(f"  Market insights tab: {'✓ included' if insights_md else '✗ market-insights.md not found'}")


if __name__ == '__main__':
    main()
