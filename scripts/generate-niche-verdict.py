#!/usr/bin/env python3
"""
generate-niche-verdict.py

Reads competitors.json and keywords.md, computes all the verdict math,
and outputs a pre-filled Niche Verdict block ready to paste at the top of
market-insights.md.

Also computes all deterministic numbers for Sections 2–6 of market-insights.md
and prints them as labeled blocks so the user knows exactly where to paste each.

All numbers are calculated from real data — the only thing left for the AI
to fill in is the one-sentence reasoning text for each field.

Usage:
  python3 scripts/generate-niche-verdict.py --niche dog-mom
  python3 scripts/generate-niche-verdict.py --niche personalized-gift-for-dad
"""

import argparse, json, re, sys, statistics
from pathlib import Path
from datetime import date
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent


def load_competitors(niche):
    path = BASE_DIR / 'projects' / niche / '01-research' / 'competitors.json'
    if not path.exists():
        print(f'✗ competitors.json not found at {path}')
        sys.exit(1)
    return json.loads(path.read_text())


def load_keywords_trend(niche):
    """Return the trend string from keywords.md if present, else 'Unknown'."""
    path = BASE_DIR / 'projects' / niche / '01-research' / 'keywords.md'
    if not path.exists():
        return 'Unknown (keywords.md not found)'
    text = path.read_text()
    # Look for a Trend column value in the table — grab the first non-header cell
    matches = re.findall(r'\|\s*(Rising|Stable|Declining|Seasonal[^|]*|Unknown[^|]*)\s*\|', text, re.IGNORECASE)
    if matches:
        return matches[0].strip()
    return 'Unknown (no trend column found in keywords.md)'


def classify_demand(top_reviews, trend):
    """Derive demand signal level and trend adjustment note based on total review count of top listing."""
    if top_reviews >= 500:
        level = 'High'
    elif top_reviews >= 100:
        level = 'Medium'
    else:
        level = 'Low'

    t = trend.lower()
    note = ''
    if 'rising' in t:
        levels = ['Low', 'Medium', 'High']
        idx = levels.index(level)
        if idx < 2:
            level = levels[idx + 1]
        note = ' (upgraded one level: trend is Rising)'
    elif 'declining' in t:
        levels = ['Low', 'Medium', 'High']
        idx = levels.index(level)
        if idx > 0:
            level = levels[idx - 1]
        note = ' (downgraded one level: trend is Declining)'
    elif 'seasonal' in t:
        note = f' (seasonal — check peak month in keywords.md)'
    elif 'unknown' in t:
        note = ' (trend unknown — left unadjusted; fill in after eRank Phase 1.4)'

    return level, note


def classify_competition(entries):
    """High barrier if majority of listings have reviews > 100."""
    shirts = [e for e in entries if e.get('is_shirt')]
    if not shirts:
        shirts = entries
    high_reviews = sum(1 for e in shirts if (e.get('reviews') or 0) > 100)
    pct = high_reviews / len(shirts) * 100 if shirts else 0
    level = 'High' if pct >= 50 else ('Medium' if pct >= 25 else 'Low')
    return level, high_reviews, len(shirts), round(pct, 1)


# ──────────────────────────────────────────────────────────────────────────────
# Normalisation helpers
# ──────────────────────────────────────────────────────────────────────────────

def norm_blank(b):
    """Normalise blank name to a canonical group label."""
    if b is None:
        return '(null)'
    b = b.lower().strip()
    if b.startswith('comfort colors') or b in ('cc',):
        return 'Comfort Colors'
    if b.startswith('bella canvas') or b.startswith('bella+canvas'):
        return 'Bella Canvas'
    if b.startswith('gildan 5000') or b == 'gildan' or b == 'gildan heavy cotton':
        return 'Gildan 5000'
    if b.startswith('gildan 64000'):
        return 'Gildan 64000'
    return b.title()


def norm_product_type(pt):
    """Normalise product_type to a canonical label."""
    if pt is None:
        return 'Unknown'
    pt = pt.lower().strip()
    if pt in ('t-shirt', 'tshirt', 'shirt'):
        return 'T-Shirt'
    if pt in ('sweatshirt', 'crewneck', 'crew neck'):
        return 'Sweatshirt'
    return pt.title()


