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


def classify_demand(top_ems, trend):
    """Derive demand signal level and trend adjustment note."""
    if top_ems >= 100:
        level = 'High'
    elif top_ems >= 30:
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
    """High barrier if majority of listings have RPM > 10."""
    shirts = [e for e in entries if e.get('is_shirt')]
    if not shirts:
        shirts = entries
    high_velocity = sum(1 for e in shirts if (e.get('reviews_per_month') or 0) > 10)
    pct = high_velocity / len(shirts) * 100 if shirts else 0
    level = 'High' if pct >= 50 else ('Medium' if pct >= 25 else 'Low')
    return level, high_velocity, len(shirts), round(pct, 1)


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
        price = e.get('price_min')
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


def compute_fpr_stats(entries):
    """
    For is_shirt=True entries with favorites_per_review > 0:
    Return top 5, median FPR, count.
    """
    shirts = [e for e in entries if e.get('is_shirt')]
    fpr_entries = [
        (e.get('id'), (e.get('title') or '')[:50], e.get('favorites_per_review'))
        for e in shirts
        if e.get('favorites_per_review') and e.get('favorites_per_review') > 0
    ]
    fpr_sorted = sorted(fpr_entries, key=lambda x: -x[2])
    fpr_values = [x[2] for x in fpr_sorted]
    return {
        'top5': fpr_sorted[:5],
        'median': round(statistics.median(fpr_values), 2) if fpr_values else None,
        'count': len(fpr_values),
    }


def compute_rpm_percentiles(entries):
    """
    For is_shirt=True entries with reviews_per_month not null.
    Compute p25, p50, p75, p90 and bucket counts.
    """
    shirts = [e for e in entries if e.get('is_shirt')]
    rpm_values = sorted(
        e.get('reviews_per_month')
        for e in shirts
        if e.get('reviews_per_month') is not None
    )
    n = len(rpm_values)
    if n < 4:
        return {'count': n, 'error': 'Too few data points for percentiles'}

    p25 = round(statistics.quantiles(rpm_values, n=4)[0], 2)
    p50 = round(statistics.median(rpm_values), 2)
    p75 = round(statistics.quantiles(rpm_values, n=4)[2], 2)
    p90 = round(statistics.quantiles(rpm_values, n=10)[8], 2)

    return {
        'count': n,
        'p25': p25,
        'p50': p50,
        'p75': p75,
        'p90': p90,
        'rpm_gt_20': sum(1 for r in rpm_values if r > 20),
        'rpm_gt_10': sum(1 for r in rpm_values if r > 10),
        'rpm_gt_2': sum(1 for r in rpm_values if r > 2),
        'rpm_lt_2': sum(1 for r in rpm_values if r < 2),
    }


