#!/usr/bin/env python3
"""
generate-competitor-report.py

Generates a self-contained competitor-report.html from competitors.json.
All current features are baked in: images, demand signals, category filters,
demand badge, rating, sort, notes, key phrases, print method tags.

Usage:
  python3 scripts/generate-competitor-report.py --niche personalized-gift-for-dad
"""

import json, argparse, datetime, re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

def niche_to_title(niche: str) -> str:
    return niche.replace('-', ' ').title()

def build_html(niche: str, data: list, date_str: str) -> str:
    niche_title = niche_to_title(niche)
    shirt_count = sum(1 for e in data if e.get('is_shirt'))
    total = len(data)
    data_json = json.dumps(data, separators=(',', ':'))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Competitor Research — {niche_title}</title>
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
    display: flex;
    align-items: center;
    height: 56px;
    gap: 12px;
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .topbar-logo {{
    width: 28px; height: 28px;
    background: var(--coral);
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }}
  .topbar-logo svg {{ width: 16px; height: 16px; fill: white; }}
  .topbar-title {{ font-size: 14px; font-weight: 600; color: var(--text-primary); }}
  .topbar-sub {{ font-size: 13px; color: var(--text-muted); margin-left: 2px; }}
  .topbar-sep {{ color: var(--border-dark); margin: 0 4px; }}

  /* ── Page header ── */
  .page-header {{ padding: 32px 32px 0; max-width: 1600px; margin: 0 auto; }}
  .page-header h1 {{ font-size: 22px; font-weight: 700; letter-spacing: -0.4px; color: var(--text-primary); }}
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

  /* ── Controls ── */
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
  .filter-btn.active-all       {{ background: var(--text-primary);  border-color: var(--text-primary);  color: white; }}
  .filter-btn.active-shirts    {{ background: var(--green);          border-color: var(--green);          color: white; }}
  .filter-btn.active-hats      {{ background: var(--purple);         border-color: var(--purple);         color: white; }}
  .filter-btn.active-drinkware {{ background: #0369A1;               border-color: #0369A1;               color: white; }}
  .filter-btn.active-kitchen   {{ background: var(--amber);          border-color: var(--amber);          color: white; }}
  .filter-btn.active-home      {{ background: #475569;               border-color: #475569;               color: white; }}
  .filter-btn.active-bags      {{ background: #92400E;               border-color: #92400E;               color: white; }}
  .filter-btn.active-novelty   {{ background: var(--coral);          border-color: var(--coral);          color: white; }}
  .sort-select {{
    margin-left: auto; padding: 5px 12px; border: 1px solid var(--border-dark);
    border-radius: 8px; font-size: 13px; font-family: inherit;
    background: var(--surface); color: var(--text-secondary); cursor: pointer;
  }}
  .sort-select:focus {{ outline: 2px solid var(--coral); outline-offset: 1px; }}
  .visible-count {{ font-size: 12px; color: var(--text-muted); margin-left: 8px; }}

  /* ── Grid ── */
  .grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(268px, 1fr));
    gap: 14px; padding: 20px 32px 48px; max-width: 1600px; margin: 0 auto;
  }}

  /* ── Section header ── */
  .section-header {{
    grid-column: 1 / -1; display: flex; align-items: center;
    gap: 10px; padding: 16px 0 4px;
  }}
  .section-header-label {{
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.8px; color: var(--text-muted); white-space: nowrap;
  }}
  .section-header-label.shirts {{ color: var(--green); }}
  .section-header-line {{ flex: 1; height: 1px; background: var(--border); }}
  .section-header-line.shirts {{ background: var(--green-light); }}
  .section-header-count {{ font-size: 11px; font-weight: 500; color: var(--text-muted); white-space: nowrap; }}

  /* ── Card ── */
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
  .card-img img {{
    position: absolute; top: 0; left: 0;
    width: 100%; height: 100%; object-fit: cover;
  }}
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
    font-size: 13px; font-weight: 600; line-height: 1.45; color: var(--text-primary);
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
  }}
  .card-price-row {{ display: flex; align-items: baseline; gap: 8px; }}
  .price {{ font-size: 16px; font-weight: 700; color: var(--text-primary); }}
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
  .divider {{ grid-column: 1/-1; height: 1px; background: var(--border); margin: 8px 0; }}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-logo">
    <svg viewBox="0 0 16 16"><path d="M8 2L10.5 6.5H13.5L11 9.5L12 13.5L8 11L4 13.5L5 9.5L2.5 6.5H5.5Z"/></svg>
  </div>
  <span class="topbar-title">POD Research</span>
  <span class="topbar-sep">/</span>
  <span class="topbar-sub">{niche_title}</span>
  <span class="topbar-sep">/</span>
  <span class="topbar-sub">Competitor Report</span>
</div>

<div class="page-header">
  <h1>Competitor Research</h1>
  <div class="page-header-meta">
    <span>Niche: <strong>{niche_title}</strong></span>
    <span class="meta-pill">{shirt_count} shirts found</span>
    <span>{total} total listings · Etsy best-sellers · US only · Physical items · {date_str}</span>
  </div>
</div>

<div class="controls">
  <span class="controls-label">Show</span>
  <button class="filter-btn" onclick="setFilter('all',this)">All <span id="cnt-all"></span></button>
  <button class="filter-btn active-shirts" onclick="setFilter('shirts',this)">👕 Apparel <span id="cnt-shirts"></span></button>
  <button class="filter-btn" onclick="setFilter('hats',this)">🧢 Hats <span id="cnt-hats"></span></button>
  <button class="filter-btn" onclick="setFilter('drinkware',this)">🥃 Drinkware <span id="cnt-drinkware"></span></button>
  <button class="filter-btn" onclick="setFilter('kitchen',this)">🍳 Kitchen <span id="cnt-kitchen"></span></button>
  <button class="filter-btn" onclick="setFilter('home',this)">🏠 Home &amp; Decor <span id="cnt-home"></span></button>
  <button class="filter-btn" onclick="setFilter('bags',this)">👜 Bags <span id="cnt-bags"></span></button>
  <button class="filter-btn" onclick="setFilter('novelty',this)">🎁 Novelty <span id="cnt-novelty"></span></button>
  <span class="visible-count" id="visible-count"></span>
  <select class="sort-select" onchange="setSort(this.value)">
    <option value="reviews">Sort: Most Reviews</option>
    <option value="price-asc">Price: Low → High</option>
    <option value="price-desc">Price: High → Low</option>
    <option value="rating">Highest Rated</option>
  </select>
</div>

<div class="grid" id="grid"></div>

<script>
const DATA = {data_json};

let filter = 'shirts', sort = 'reviews';

function getCategory(e) {{
  const pt = (e.product_type||'').toLowerCase();
  if (e.is_shirt || ['pajama','socks','apron'].some(x=>pt.includes(x))) return 'shirts';
  if (pt.includes('hat') && !pt.includes('holder') && !pt.includes('organizer')) return 'hats';
  if (['mug','whiskey','glass','tumbler','decanter'].some(x=>pt.includes(x))) return 'drinkware';
  if (['cutting board','charcuterie','grill','serving','platter','burger press'].some(x=>pt.includes(x))) return 'kitchen';
  if (pt.includes('bag')) return 'bags';
  if (['frame','sign','plaque','night light','box','blanket','music box','desk mat','hat holder','organizer'].some(x=>pt.includes(x))) return 'home';
  return 'novelty';
}}

const CATEGORIES = [
  {{ key:'shirts',    label:'Apparel',              labelClass:'shirts' }},
  {{ key:'hats',      label:'Hats',                 labelClass:'' }},
  {{ key:'drinkware', label:'Drinkware',             labelClass:'' }},
  {{ key:'kitchen',   label:'Kitchen & BBQ',         labelClass:'' }},
  {{ key:'home',      label:'Home & Decor',           labelClass:'' }},
  {{ key:'bags',      label:'Bags & Leather',         labelClass:'' }},
  {{ key:'novelty',   label:'Novelty & Accessories',  labelClass:'' }},
];

function getBg(item) {{
  if (item.is_shirt) return 'bg-shirt';
  const t = (item.product_type||'').toLowerCase();
  if (t.includes('hat')||t.includes('cap')) return 'bg-hat';
  if (t.includes('mug')||t.includes('tumbler')) return 'bg-mug';
  if (t.includes('glass')||t.includes('decanter')) return 'bg-glass';
  if (t.includes('board')||t.includes('tray')||t.includes('platter')) return 'bg-board';
  if (t.includes('sign')||t.includes('plaque')||t.includes('frame')) return 'bg-sign';
  if (t.includes('bracelet')||t.includes('jewelry')||t.includes('bag')||t.includes('kit')) return 'bg-jewelry';
  return 'bg-other';
}}

function printTag(m) {{
  if (!m||m==='unknown') return '';
  if (m==='DTG') return '<span class="tag tag-dtg">DTG</span>';
  if (m==='HTV') return '<span class="tag tag-htv">HTV</span>';
  if (m==='embroidery') return '<span class="tag tag-embroidery">Embroidery</span>';
  if (m==='sublimation') return '<span class="tag tag-sublimation">Sublimation</span>';
  return `<span class="tag tag-type">${{m}}</span>`;
}}

function parsePrice(p) {{ return parseFloat((p||'0').replace(/[^0-9.]/g,''))||0; }}

function card(item) {{
  const shirt = item.is_shirt;
  const revBadge = item.reviews > 0
    ? `<div class="reviews-badge"><span class="star">★</span> ${{item.reviews.toLocaleString()}}</div>` : '';
  const shirtBadge = shirt ? `<div class="shirt-badge">Shirt</div>` : '';
  const revLine = item.reviews > 0
    ? `<span class="reviews-text"><strong>${{item.reviews.toLocaleString()}}</strong> reviews · ★ ${{item.rating}}</span>`
    : `<span class="reviews-text" style="color:var(--text-muted)">No reviews yet · ★ ${{item.rating}}</span>`;
  const phrases = (item.key_phrases||[]).map(p=>`<span class="phrase">${{p}}</span>`).join('');
  const demandHtml = (item.demand_signals||[]).length > 0
    ? (item.demand_signals||[]).map(s=>`<span class="demand-signal">🔥 ${{s}}</span>`).join(' ')
    : '';
  const imgInner = item.image_url
    ? `<img src="${{item.image_url}}" alt="" loading="lazy">`
    : `<div class="card-img-label">${{item.product_type}}</div>`;
  return `
<div class="card${{shirt?' is-shirt':''}}">
  <div class="card-img ${{getBg(item)}}">
    ${{shirtBadge}}${{revBadge}}
    ${{imgInner}}
  </div>
  <div class="card-body">
    <div class="card-title">${{item.title}}</div>
    <div class="card-price-row">
      <span class="price">${{item.price}}</span>
      ${{revLine}}
    </div>
    <div class="tags">
      ${{shirt?'<span class="tag tag-shirt">👕 Apparel</span>':''}}
      <span class="tag tag-type">${{item.product_type}}</span>
      ${{printTag(item.print_method)}}
      ${{item.blank?`<span class="tag tag-type">${{item.blank}}</span>`:''}}
    </div>
    <div class="design-style">${{item.design_style}}</div>
    ${{phrases?`<div class="key-phrases">${{phrases}}</div>`:''}}
    ${{demandHtml?`<div>${{demandHtml}}</div>`:''}}
    <div class="shop-row">
      <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="7" width="12" height="8" rx="1"/><path d="M5 7V5a3 3 0 116 0v2"/></svg>
      ${{item.shop_name||'—'}}
    </div>
  </div>
  ${{item.notes?`<div class="notes-row">${{item.notes}}</div>`:''}}
  <div class="card-footer">
    <a class="open-btn" href="${{item.url}}" target="_blank">Open on Etsy ↗</a>
  </div>
</div>`;
}}

function render() {{
  let items = [...DATA];
  if (sort==='reviews') items.sort((a,b)=>b.reviews-a.reviews);
  else if (sort==='price-asc') items.sort((a,b)=>parsePrice(a.price)-parsePrice(b.price));
  else if (sort==='price-desc') items.sort((a,b)=>parsePrice(b.price)-parsePrice(a.price));
  else if (sort==='rating') items.sort((a,b)=>(b.rating||0)-(a.rating||0));

  document.getElementById('cnt-all').textContent=`(${{DATA.length}})`;
  CATEGORIES.forEach(cat => {{
    const el = document.getElementById(`cnt-${{cat.key}}`);
    if (el) el.textContent=`(${{DATA.filter(i=>getCategory(i)===cat.key).length}})`;
  }});

  let visible = 0, html = '';

  if (filter === 'all') {{
    CATEGORIES.forEach(cat => {{
      const group = items.filter(i=>getCategory(i)===cat.key);
      if (!group.length) return;
      html += `<div class="section-header">
        <span class="section-header-label ${{cat.labelClass}}">${{cat.label}}</span>
        <div class="section-header-line ${{cat.labelClass}}"></div>
        <span class="section-header-count">${{group.length}} listings</span>
      </div>`;
      group.forEach(i=>{{ html+=card(i); visible++; }});
    }});
  }} else {{
    const group = items.filter(i=>getCategory(i)===filter);
    const cat = CATEGORIES.find(c=>c.key===filter);
    if (group.length) {{
      html += `<div class="section-header">
        <span class="section-header-label ${{cat?.labelClass||''}}">${{cat?.label||filter}}</span>
        <div class="section-header-line ${{cat?.labelClass||''}}"></div>
        <span class="section-header-count">${{group.length}} listings</span>
      </div>`;
      group.forEach(i=>{{ html+=card(i); visible++; }});
    }}
  }}

  document.getElementById('visible-count').textContent = `Showing ${{visible}} listings`;
  document.getElementById('grid').innerHTML = html || '<div style="grid-column:1/-1;text-align:center;padding:60px;color:var(--text-muted)">No results</div>';
}}

function setFilter(f, btn) {{
  filter = f;
  document.querySelectorAll('.filter-btn').forEach(b=>b.className='filter-btn');
  btn.className = `filter-btn active-${{f}}`;
  render();
}}

function setSort(v) {{ sort=v; render(); }}

render();
</script>
</body>
</html>""".replace('{data_json}', data_json)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--niche', required=True, help='Niche folder name, e.g. personalized-gift-for-dad')
    args = parser.parse_args()

    json_path = BASE_DIR / 'projects' / args.niche / '01-research' / 'competitors.json'
    out_path  = BASE_DIR / 'projects' / args.niche / '01-research' / 'competitor-report.html'

    if not json_path.exists():
        print(f"✗ Not found: {json_path}")
        return

    data = json.load(open(json_path))
    date_str = datetime.date.today().isoformat()
    html = build_html(args.niche, data, date_str)
    out_path.write_text(html)

    shirt_count = sum(1 for e in data if e.get('is_shirt'))
    print(f"✓ Generated {out_path}")
    print(f"  {len(data)} listings · {shirt_count} shirts · {date_str}")


if __name__ == '__main__':
    main()