# ──────────────────────────────────────────────────────────────────────────────
# Calculation functions
# ──────────────────────────────────────────────────────────────────────────────

def compute_price_table(entries):
    """
    Group is_shirt=True entries by (product_type_norm, blank_norm, print_method).
    Return rows with n≥2, sorted by product_type then blank.
    """
    shirts = [e for e in entries if e.get('is_shirt')]
    groups = defaultdict(list)
    for e in shirts:
        nb = norm_blank(e.get('blank'))
        npt = norm_product_type(e.get('product_type'))
        pm = (e.get('print_method') or 'unknown').lower()
        price = e.get('price_real_min')
        if price is not None:
            groups[(npt, nb, pm)].append(price)

    rows = []
    for (pt, blank, pm), prices in groups.items():
        if len(prices) >= 2:
            rows.append({
                'product_type': pt,
                'blank': blank,
                'print_method': pm,
                'n': len(prices),
                'min': round(min(prices), 2),
                'median': round(statistics.median(prices), 2),
                'max': round(max(prices), 2),
            })

    rows.sort(key=lambda r: (r['product_type'], r['blank'], r['print_method']))
    return rows


def compute_print_method_breakdown(entries):
    """
    Count all entries by print_method; for each, count confirmed vs inferred.
    Returns sorted list of dicts.
    """
    counts = defaultdict(lambda: {'total': 0, 'confirmed': 0, 'inferred': 0})
    for e in entries:
        pm = (e.get('print_method') or 'unknown').lower()
        counts[pm]['total'] += 1
        if e.get('print_method_confirmed'):
            counts[pm]['confirmed'] += 1
        else:
            counts[pm]['inferred'] += 1

    rows = [{'method': pm, **v} for pm, v in counts.items()]
    rows.sort(key=lambda r: -r['total'])
    return rows


def compute_blank_distribution(entries):
    """
    Count is_shirt=True entries by normalised blank.
    Returns sorted list (desc by count).
    """
    shirts = [e for e in entries if e.get('is_shirt')]
    counts = defaultdict(int)
    for e in shirts:
        counts[norm_blank(e.get('blank'))] += 1

    rows = [{'blank': b, 'count': c} for b, c in counts.items()]
    rows.sort(key=lambda r: -r['count'])
    return rows


def compute_personalization_breakdown(entries):
    """
    Break down personalization fields across all entries.
    Returns:
      - total_personalized: int
      - total_not_personalized: int
      - not_personalized_examples: list of {id, title}
      - type_counts: list of {type, count} sorted desc (null → 'Not personalized')
      - photo_required: int (personalization_type contains 'photo')
      - name_only: int (personalization=True but no 'photo' in type)
    """
    total = len(entries)
    personalized = [e for e in entries if e.get('personalization')]
    not_personalized = [e for e in entries if not e.get('personalization')]

    from collections import Counter
    type_counter = Counter()
    for e in entries:
        pt = e.get('personalization_type') if e.get('personalization') else None
        type_counter[pt] += 1

    type_counts = [
        {'type': t if t is not None else '(none — not personalized)', 'count': c}
        for t, c in type_counter.most_common()
    ]

    photo_required = sum(
        1 for e in personalized
        if e.get('personalization_type') and 'photo' in e.get('personalization_type', '').lower()
    )
    name_only = sum(
        1 for e in personalized
        if e.get('personalization_type') and 'photo' not in e.get('personalization_type', '').lower()
    )

    return {
        'total': total,
        'total_personalized': len(personalized),
        'total_not_personalized': len(not_personalized),
        'not_personalized_examples': [
            {'id': e.get('id'), 'title': (e.get('title') or '')[:70]}
            for e in not_personalized
        ],
        'type_counts': type_counts,
        'photo_required': photo_required,
        'name_only': name_only,
    }