def compute_top_n_reference(entries, n=10):
    """Top N listings by EMS — structured reference for AI writing design patterns."""
    sorted_entries = sorted(entries, key=lambda e: e.get('estimated_monthly_sales') or 0, reverse=True)
    result = []
    for rank, e in enumerate(sorted_entries[:n], 1):
        result.append({
            'rank': rank,
            'id': e.get('id'),
            'title': e.get('title') or '',
            'ems': e.get('estimated_monthly_sales') or 0,
            'blank': norm_blank(e.get('blank')),
            'print_method': e.get('print_method') or 'unknown',
            'confirmed': e.get('print_method_confirmed', False),
            'price_min': e.get('price_min'),
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

    # Sort by EMS descending
    sorted_entries = sorted(entries, key=lambda e: e.get('estimated_monthly_sales') or 0, reverse=True)
    top5 = sorted_entries[:5]

    top_ems = top5[0].get('estimated_monthly_sales') or 0 if top5 else 0
    demand_level, trend_note = classify_demand(top_ems, trend)
    comp_level, high_vel_count, shirt_n, high_vel_pct = classify_competition(entries)

    # 15/month check
    top5_ems_values = [(e.get('id', '?'), e.get('title', '')[:50], e.get('estimated_monthly_sales') or 0) for e in top5]
    top5_pass = sum(1 for _, _, ems in top5_ems_values if ems >= 15)
    fifteen_check = 'Pass' if top5_pass >= 3 else 'Fail'

    # Demand signals
    bestseller_count = sum(1 for e in entries if e.get('is_bestseller'))
    in_carts_count = sum(1 for e in entries if (e.get('in_carts') or 0) > 0)
    high_demand_count = sum(1 for e in entries if any('high demand' in s.lower() for s in (e.get('demand_signals') or [])))

    # RPM stats
    all_rpm = [e.get('reviews_per_month') or 0 for e in entries]
    legacy_count = sum(1 for r in all_rpm if r < 2)
    high_rpm_count = sum(1 for r in all_rpm if r > 20)

    # Recommendation
    if demand_level == 'High' and fifteen_check == 'Pass':
        if comp_level == 'High':
            recommendation = 'Enter with sub-niche pivot'
        else:
            recommendation = 'Enter'
    elif demand_level == 'Medium' and fifteen_check == 'Pass':
        recommendation = 'Enter'
    elif demand_level == 'Low' or fifteen_check == 'Fail':
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
    lines.append(f'Basis: Top listing EMS={top_ems}. Bestseller badges: {bestseller_count}/{total}. '
                 f'In-carts signals: {in_carts_count}. In-high-demand signals: {high_demand_count}. '
                 f'Trend: {trend}. '
                 f'[FILL IN: one-sentence summary of what this means for entry viability]')
    lines.append('')
    lines.append(f'**Competition barrier:** {comp_level}')
    lines.append(f'Basis: {high_vel_count}/{shirt_n} shirt listings ({high_vel_pct}%) have RPM > 10 '
                 f'(majority threshold = 50%). {legacy_count}/{total} listings are legacy (RPM < 2). '
                 f'[FILL IN: one-sentence judgment on barrier to entry]')
    lines.append('')
    lines.append(f'**15/month check:** {fifteen_check}')
    lines.append('Basis: Top 5 listings by estimated monthly sales:')
    for i, (lid, title, ems) in enumerate(top5_ems_values, 1):
        flag = ' ✓' if ems >= 15 else ' ✗'
        lines.append(f'  {i}. ID {lid} — "{title}..." — EMS {ems}{flag}')
    lines.append(f'  {top5_pass}/5 meet the 15/month threshold → {fifteen_check}')
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
    lines.append(f'_High-velocity listings (RPM > 20): {high_rpm_count}. Legacy listings (RPM < 2): {legacy_count}._')

    print('\n'.join(lines))
    print()
    print('─' * 60)
    print('Paste the block above at the TOP of market-insights.md.')
    print('Fill in the [FILL IN] placeholders, then remove this line.')

    # ── Top 10 Reference ─────────────────────────────────────────────────────
    print(section_header('Top 10 Reference', 'use when writing Section 1 (Design Patterns) — ensure every listing here appears under a pattern'))
    top10 = compute_top_n_reference(entries, n=10)
    print(f'{"#":<4} {"ID":<14} {"EMS":>6}  {"Blank":<20} {"Print":<12} {"Confirmed":<10} {"Price Min":>10}')
    print('-' * 80)
    for r in top10:
        conf = 'yes' if r['confirmed'] else 'inferred'
        price = f"${r['price_min']:.2f}" if r['price_min'] else 'N/A'
        print(f"{r['rank']:<4} {str(r['id']):<14} {r['ems']:>6}  {r['blank']:<20} {r['print_method']:<12} {conf:<10} {price:>10}")
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

    # ── FPR Stats ─────────────────────────────────────────────────────────────
    print(section_header('FPR Stats', 'paste into market-insights.md Section 5 / Section 8'))
    fpr = compute_fpr_stats(entries)
    print(f'Shirt listings with FPR > 0: {fpr["count"]}')
    print(f'Median FPR: {fpr["median"]}')
    print()
    print('Top 5 by favorites_per_review:')
    print()
    print('| Rank | ID | Title (truncated) | FPR |')
    print('|---|---|---|---|')
    for i, (lid, title, fpr_val) in enumerate(fpr['top5'], 1):
        print(f'| {i} | {lid} | {title} | {fpr_val} |')
    print()
    print('[FILL IN: one sentence on what the top FPR listings have in common]')

    # ── RPM Percentiles ───────────────────────────────────────────────────────
    print(section_header('RPM Percentiles', 'paste into market-insights.md Section 6 / Appendix'))
    rpm = compute_rpm_percentiles(entries)
    if 'error' in rpm:
        print(f'ERROR: {rpm["error"]}')
    else:
        print(f'Shirt listings with RPM data: {rpm["count"]}')
        print()
        print('| Percentile | RPM value |')
        print('|---|---|')
        print(f'| p25 | {rpm["p25"]} |')
        print(f'| p50 (median) | {rpm["p50"]} |')
        print(f'| p75 | {rpm["p75"]} |')
        print(f'| p90 | {rpm["p90"]} |')
        print()
        print('| Bucket | Count |')
        print('|---|---|')
        print(f'| RPM > 20 (high velocity) | {rpm["rpm_gt_20"]} |')
        print(f'| RPM > 10 | {rpm["rpm_gt_10"]} |')
        print(f'| RPM > 2 | {rpm["rpm_gt_2"]} |')
        print(f'| RPM < 2 (legacy) | {rpm["rpm_lt_2"]} |')
        print()
        print('[FILL IN: one sentence on what RPM distribution means for competitive intensity]')


if __name__ == '__main__':
    main()