def compute_fpr_stats(entries):
    """
    For is_shirt=True entries with favorites_per_review > 0:
    Return top 5 with full context, median FPR, count.
    Confidence: High = reviews >= 20, Medium = 5-19, Low = < 5 (FPR is volatile at low counts).
    """
    shirts = [e for e in entries if e.get('is_shirt')]
    fpr_entries = []
    for e in shirts:
        fpr = e.get('favorites_per_review')
        if not fpr or fpr <= 0:
            continue
        reviews = e.get('reviews') or 0
        if reviews >= 20:
            confidence = ('✅ High', 'reviews ≥ 20')
        elif reviews >= 5:
            confidence = ('⚠️ Medium', 'reviews 5–19')
        else:
            confidence = ('❌ Low', 'reviews < 5 — FPR is volatile')
        fpr_entries.append({
            'id':            e.get('id'),
            'title':         (e.get('title') or '')[:52],
            'fpr':           fpr,
            'reviews':       reviews,
            'favorites':     e.get('favorites_count') or 0,
            'is_bestseller': e.get('is_bestseller', False),
            'in_carts':      e.get('in_carts'),
            'shop_sales':    e.get('shop_sales') or 0,
            'shop_years':    e.get('shop_years_on_etsy'),
            'confidence':    confidence[0],
            'conf_reason':   confidence[1],
        })
    fpr_sorted = sorted(fpr_entries, key=lambda x: -x['fpr'])
    fpr_values = [x['fpr'] for x in fpr_sorted]
    return {
        'top5':   fpr_sorted[:5],
        'median': round(statistics.median(fpr_values), 2) if fpr_values else None,
        'count':  len(fpr_values),
    }


def compute_reviews_percentiles(entries):
    """
    For is_shirt=True entries with reviews not null.
    Compute p25, p50, p75, p90 and bucket counts.
    """
    shirts = [e for e in entries if e.get('is_shirt')]
    reviews_values = sorted(
        e.get('reviews')
        for e in shirts
        if e.get('reviews') is not None
    )
    n = len(reviews_values)
    if n < 4:
        return {'count': n, 'error': 'Too few data points for percentiles'}

    p25 = round(statistics.quantiles(reviews_values, n=4)[0], 2)
    p50 = round(statistics.median(reviews_values), 2)
    p75 = round(statistics.quantiles(reviews_values, n=4)[2], 2)
    p90 = round(statistics.quantiles(reviews_values, n=10)[8], 2)

    return {
        'count': n,
        'p25': p25,
        'p50': p50,
        'p75': p75,
        'p90': p90,
        'reviews_gt_500': sum(1 for r in reviews_values if r > 500),
        'reviews_gt_100': sum(1 for r in reviews_values if r > 100),
        'reviews_gt_20': sum(1 for r in reviews_values if r > 20),
        'reviews_lt_20': sum(1 for r in reviews_values if r < 20),
    }


# ── Comfort Colors hex lookup ─────────────────────────────────────────────────
# Tier 1 (CONFIRMED): scraped from retail.comfortcolors.com inline swatch CSS.
# Tier 2 (APPROX): cross-referenced from POD community references; flagged below.
# To update a Tier 2 entry: replace the hex and remove the # APPROX comment.
# Source: retail.comfortcolors.com/en-us/comfort-colors-1717 (2026-06-11)
CC_HEX = {
    # Tier 1 — confirmed from official site
    'White':          '#FFFFFF',
    'Black':          '#25282A',
    'True Navy':      '#041E42',
    'Crimson':        '#A4123F',
    'Berry':          '#7E4966',
    'Watermelon':     '#F4364C',
    'Crunchberry':    '#EF4A81',
    'Flo Blue':       '#5576D1',
    'Violet':         '#7474C1',
    'Lagoon Blue':    '#05C3DE',
    'Chambray':       '#BDD6E6',
    'Ice Blue':       '#5B7F95',
    'Denim':          '#425563',
    'Granite':        '#7C878E',
    'Grey':           '#716E6A',
    'Seafoam':        '#487A7B',
    'Chalky Mint':    '#5CB8B2',
    'Island Reef':    '#8FE2B0',
    'Light Green':    '#5C7F71',
    'Blue Spruce':    '#3E5D58',
    'Butter':         '#F5E1A4',
    'Bright Salmon':  '#FF6D6A',
    'Neon Red Orange':'#FF585D',
    'Pepper':         '#4E4B48',
    # Tier 2 — approximated; update when confirmed hex is available
    'Ivory':          '#F4F0E0',  # APPROX
    'Blossom':        '#E8B4C8',  # APPROX
    'Blue Jean':      '#6B8DB2',  # APPROX
    'Moss':           '#6B7A3C',  # APPROX
    'Espresso':       '#2C1A0E',  # APPROX
    'Yam':            '#C4623A',  # APPROX
    'Orchid':         '#C597C5',  # APPROX
    'Bay':            '#6B8FA3',  # APPROX
    'Sage':           '#8FAF8F',  # APPROX
    'Mustard':        '#C9A84C',  # APPROX
    'Red':            '#B22222',  # APPROX
    'Brick':          '#8B3A3A',  # APPROX
    'Terracotta':     '#C06040',  # APPROX
    'Banana':         '#FAE87C',  # APPROX
    'Melon':          '#F4A47A',  # APPROX
    'Sandstone':      '#C8B89A',  # APPROX
    'Hemp':           '#A89070',  # APPROX
    'Khaki':          '#C8B878',  # APPROX
    'Peach':          '#FFCBA4',  # APPROX
    'Neon Pink':      '#FF69B4',  # APPROX
    'Sapphire':       '#2D5FA8',  # APPROX
}

# DTG threshold: 0.35 (higher than WCAG 0.179 — DTG fabric needs white ink
# on mid-tones that web accessibility considers "light enough for dark text")
_DTG_THRESHOLD = 0.35


def _luminance(hex_str):
    """W3C relative luminance from a hex color string. Returns 0.0–1.0."""
    h = hex_str.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _classify_color(name):
    """Returns ('light'|'dark'|'unknown', luminance|None, tier)."""
    key = name.strip().title()
    # Try exact match, then case-insensitive
    hex_val = CC_HEX.get(key) or CC_HEX.get(name.strip())
    if not hex_val:
        for k, v in CC_HEX.items():
            if k.lower() == name.strip().lower():
                hex_val = v
                key = k
                break
    if not hex_val:
        return ('unknown', None, None)
    lum = _luminance(hex_val)
    shade = 'light' if lum > _DTG_THRESHOLD else 'dark'
    tier = 'approx' if '# APPROX' in f'{key}' or any(
        k.lower() == key.lower() and 'APPROX' in f'{CC_HEX[k]}'
        for k in CC_HEX
    ) else 'confirmed'
    # Re-check tier from dict comment (stored as suffix in value — not possible,
    # so check against known Tier 1 keys instead)
    tier1 = {k.lower() for k in [
        'White','Black','True Navy','Crimson','Berry','Watermelon','Crunchberry',
        'Flo Blue','Violet','Lagoon Blue','Chambray','Ice Blue','Denim','Granite',
        'Grey','Seafoam','Chalky Mint','Island Reef','Light Green','Blue Spruce',
        'Butter','Bright Salmon','Neon Red Orange','Pepper',
    ]}
    tier = 'confirmed' if key.lower() in tier1 else 'approx'
    return (shade, round(lum, 3), tier)


def compute_color_strategy(entries):
    """
    Compute all color strategy data deterministically from competitors.json.
    Returns:
      - top5_by_reviews: top 5 shirt listings by reviews, with blank + color count
      - cc_count: number of CC shirt listings
      - cc_color_freq: list of (color, count, pct, shade, tier) sorted by freq, top 20
      - cc_light / cc_dark / cc_unknown: colors split by DTG ink classification
      - bc_listings: confirmed BC shirt listings with id, color_count, price_real_min
      - bc_price_min / bc_price_max: actual price range across BC listings
    """
    from collections import Counter

    shirts = [e for e in entries if e.get('is_shirt')]
    top5 = sorted(shirts, key=lambda e: e.get('reviews') or 0, reverse=True)[:5]

    cc = [e for e in shirts if norm_blank(e.get('blank')) == 'Comfort Colors']
    all_cc_colors = []
    for e in cc:
        all_cc_colors.extend(e.get('colors') or [])
    cc_n = len(cc)

    cc_freq = []
    for color, count in Counter(all_cc_colors).most_common(20):
        shade, lum, tier = _classify_color(color)
        pct = round(count / cc_n * 100) if cc_n else 0
        cc_freq.append((color, count, pct, shade, lum, tier))

    cc_light   = [(c, cnt, pct, lum, tier) for c, cnt, pct, shade, lum, tier in cc_freq if shade == 'light']
    cc_dark    = [(c, cnt, pct, lum, tier) for c, cnt, pct, shade, lum, tier in cc_freq if shade == 'dark']
    cc_unknown = [(c, cnt, pct, lum, tier) for c, cnt, pct, shade, lum, tier in cc_freq if shade == 'unknown']

    bc = [e for e in shirts if norm_blank(e.get('blank')) == 'Bella Canvas']
    bc_prices = [e.get('price_real_min') for e in bc if e.get('price_real_min')]

    return {
        'top5': [
            {
                'id': e.get('id'),
                'reviews': e.get('reviews') or 0,
                'blank': norm_blank(e.get('blank')),
                'color_count': len(e.get('colors') or []),
            }
            for e in top5
        ],
        'cc_count': cc_n,
        'cc_freq': cc_freq,
        'cc_light': cc_light,
        'cc_dark': cc_dark,
        'cc_unknown': cc_unknown,
        'bc_listings': sorted(
            [
                {
                    'id': e.get('id'),
                    'color_count': len(e.get('colors') or []),
                    'price_real_min': e.get('price_real_min'),
                }
                for e in bc
            ],
            key=lambda x: -(x.get('price_real_min') or 0),
        ),
        'bc_price_min': round(min(bc_prices), 2) if bc_prices else None,
        'bc_price_max': round(max(bc_prices), 2) if bc_prices else None,
    }


def compute_top_n_reference(entries, n=10):
    """Top N listings by reviews — structured reference for AI writing design patterns."""
    sorted_entries = sorted(entries, key=lambda e: e.get('reviews') or 0, reverse=True)
    result = []
    for rank, e in enumerate(sorted_entries[:n], 1):
        result.append({
            'rank': rank,
            'id': e.get('id'),
            'title': e.get('title') or '',
            'reviews': e.get('reviews') or 0,
            'blank': norm_blank(e.get('blank')),
            'print_method': e.get('print_method') or 'unknown',
            'confirmed': e.get('print_method_confirmed', False),
            'price_real_min': e.get('price_real_min'),
        })
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Formatting helpers
# ──────────────────────────────────────────────────────────────────────────────

SEP = '═' * 60


def section_header(title, destination):
    return f'\n{SEP}\nSECTION: {title}  →  {destination}\n{SEP}\n'


# ──────────────────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Generate pre-filled market-insights blocks from competitors.json')
    parser.add_argument('--niche', required=True, help='Niche slug, e.g. dog-mom')
    args = parser.parse_args()

    niche = args.niche.strip().lower()
    entries = load_competitors(niche)
    trend = load_keywords_trend(niche)

    shirts = [e for e in entries if e.get('is_shirt')]
    total = len(entries)
    shirt_count = len(shirts)

    # Sort by reviews descending
    sorted_entries = sorted(entries, key=lambda e: e.get('reviews') or 0, reverse=True)
    top5 = sorted_entries[:5]

    top_reviews = top5[0].get('reviews') or 0 if top5 else 0
    demand_level, trend_note = classify_demand(top_reviews, trend)
    comp_level, high_reviews_count, shirt_n, high_reviews_pct = classify_competition(entries)

    # Proof of demand check
    top5_reviews_values = [(e.get('id', '?'), e.get('title', '')[:50], e.get('reviews') or 0) for e in top5]
    top5_pass = sum(1 for _, _, reviews in top5_reviews_values if reviews >= 20)
    reviews_check = 'Pass' if top5_pass >= 3 else 'Fail'

    # Demand signals
    bestseller_count = sum(1 for e in entries if e.get('is_bestseller'))
    in_carts_count = sum(1 for e in entries if (e.get('in_carts') or 0) > 0)
    high_demand_count = sum(1 for e in entries if any('high demand' in s.lower() for s in (e.get('demand_signals') or [])))

    # Recommendation
    if demand_level == 'High' and reviews_check == 'Pass':
        if comp_level == 'High':
            recommendation = 'Enter with sub-niche pivot'
        else:
            recommendation = 'Enter'
    elif demand_level == 'Medium' and reviews_check == 'Pass':
        recommendation = 'Enter'
    elif demand_level == 'Low' or reviews_check == 'Fail':
        recommendation = 'Do not enter'
    else:
        recommendation = 'Enter with sub-niche pivot'

    # Confidence
    if trend.lower().startswith('unknown'):
        confidence = 'Medium — trend unknown; complete Phase 1.4 eRank to raise to High'
    else:
        confidence = 'High — verdict backed by scraped data + trend direction'

    # ── Niche Verdict block ───────────────────────────────────────────────────
    lines = []
    lines.append('## Niche Verdict [REQUIRED]')
    lines.append('')
    lines.append(f'**Demand signal:** {demand_level}{trend_note}')
    lines.append(f'Basis: Top listing reviews={top_reviews}. Bestseller badges: {bestseller_count}/{total}. '
                 f'In-carts signals: {in_carts_count}. In-high-demand signals: {high_demand_count}. '
                 f'Trend: {trend}. '
                 f'[FILL IN: one-sentence summary of what this means for entry viability]')
    lines.append('')
    lines.append(f'**Competition barrier:** {comp_level}')
    lines.append(f'Basis: {high_reviews_count}/{shirt_n} shirt listings ({high_reviews_pct}%) have reviews > 100 '
                 f'(majority threshold = 50%). '
                 f'[FILL IN: one-sentence judgment on barrier to entry]')
    lines.append('')
    lines.append(f'**Proof of demand:** {reviews_check}')
    lines.append('Basis: Top 5 listings by reviews:')
    for i, (lid, title, reviews) in enumerate(top5_reviews_values, 1):
        flag = ' ✓' if reviews >= 20 else ' ✗'
        lines.append(f'  {i}. ID {lid} — "{title}..." — reviews {reviews}{flag}')
    lines.append(f'  {top5_pass}/5 meet the reviews >= 20 threshold → {reviews_check}')
    lines.append('')
    lines.append(f'**Recommendation:** {recommendation}')
    lines.append('[FILL IN: one sentence combining demand + competition + 15-check signals]')
    lines.append('')
    lines.append('**If sub-niche pivot recommended:** [FILL IN: specific angle with fewer dominant competitors]')
    lines.append('')
    lines.append(f'**Confidence:** {confidence}')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append(f'_Generated by generate-niche-verdict.py on {date.today()} from {total} scraped listings ({shirt_count} shirts)._')

    print('\n'.join(lines))
    print()
    print('─' * 60)
    print('Paste the block above at the TOP of market-insights.md.')
    print('Fill in the [FILL IN] placeholders, then remove this line.')

    # ── Top 10 Reference ─────────────────────────────────────────────────────
    print(section_header('Top 10 Reference', 'use when writing Section 1 (Design Patterns) — ensure every listing here appears under a pattern'))
    top10 = compute_top_n_reference(entries, n=10)
    print(f'{"#":<4} {"ID":<14} {"Reviews":>8}  {"Blank":<20} {"Print":<12} {"Confirmed":<10} {"Price Min":>10}')
    print('-' * 80)
    for r in top10:
        conf = 'yes' if r['confirmed'] else 'inferred'
        price = f"${r['price_real_min']:.2f}" if r['price_real_min'] else 'N/A'
        print(f"{r['rank']:<4} {str(r['id']):<14} {r['reviews']:>8}  {r['blank']:<20} {r['print_method']:<12} {conf:<10} {price:>10}")
        print(f"     {r['title'][:90]}")
        print()
    print('[AI instruction: every ID above must appear in a named pattern below. If a listing fits no existing pattern, add a new one.]')

    # ── Price Table ───────────────────────────────────────────────────────────
    print(section_header('Price Table', 'paste into market-insights.md Section 2'))
    price_rows = compute_price_table(entries)
    print('| Product | Blank | Print Method | n | Min | Median | Max |')
    print('|---|---|---|---|---|---|---|')
    for r in price_rows:
        print(f"| {r['product_type']} | {r['blank']} | {r['print_method']} "
              f"| {r['n']} | ${r['min']:.2f} | ${r['median']:.2f} | ${r['max']:.2f} |")
    print()
    print('[FILL IN: one sentence on price positioning opportunity]')

    # ── Print Method Breakdown ────────────────────────────────────────────────
    print(section_header('Print Method Breakdown', 'paste into market-insights.md Section 3 (verify/replace)'))
    pm_rows = compute_print_method_breakdown(entries)
    print('| Print Method | Count | Confirmed | Inferred |')
    print('|---|---|---|---|')
    for r in pm_rows:
        print(f"| {r['method']} | {r['total']} | {r['confirmed']} | {r['inferred']} |")
    total_pm = sum(r['total'] for r in pm_rows)
    total_conf = sum(r['confirmed'] for r in pm_rows)
    total_inf = sum(r['inferred'] for r in pm_rows)
    print(f'| **Total** | **{total_pm}** | **{total_conf}** | **{total_inf}** |')
    print()
    print('[FILL IN: one sentence on what print method dominance means for new entrants]')

    # ── Blank Distribution ────────────────────────────────────────────────────
    print(section_header('Blank Distribution', 'paste into market-insights.md Section 4 (verify/replace)'))
    blank_rows = compute_blank_distribution(entries)
    print(f'Shirts-only (is_shirt=True): {shirt_count} total')
    print()
    print('| Blank (normalised) | Count | % of shirt listings |')
    print('|---|---|---|')
    for r in blank_rows:
        pct = round(r['count'] / shirt_count * 100, 1) if shirt_count else 0
        print(f"| {r['blank']} | {r['count']} | {pct}% |")
    print()
    print('[FILL IN: one sentence on blank dominance and what it means for sourcing]')

    # ── Personalization Breakdown ─────────────────────────────────────────────
    print(section_header('Personalization Breakdown', 'paste into market-insights.md Section 2 (Most Common Personalization Types)'))
    pb = compute_personalization_breakdown(entries)
    print(f'Total listings: {pb["total"]}')
    print(f'Personalized (personalization=True): {pb["total_personalized"]}/{pb["total"]}')
    print(f'Not personalized (personalization=False): {pb["total_not_personalized"]}/{pb["total"]}')
    print()
    print('**Personalization type breakdown** (from personalization_type field in competitors.json):')
    print()
    print('| Personalization Type | Count |')
    print('|---|---|')
    for row in pb['type_counts']:
        print(f"| {row['type']} | {row['count']} |")
    print()
    print(f'Of the {pb["total_personalized"]} personalized listings:')
    print(f'  - Photo required (type contains "photo"): {pb["photo_required"]}')
    print(f'  - Name/breed only (no photo): {pb["name_only"]}')
    print()
    print('Non-personalized listings (no custom input required):')
    for ex in pb['not_personalized_examples']:
        print(f'  - ID {ex["id"]}: {ex["title"]}')
    print()
    print('[FILL IN: one sentence on what personalization tier dominates and what it means for your product strategy]')
    print('[FILL IN: one sentence on whether name-only or photo-required listings have higher reviews in this niche]')

    # ── FPR Stats ─────────────────────────────────────────────────────────────
    print(section_header('FPR Stats', 'replace Section 7 (Listings to Watch) in market-insights.md'))
    fpr = compute_fpr_stats(entries)
    print(f'Shirt listings with FPR > 0: {fpr["count"]}')
    print(f'Median FPR: {fpr["median"]}')
    print()
    print('| Rank | ID | Title (truncated) | FPR | Reviews | Favorites | Bestseller | In-Carts | Shop Sales | Shop Yrs | Confidence |')
    print('|---|---|---|---|---|---|---|---|---|---|---|')
    for i, r in enumerate(fpr['top5'], 1):
        carts = r['in_carts'] if r['in_carts'] is not None else 'null'
        yrs   = f'{r["shop_years"]:.1f}' if r['shop_years'] else '?'
        bs    = '✓' if r['is_bestseller'] else '—'
        print(f'| {i} | {r["id"]} | {r["title"]} | {r["fpr"]} | {r["reviews"]} | {r["favorites"]:,} | {bs} | {carts} | {r["shop_sales"]:,} | {yrs} | {r["confidence"]} |')
    print()
    # Auto-commentary
    low_count  = sum(1 for r in fpr['top5'] if r['confidence'] == '❌ Low')
    accessible = sum(1 for r in fpr['top5'] if r['shop_sales'] < 20_000)
    bs_count   = sum(1 for r in fpr['top5'] if r['is_bestseller'])
    if low_count:
        print(f'⚠️  {low_count} of 5 top-FPR listings have fewer than 5 reviews — FPR is unreliable at this sample size; treat as directional only. `[our data]`')
    print(f'{bs_count}/5 top-FPR listings carry a Bestseller badge despite low review counts. `[our data]` '
          f'{accessible}/5 are from accessible shops (under 20k total sales) — '
          f'{"suggesting this pattern is reachable for a new entrant" if accessible >= 3 else "most are from established shops — harder to replicate quickly"}. `[inferred]`')
    print('[AI instruction: do NOT add titles, IDs, or counts not shown above]')

    # ── Reviews Percentiles ───────────────────────────────────────────────────
    print(section_header('Reviews Percentiles', 'paste into market-insights.md Section 6 / Appendix'))
    rev_pct = compute_reviews_percentiles(entries)
    if 'error' in rev_pct:
        print(f'ERROR: {rev_pct["error"]}')
    else:
        print(f'Shirt listings with reviews data: {rev_pct["count"]}')
        print()
        print('| Percentile | Reviews value |')
        print('|---|---|')
        print(f'| p25 | {rev_pct["p25"]} |')
        print(f'| p50 (median) | {rev_pct["p50"]} |')
        print(f'| p75 | {rev_pct["p75"]} |')
        print(f'| p90 | {rev_pct["p90"]} |')
        print()
        print('| Bucket | Count |')
        print('|---|---|')
        print(f'| reviews > 500 (high social proof) | {rev_pct["reviews_gt_500"]} |')
        print(f'| reviews > 100 | {rev_pct["reviews_gt_100"]} |')
        print(f'| reviews > 20 | {rev_pct["reviews_gt_20"]} |')
        print(f'| reviews < 20 (low proof) | {rev_pct["reviews_lt_20"]} |')
        print()
        print('[FILL IN: one sentence on what reviews distribution means for competitive intensity]')

    # ── Color Strategy ────────────────────────────────────────────────────────
    print(section_header('Color Strategy', 'replace Section 5 (Color Strategy) in market-insights.md'))
    cs = compute_color_strategy(entries)

    print('**Top 5 listings by reviews — blank and color count**')
    print('(Reviews = ranking proxy. No EMS available — listing creation date not scraped.)')
    print()
    print('| Listing ID | Reviews | Blank | Color count |')
    print('|---|---|---|---|')
    for r in cs['top5']:
        print(f"| {r['id']} | {r['reviews']:,} | {r['blank']} | {r['color_count']} |")
    print()

    n = cs['cc_count']
    print(f'**Comfort Colors palette — most common colors across {n} CC shirt listings**')
    print(f'*(Classified by DTG ink rule: luminance > 0.35 = light shirt → use black-ink design; ≤ 0.35 = dark shirt → use white-ink design)*')
    print()

    def _print_cc_subtable(rows, label, ink_note, n):
        if not rows:
            print(f'*No {label.lower()} colors in top 20.*')
            return
        print(f'**{label}** — {ink_note}')
        print()
        print('| Color | Listings | % of CC listings | Luminance | Hex source |')
        print('|---|---|---|---|---|')
        for color, count, pct, lum, tier in rows:
            hex_val = CC_HEX.get(color.strip().title()) or CC_HEX.get(color.strip()) or '—'
            lum_str = f'{lum:.3f}' if lum is not None else '—'
            src = '✓ confirmed' if tier == 'confirmed' else '~ approx'
            print(f'| {color} | {count}/{n} | {pct}% | {lum_str} | {src} |')
        print()

    _print_cc_subtable(cs['cc_light'],   'Light colors (use black-ink design file)',  'luminance > 0.35', n)
    _print_cc_subtable(cs['cc_dark'],    'Dark colors (use white-ink design file)',    'luminance ≤ 0.35', n)
    if cs['cc_unknown']:
        _print_cc_subtable(cs['cc_unknown'], 'Unknown — not in hex lookup',           'add hex to CC_HEX dict', n)

    if cs['bc_listings']:
        print(f'**Bella Canvas listings ({len(cs["bc_listings"])} confirmed):**')
        print()
        print('| Listing ID | Colors | Price min |')
        print('|---|---|---|')
        for r in cs['bc_listings']:
            price = f"${r['price_real_min']:.2f}" if r['price_real_min'] else 'N/A'
            print(f"| {r['id']} | {r['color_count']} | {price} |")
        if cs['bc_price_min'] and cs['bc_price_max']:
            print(f'\nBC price range: ${cs["bc_price_min"]:.2f}–${cs["bc_price_max"]:.2f}')
    else:
        print('No confirmed Bella Canvas listings found.')
    print()
    print('[FILL IN: one sentence on recommended palette — how many light vs dark colors, and which specific colors to prioritize]')
    print('[AI instruction: do NOT add colors, IDs, or price ranges not shown above — all numbers come from this block]')


if __name__ == '__main__':
    main()
