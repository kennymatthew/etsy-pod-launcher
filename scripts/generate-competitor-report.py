#!/usr/bin/env python3
"""
generate-competitor-report.py

Generates a self-contained competitor-report.html with three tabs:
  Tab 1 — Market Insights    (Niche Verdict + Design Patterns visual + market-insights.md sections)
  Tab 2 — Competitor Report  (card grid from competitors.json)
  Tab 3 — Shop Intelligence  (M1/M2/M3 table from shop-watchlist.json)

Required inputs before running:
  competitors.json, market-insights.md, shop-watchlist.json, patterns-config.json

Usage:
  python3 scripts/generate-competitor-report.py --niche personalized-gift-for-dad
"""

import json, argparse, datetime, re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def niche_to_title(niche: str) -> str:
    return niche.replace('-', ' ').title()


# ── Design patterns helpers ───────────────────────────────────────────────────

def assign_pattern(entry, patterns):
    """First-match-wins classification using config array order."""
    title = (entry.get('title') or '').lower()
    fallback = 'P0'
    for p in patterns:
        pid = p['id']
        if pid == 'P0':
            fallback = pid
            continue
        for rule in p.get('confirmed_field_rules', []):
            field_val = entry.get(rule['field'])
            if field_val == rule['value']:
                if rule.get('confirmed_only'):
                    if entry.get(rule['field'] + '_confirmed'):
                        return pid
                else:
                    return pid
        if any(kw.lower() in title for kw in p.get('keywords', [])):
            return pid
    return fallback


def dp_ems_color(reviews):
    if reviews is None: return '#9ca3af'
    if reviews >= 500:  return '#16a34a'
    if reviews >= 100:  return '#d97706'
    return '#9ca3af'


def escape_html(s):
    return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _extract_interp_slots(section_text):
    """Pull interpretation lines from an existing Section 6 block.

    Returns up to 4 slots (verdict, badge commentary, carts commentary,
    pattern commentary). Slots with [FILL IN] or empty content return ''.
    """
    slots = []
    current = []
    in_table = False

    for line in section_text.split('\n'):
        s = line.strip()
        if s.startswith('|'):
            in_table = True
            if current:
                slots.append(' '.join(current))
                current = []
        elif s.startswith('##') or s == '---' or not s:
            if in_table and current:
                slots.append(' '.join(current))
                current = []
            in_table = False
        else:
            if not in_table:
                current.append(s)
    if current:
        slots.append(' '.join(current))

    # Drop lines that are only a source tag (e.g. `` `[our data]` `` standalone)
    _src_only = re.compile(r'^`\[(our data|inferred|market knowledge)\]`$')
    cleaned = []
    for slot in slots:
        if not slot or '[FILL IN' in slot or _src_only.match(slot):
            cleaned.append('')
        else:
            cleaned.append(slot)
    while len(cleaned) < 4:
        cleaned.append('')
    return cleaned[:4]


def _tier_signal_commentary(tier, baseline, tier_label, gap_threshold=20):
    """
    Compare a tier against the baseline (all other listings) on measurable signals.
    Only surface findings where the gap >= gap_threshold percentage points.
    Returns a list of finding strings, each tagged [our data] / [inferred].
    """
    from datetime import date, datetime
    today = date.today()

    def rate(group, fn):
        if not group:
            return 0
        return round(sum(1 for d in group if fn(d)) / len(group) * 100)

    signals = {
        'Comfort Colors blank': lambda d: 'comfort' in (d.get('blank') or '').lower(),
        'personalization':      lambda d: bool(d.get('personalization')),
        'Bestseller badge':     lambda d: bool(d.get('is_bestseller')),
        'in carts':             lambda d: (d.get('in_carts') or 0) > 0,
        'reviewed last 7 days': lambda d: bool(
            d.get('most_recent_review_date') and
            (today - datetime.strptime(d['most_recent_review_date'], '%Y-%m-%d').date()).days <= 7
        ),
    }

    findings = []
    for label, fn in signals.items():
        tier_rate = rate(tier, fn)
        base_rate = rate(baseline, fn)
        gap = tier_rate - base_rate
        if abs(gap) >= gap_threshold:
            direction = 'higher' if gap > 0 else 'lower'
            findings.append(
                f'**{label}**: {tier_rate}% of {tier_label} vs {base_rate}% of remaining listings '
                f'({abs(gap)}pp {direction}). `[our data]`'
            )

    return findings


def _fpr_confidence(reviews):
    """Deterministic confidence tier for FPR based on review count."""
    if reviews >= 20:
        return '✅ High'
    elif reviews >= 5:
        return '⚠️ Medium'
    else:
        return '❌ Low'


def update_listings_to_watch_in_md(md_text, comp_data):
    """Rewrite Section 7 (Listings to Watch) — fully deterministic, no AI fill-in."""
    shirts = [e for e in comp_data if e.get('is_shirt')]
    fpr_entries = []
    for e in shirts:
        fpr = e.get('favorites_per_review')
        if not fpr or fpr <= 0:
            continue
        reviews  = e.get('reviews') or 0
        sales    = e.get('shop_sales') or 0
        yrs      = e.get('shop_years_on_etsy')
        fpr_entries.append({
            'id':       e.get('id'),
            'title':    (e.get('title') or '')[:52],
            'fpr':      fpr,
            'reviews':  reviews,
            'favorites': e.get('favorites_count') or 0,
            'bs':       e.get('is_bestseller', False),
            'carts':    e.get('in_carts'),
            'sales':    sales,
            'years':    yrs,
            'conf':     _fpr_confidence(reviews),
        })
    tier1 = sorted(
        [e for e in fpr_entries if e['fpr'] > 5.0 and e['reviews'] >= 20],
        key=lambda x: -x['fpr']
    )
    tier2 = sorted(
        [e for e in fpr_entries if e['fpr'] > 10.0 and e['reviews'] < 20],
        key=lambda x: -x['fpr']
    )

    # Raw shirt entries for signal comparison (keyed by listing id)
    shirt_map = {e.get('id'): e for e in shirts}
    tier1_ids = {r['id'] for r in tier1}
    tier2_ids = {r['id'] for r in tier2}
    tier1_raw = [shirt_map[i] for i in tier1_ids if i in shirt_map]
    tier2_raw = [shirt_map[i] for i in tier2_ids if i in shirt_map]
    rest_raw  = [e for e in shirts if e.get('id') not in tier1_ids and e.get('id') not in tier2_ids]

    if not tier1 and not tier2:
        return md_text

    col_header = '| Rank | ID | Title (truncated) | FPR | Reviews | Favorites | Bestseller | In-Carts | Shop Sales | Shop Yrs | Confidence |'
    col_sep    = '|---|---|---|---|---|---|---|---|---|---|---|'

    def build_rows(entries):
        rows = []
        for i, r in enumerate(entries, 1):
            carts = r['carts'] if r['carts'] is not None else 'null'
            yrs   = f"{r['years']:.1f}" if r['years'] else '?'
            bs    = '✓' if r['bs'] else '—'
            title = r['title'].replace('|', '–')  # pipe breaks markdown table cells
            conf  = r['conf']
            if r['reviews'] >= 20 and r['years'] and r['years'] <= 1.0:
                conf += ' ⚡'  # young shop accumulating reviews fast
            rows.append(
                f"| {i} | {r['id']} | {title} | {r['fpr']} "
                f"| {r['reviews']} | {r['favorites']:,} | {bs} | {carts} "
                f"| {r['sales']:,} | {yrs} | {conf} |"
            )
        return rows

    # Tier 1 block
    if tier1:
        t1_findings = _tier_signal_commentary(tier1_raw, rest_raw, f'Tier 1 ({len(tier1)})')
        t1_signal_block = (
            '\n**What these listings have in common vs the rest of the field:**\n'
            + '\n'.join(f'- {f}' for f in t1_findings)
            + ('\n- *No signals exceed the 20pp gap threshold — Tier 1 listings do not differ significantly from the field on measured attributes.* `[our data]`' if not t1_findings else '')
        )
        tier1_block = (
            f'### Tier 1 — Reliable (reviews ≥ 20, FPR > 5.0)\n\n'
            f'{col_header}\n{col_sep}\n'
            + chr(10).join(build_rows(tier1))
            + f'\n{t1_signal_block}'
        )
    else:
        tier1_block = '### Tier 1 — Reliable (reviews ≥ 20, FPR > 5.0)\n\n*No listings meet Tier 1 criteria.*'

    # Tier 2 block (omit if empty)
    if tier2:
        low_conf_t2 = sum(1 for r in tier2 if r['conf'] == '❌ Low')
        warn_line = (
            f'\n⚠️ **Data quality note:** {low_conf_t2} of {len(tier2)} Tier 2 listings have fewer than 5 reviews — '
            f'FPR is unreliable at this sample size; treat as directional only. `[our data]`\n'
            if low_conf_t2 else ''
        )
        t2_findings = _tier_signal_commentary(tier2_raw, rest_raw, f'Tier 2 ({len(tier2)})')
        t2_signal_block = (
            '\n**What these listings have in common vs the rest of the field:**\n'
            + '\n'.join(f'- {f}' for f in t2_findings)
            + ('\n- *No signals exceed the 20pp gap threshold — Tier 2 listings do not differ significantly from the field on measured attributes.* `[our data]`' if not t2_findings else '')
        )
        tier2_block = (
            f'### Tier 2 — Directional only (reviews < 20, FPR > 10.0 — treat as weak signal)\n'
            f'{warn_line}\n'
            f'{col_header}\n{col_sep}\n'
            + chr(10).join(build_rows(tier2))
            + f'\n{t2_signal_block}'
        )
    else:
        tier2_block = ''

    # Auto-commentary across both tiers
    all_entries = tier1 + tier2
    accessible  = sum(1 for r in all_entries if r['sales'] < 20_000)
    bs_count    = sum(1 for r in all_entries if r['bs'])
    entry_note  = (
        'suggesting this pattern is reachable for a new entrant'
        if accessible >= 3
        else 'most are from established shops — harder to replicate quickly'
    )
    commentary = (
        f'Tier 1 ({len(tier1)} reliable listings) + Tier 2 ({len(tier2)} directional). `[our data]` '
        f'{bs_count} top-FPR listings carry a Bestseller badge. `[our data]` '
        f'{accessible} across both tiers are from shops with under 20k total sales — {entry_note}. `[inferred]`'
    )

    tier2_section = f'\n{tier2_block}\n' if tier2_block else ''

    new_section = f"""
## 7. Listings to Watch

*(favorites_per_review — high buyer interest relative to review count)*

Shoppers are saving these items faster than they are leaving reviews — signals a newer listing gaining traction, a price above impulse-buy threshold, or a wishlist/gift item. `[market knowledge]` FPR is only reliable when reviews ≥ 20; lower counts are directional only. `[market knowledge]` ⚡ = shop under 1 year old with ≥ 20 reviews — high review velocity relative to shop age. `[inferred]`

{tier1_block}
{tier2_section}
{commentary}

---
"""
    start = md_text.find('\n## 7. Listings to Watch')
    if start == -1:
        return md_text
    end_match = re.search(r'\n## [^7\n]', md_text[start + 1:])
    end = start + 1 + end_match.start() if end_match else len(md_text)
    return md_text[:start] + new_section + md_text[end:]


def _entrenchment_tier(entry):
    """Classify a listing's shop as entrenched / mid / accessible.

    Uses shop_sales (available for all entries) as primary signal.
    shop_years_on_etsy upgrades to 'entrenched' when >= 5 years regardless of sales.
    """
    sales = entry.get('shop_sales') or 0
    years = entry.get('shop_years_on_etsy') or 0
    if sales >= 100_000 or years >= 5:
        return 'entrenched'
    elif sales >= 20_000 or years >= 2:
        return 'mid'
    else:
        return 'accessible'


def update_demand_signals_in_md(md_text, comp_data, patterns_config):
    """Rewrite Section 6 in market-insights.md — fully deterministic, no AI fill-in slots."""
    patterns = (patterns_config or {}).get('patterns', [])
    n = len(comp_data)

    # ── Badge counts ──────────────────────────────────────────────────────────
    bs_count      = sum(1 for e in comp_data if e.get('is_bestseller'))
    pick_count    = sum(1 for e in comp_data if e.get('badge') == "Etsy's Pick")
    in_carts_any  = sum(1 for e in comp_data if (e.get('in_carts') or 0) > 0)
    in_carts_null = sum(1 for e in comp_data if e.get('in_carts') is None)

    pick_shops = ', '.join(
        f"{e.get('shop_name')} ({e.get('reviews') or 0:,} reviews)"
        for e in comp_data if e.get('badge') == "Etsy's Pick"
    )
    pick_note = (
        f'Not a lesser signal — {pick_shops} `[our data]`'
        if pick_count else 'Signal exists on Etsy but did not trigger `[our data]`'
    )

    in_demand_listings = [
        e for e in comp_data
        if any('In demand' in s for s in (e.get('demand_signals') or []))
    ]
    in_demand_detail = ', '.join(
        f"{e.get('shop_name')} ({re.search(r'(\d+) people', next(s for s in e['demand_signals'] if 'In demand' in s)).group(1)} bought)"
        for e in in_demand_listings
        if re.search(r'(\d+) people', next((s for s in e['demand_signals'] if 'In demand' in s), ''))
    ) or '—'
    demand_24h_note = (
        f'24h snapshot only — not confirmed sustained demand: {in_demand_detail} `[our data]`'
        if in_demand_listings else 'Signal exists on Etsy but did not trigger `[our data]`'
    )

    # ── Entrenchment breakdown of bestseller badge holders ────────────────────
    bs_entries    = [e for e in comp_data if e.get('is_bestseller')]
    n_entrenched  = sum(1 for e in bs_entries if _entrenchment_tier(e) == 'entrenched')
    n_mid         = sum(1 for e in bs_entries if _entrenchment_tier(e) == 'mid')
    n_accessible  = sum(1 for e in bs_entries if _entrenchment_tier(e) == 'accessible')
    pct_accessible = round(n_accessible / bs_count * 100) if bs_count else 0

    years_known = [e.get('shop_years_on_etsy') for e in bs_entries if e.get('shop_years_on_etsy')]
    median_years = sorted(years_known)[len(years_known) // 2] if years_known else None
    years_range  = f'{min(years_known):.0f}–{max(years_known):.0f}' if years_known else 'unknown'

    top_reviews = max((e.get('reviews') or 0) for e in comp_data)
    high_proof  = sum(1 for e in comp_data if (e.get('reviews') or 0) >= 500)

    # ── Auto-generated verdict (no AI) ───────────────────────────────────────
    entry_outlook = (
        'majority accessible to a new entrant'
        if pct_accessible >= 50
        else 'market is mid-to-entrenched — expect slower ramp'
    )
    v_line = (
        f'{bs_count}/{n} listings carry a Bestseller badge (sustained 6-month purchase volume); '
        f'top listing has {top_reviews:,} reviews; {high_proof} listings exceed 500 reviews. `[our data]` '
        f'{pct_accessible}% of badge-holders are from shops with under 20k total sales or under 5 years on Etsy — {entry_outlook}. `[inferred]`'
    )

    # ── Entrenchment commentary (no AI) ──────────────────────────────────────
    b_line = (
        f'{n_entrenched} of {bs_count} Bestseller listings are from entrenched shops '
        f'(100k+ sales or 5+ years on Etsy); {n_mid} are mid-tier; {n_accessible} are accessible. `[our data]` '
        f'Shop age for badge-holders: median {median_years:.0f} years, range {years_range} years. `[our data]`'
        if years_known else
        f'{n_entrenched} of {bs_count} Bestseller listings are from entrenched shops '
        f'(100k+ sales); {n_mid} are mid-tier; {n_accessible} are accessible. `[our data]`'
    )

    # ── In-carts buckets ─────────────────────────────────────────────────────
    b20  = sum(1 for e in comp_data if (e.get('in_carts') or 0) >= 20)
    b11  = sum(1 for e in comp_data if 11 <= (e.get('in_carts') or 0) <= 19)
    b1   = sum(1 for e in comp_data if 1  <= (e.get('in_carts') or 0) <= 10)
    pct_cap = round(b20 / n * 100) if n else 0
    c_line = f'{pct_cap}% of listings are at the display cap (20+). `[our data]` Cart counts are intent signals — not purchases; abandon rates on Etsy are high. `[market knowledge]`'

    # ── Pattern breakdown with Entry Score ───────────────────────────────────
    plabel = {p['id']: p['label'] for p in patterns}
    groups = {}
    for e in comp_data:
        pid = assign_pattern(e, patterns) if patterns else 'P0'
        groups.setdefault(pid, []).append(e)

    scored = []
    for pid, entries in groups.items():
        pn   = len(entries)
        pbs  = sum(1 for e in entries if e.get('is_bestseller'))
        pc   = sum(1 for e in entries if (e.get('in_carts') or 0) > 0)
        pc20 = sum(1 for e in entries if (e.get('in_carts') or 0) >= 20)
        pavg = round(sum((e.get('reviews') or 0) for e in entries) / pn)
        bsl_pct = pbs / pn if pn else 0
        # Entry score: bestseller% / listing_count — higher = more proven demand per competitor
        score = round(bsl_pct / pn, 4) if pn >= 3 else None  # skip tiny samples
        label = plabel.get(pid, pid)
        scored.append((pid, label, pn, pbs, pc, pc20, pavg, bsl_pct, score))

    # Sort by avg reviews descending (keeps existing visual order)
    scored.sort(key=lambda x: -x[6])

    pattern_rows = []
    for pid, label, pn, pbs, pc, pc20, pavg, bsl_pct, score in scored:
        if score is None:
            score_cell = '⚠️ n<3'
        else:
            score_cell = f'{score:.3f}'
        pattern_rows.append(
            f'| {label} | {pn} | {pbs}/{pn} | {pc}/{pn} | {pc20}/{pn} | {pavg:,} | {score_cell} |'
        )

    # ── Auto-generated pattern commentary (no AI) ────────────────────────────
    eligible = [(label, pn, pbs, pavg, score) for _, label, pn, pbs, pc, pc20, pavg, bsl_pct, score in scored if score is not None]
    if eligible:
        best_label, best_n, best_bs, best_avg, best_score = max(eligible, key=lambda x: x[4])
        worst_label, worst_n, worst_bs, worst_avg, worst_score = min(eligible, key=lambda x: x[4])
        p_line = (
            f'Best entry pattern: **{best_label}** — {best_n} listings, {best_bs}/{best_n} Bestseller, '
            f'avg {best_avg:,} reviews, Entry Score {best_score:.3f}. `[our data]` '
            f'Avoid **{worst_label}** as a first listing — {worst_n} competitors, lowest Entry Score ({worst_score:.3f}). `[inferred]`'
        )
    else:
        p_line = 'Insufficient pattern data to compute Entry Score. `[our data]`'

    # ── Assemble section ──────────────────────────────────────────────────────
    start = md_text.find('\n## 6. Demand Signals Summary')
    if start == -1:
        return md_text
    end_match = re.search(r'\n## [^6\n]', md_text[start + 1:])
    end = start + 1 + end_match.start() if end_match else len(md_text)

    new_section = f"""
## 6. Demand Signals Summary

{v_line}

### Bestseller Badge Holders — Shop Entrenchment

| Tier | Count | Criteria |
|---|---|---|
| Entrenched | {n_entrenched}/{bs_count} | 100k+ shop sales or 5+ years on Etsy `[our data]` |
| Mid-tier | {n_mid}/{bs_count} | 20k–100k sales or 2–5 years `[our data]` |
| Accessible | {n_accessible}/{bs_count} | Under 20k sales and under 5 years `[our data]` |

{b_line}

### Etsy Demand Labels — Full Scan

| Signal | Count | Reliability | Notes |
|---|---|---|---|
| Bestseller badge | {bs_count}/{n} | Strong | Sustained 6-month sales volume — official Etsy criteria `[market knowledge]` |
| Etsy's Pick badge | {pick_count}/{n} | Medium | {pick_note} |
| In-carts detected | {in_carts_any}/{n} | Medium | Intent signal — not a purchase; {in_carts_null} listings returned null `[our data]` |
| "N bought in last 24h" | {len(in_demand_listings)}/{n} | Snapshot only | {demand_24h_note} |

### In-Carts Heat

| Cart level | Listings | Signal |
|---|---|---|
| 20+ (Etsy display cap) | {b20}/{n} | Hot — real counts likely higher `[market knowledge]` |
| 11–19 | {b11}/{n} | Warm |
| 1–10 | {b1}/{n} | Mild |
| Not detected (null) | {in_carts_null}/{n} | Unknown — scraper could not read `[our data]` |

{c_line}

### Demand by Pattern Segment

*Entry Score = bestseller% ÷ listing count. Higher = more proven demand per competitor. Patterns with fewer than 3 listings excluded.*

| Pattern | Listings | Bestseller | Carts > 0 | Carts 20+ | Avg Reviews | Entry Score |
|---|---|---|---|---|---|---|
{chr(10).join(pattern_rows)}

{p_line}

---
"""
    return md_text[:start] + new_section + md_text[end:]


def build_design_patterns_section(comp_data, config):
    """Build the Netflix-rows design patterns block for Tab 1."""
    patterns = config.get('patterns', [])
    if not patterns:
        return ''

    pattern_map   = {p['id']: p for p in patterns}
    display_sorted = sorted(patterns, key=lambda p: p.get('display_rank', 99))
    ordered_ids   = [p['id'] for p in display_sorted]

    groups = {p['id']: [] for p in patterns}
    for e in comp_data:
        if e.get('image_url'):
            groups[assign_pattern(e, patterns)].append(e)
    for k in groups:
        groups[k].sort(key=lambda e: e.get('reviews') or 0, reverse=True)

    total     = sum(len(v) for v in groups.values())
    n_patterns = len([p for p in patterns if p['id'] != 'P0'])

    rows_html = ''
    for pid in ordered_ids:
        items = groups.get(pid, [])
        meta  = pattern_map[pid]
        color = meta.get('color', '#9ca3af')
        count = len(items)

        cards_html = ''
        if not items:
            cards_html = '<span class="dp-empty">No listings classified in this pattern.</span>'
        else:
            for e in items:
                eid   = e.get('id', '')
                url   = e.get('url', f'https://www.etsy.com/listing/{eid}/')
                img   = e.get('image_url', '')
                title = escape_html((e.get('title') or '')[:120])
                reviews = e.get('reviews') or 0
                price   = escape_html(e.get('price') or '')
                reviews_val = e.get('reviews') or 0
                ems_bg  = dp_ems_color(reviews_val if reviews_val > 0 else None)
                ems_label = f'{reviews_val:,} reviews' if reviews_val else 'No reviews'
                is_best   = e.get('is_bestseller', False)
                best_badge = '<span class="dp-badge-best">&#9733; Best</span>' if is_best else ''
                ems_badge  = f'<span class="dp-badge-ems" style="background:{ems_bg}">{ems_label}</span>'
                cards_html += (
                    f'<a class="dp-card" href="{url}" target="_blank">'
                    f'<div class="dp-card-img"><img src="{img}" alt="" loading="lazy">'
                    f'{ems_badge}{best_badge}</div>'
                    f'<div class="dp-card-body">'
                    f'<div class="dp-card-title">{title}</div>'
                    f'<div class="dp-card-meta">{reviews:,} reviews &middot; {price}</div>'
                    f'</div></a>'
                )

        rows_html += (
            f'\n<div class="dp-row" style="--dp-color:{color}">'
            f'\n  <div class="dp-row-header">'
            f'<span class="dp-row-label">{escape_html(meta["label"])}</span>'
            f'<span class="dp-row-count">{count} listings</span></div>'
            f'\n  <p class="dp-row-desc">{escape_html(meta.get("description",""))}</p>'
            f'\n  <div class="dp-scroll">{cards_html}</div>'
            f'\n</div>'
        )

    return (
        f'\n<div class="dp-section">'
        f'\n<h2 class="mi-h2">Top Design Patterns</h2>'
        f'\n<p class="dp-subtitle">{total} listings across {n_patterns} patterns'
        f' &middot; listed in no particular order &middot; click any card to open on Etsy</p>'
        f'{rows_html}'
        f'\n</div>'
    )


def build_garment_blanks_section(comp_data):
    """Compute Section 3: Garment Blanks — always derived from competitors.json."""
    from collections import Counter
    total = len(comp_data)

    raw_counts = Counter(e.get('blank') for e in comp_data)
    null_count = raw_counts.pop(None, 0)
    identified = total - null_count

    # Consolidate sub-variants for display but keep raw counts accurate
    groups = {}  # display_name -> {sub: count}
    for blank, cnt in raw_counts.items():
        if 'Comfort Colors' in blank:
            groups.setdefault('Comfort Colors', {})['— ' + blank] = cnt
        elif 'Bella' in blank:
            groups.setdefault('Bella Canvas', {})['— ' + blank] = cnt
        elif 'Gildan' in blank:
            groups.setdefault('Gildan', {})['— ' + blank] = cnt
        else:
            groups.setdefault(blank, {})[blank] = cnt

    rows_html = ''
    for group, subs in sorted(groups.items(), key=lambda x: -sum(x[1].values())):
        group_total = sum(subs.values())
        rows_html += f'<tr><td><strong>{escape_html(group)} (all variants)</strong></td><td style="text-align:right">{group_total}</td><td>Consolidated <span class="src-tag src-our-data" title="[our data]">[our data]</span></td></tr>'
        for sub, cnt in sorted(subs.items(), key=lambda x: -x[1]):
            label = sub if sub.startswith('—') else '— ' + sub
            rows_html += f'<tr><td style="padding-left:24px">{escape_html(label)}</td><td style="text-align:right">{cnt}</td><td>blank field = <code class="mi-code">{escape_html(sub.lstrip("— "))}</code> <span class="src-tag src-our-data" title="[our data]">[our data]</span></td></tr>'

    rows_html += (
        f'<tr><td><strong>Not specified (null)</strong></td>'
        f'<td style="text-align:right">{null_count}</td>'
        f'<td>Blank could not be parsed from listing <span class="src-tag src-our-data" title="[our data]">[our data]</span></td></tr>'
    )

    cc_total = sum(v for k, v in raw_counts.items() if 'Comfort Colors' in k)
    cc_pct = round(cc_total / total * 100, 1)

    return (
        '<h2 class="mi-h2">3. Garment Blanks Mentioned</h2>'
        '<div class="mi-table-wrap"><table class="mi-table">'
        '<thead><tr><th>Blank</th><th style="text-align:right">Count</th><th>Notes</th></tr></thead>'
        '<tbody>' + rows_html + '</tbody>'
        '</table></div>'
        f'<p class="mi-p"><strong>Totals:</strong> {identified}/{total} listings have a blank identified; {null_count}/{total} have null. '
        f'<span class="src-tag src-our-data" title="[our data]">[our data]</span></p>'
        f'<p class="mi-p"><strong>Important caveat:</strong> The <code class="mi-code">blank</code> field is populated by title/description text parsing. '
        f'<span class="src-tag src-our-data" title="[our data]">[our data]</span> '
        f'Sellers sometimes name a blank in their listing title for SEO purposes even if the product ships on a different blank. '
        f'<span class="src-tag src-market" title="[market knowledge]">[market knowledge]</span></p>'
        f'<p class="mi-p"><strong>Comfort Colors dominance:</strong> {cc_total}/{total} listings ({cc_pct}%) reference Comfort Colors. '
        f'<span class="src-tag src-our-data" title="[our data]">[our data]</span> '
        f'Comfort Colors garment-dyed blanks are broadly favored in POD apparel niches for their vintage aesthetic — this niche confirms that pattern. '
        f'<span class="src-tag src-market" title="[market knowledge]">[market knowledge]</span></p>'
        '<div class="mi-hr"></div>'
    )


def build_print_methods_section(comp_data):
    """Compute Section 4: Print Methods — always derived from competitors.json."""
    from collections import Counter
    total = len(comp_data)

    method_stats = {}  # method -> {total, confirmed, inferred}
    for e in comp_data:
        m = e.get('print_method') or 'unknown'
        confirmed = bool(e.get('print_method_confirmed'))
        if m not in method_stats:
            method_stats[m] = {'total': 0, 'confirmed': 0, 'inferred': 0}
        method_stats[m]['total'] += 1
        if m == 'unknown':
            method_stats[m]['inferred'] += 1
        elif confirmed:
            method_stats[m]['confirmed'] += 1
        else:
            method_stats[m]['inferred'] += 1

    display_order = ['dtg', 'embroidery', 'screen_print', 'unknown']
    display_names = {'dtg': 'DTG', 'embroidery': 'Embroidery', 'screen_print': 'Screen print', 'unknown': 'Unknown'}

    rows_html = ''
    grand_total = grand_confirmed = grand_inferred = 0
    for m in display_order:
        if m not in method_stats:
            continue
        s = method_stats[m]
        name = display_names.get(m, m)
        conf_str = 'n/a' if m == 'unknown' else str(s['confirmed'])
        rows_html += (
            f'<tr><td>{name}</td>'
            f'<td style="text-align:right">{s["total"]}</td>'
            f'<td style="text-align:right">{conf_str}</td>'
            f'<td style="text-align:right">{s["inferred"]}</td></tr>'
        )
        grand_total += s['total']
        grand_confirmed += s['confirmed']
        grand_inferred += s['inferred']

    rows_html += (
        f'<tr><td><strong>Total</strong></td>'
        f'<td style="text-align:right"><strong>{grand_total}</strong></td>'
        f'<td style="text-align:right"><strong>{grand_confirmed}</strong></td>'
        f'<td style="text-align:right"><strong>{grand_inferred}</strong></td></tr>'
    )

    dtg = method_stats.get('dtg', {})
    emb = method_stats.get('embroidery', {})
    unk = method_stats.get('unknown', {})

    dtg_total = dtg.get('total', 0)
    emb_total = emb.get('total', 0)
    emb_confirmed = emb.get('confirmed', 0)
    dtg_inferred = dtg.get('inferred', 0)
    dtg_pct = round(dtg_total / total * 100, 1) if total else 0
    emb_pct = round(emb_total / total * 100, 1) if total else 0
    unk_total = unk.get('total', 0)

    prose = (
        f'All method counts are from competitors.json. <span class="src-tag src-our-data" title="[our data]">[our data]</span> '
        f'{dtg_inferred} of the {dtg_total} DTG listings are inferred — the print method was not stated explicitly in the listing. '
        f'<span class="src-tag src-our-data" title="[our data]">[our data]</span> '
    )
    if emb_confirmed == emb_total and emb_total > 0:
        prose += (
            f'Embroidery is always explicitly stated ({emb_confirmed}/{emb_total} confirmed). '
            f'<span class="src-tag src-our-data" title="[our data]">[our data]</span> '
        )
    prose += (
        f'Sellers typically call out embroidery as a premium selling point but treat DTG as a generic default not worth mentioning. '
        f'<span class="src-tag src-market" title="[market knowledge]">[market knowledge]</span>'
    )

    # Unknown caveat if significant
    unknown_note = ''
    if unk_total >= 5:
        unk_pct = round(unk_total / total * 100)
        unknown_note = (
            f'<p class="mi-p"><strong>Note:</strong> {unk_total} listings ({unk_pct}%) have an unresolved print method — '
            f'these are typically listings where neither the title, description, nor tags made the method clear. '
            f'Do not conflate "unknown" with DTG; treat them as unverified. '
            f'<span class="src-tag src-our-data" title="[our data]">[our data]</span></p>'
        )

    dist_note = (
        f'<p class="mi-p"><strong>Distribution:</strong> DTG is the dominant method ({dtg_pct}% of listings). '
        f'Embroidery is present in {emb_total} listings ({emb_pct}%), concentrated in sweatshirts and portrait-from-photo products. '
        f'<span class="src-tag src-our-data" title="[our data]">[our data]</span></p>'
    )

    return (
        '<h2 class="mi-h2">4. Print Methods</h2>'
        '<div class="mi-table-wrap"><table class="mi-table">'
        '<thead><tr>'
        '<th>Method</th>'
        '<th style="text-align:right">Total</th>'
        '<th style="text-align:right">Confirmed</th>'
        '<th style="text-align:right">Inferred</th>'
        '</tr></thead>'
        '<tbody>' + rows_html + '</tbody>'
        '</table></div>'
        f'<p class="mi-p">{prose}</p>'
        + dist_note
        + unknown_note
        + '<div class="mi-hr"></div>'
    )


def build_listing_pricing_strategy_section(comp_data):
    """Build the combined Pricing & Listing Strategy section for Tab 1."""
    from collections import Counter
    import statistics

    if not comp_data:
        return ''

    total = len(comp_data)

    # ── Part 1: Intro paragraph ───────────────────────────────────────────────

    intro_p = (
        '<p class="mi-p">Pricing in the dog-mom niche is more complex than it appears. '
        'Most high-volume sellers use <strong>anchor pricing</strong> — displaying an artificially '
        'low variant (youth sizes, digital files, small accessories) in Etsy search results while '
        'the shirt a buyer actually wants costs significantly more. '
        'Understanding the gap between displayed prices and real prices is essential before you '
        'set your own — you could inadvertently anchor against yourself or misprice relative '
        'to the true competitive range.</p>'
    )

    # ── Part 2: Price band table (uses price_real_min) ────────────────────────

    BANDS = [
        ('Under $14',  None,  14.0),
        ('$14–$20',    14.0,  20.0),
        ('$20–$28',    20.0,  28.0),
        ('$28+',       28.0,  None),
    ]

    def band_label(price):
        for label, lo, hi in BANDS:
            if (lo is None or price >= lo) and (hi is None or price < hi):
                return label
        return '$28+'

    band_groups = {label: [] for label, _, _ in BANDS}
    for e in comp_data:
        real_min = e.get('price_real_min')
        if real_min is not None:
            lbl = band_label(real_min)
            band_groups[lbl].append(e)

    band_rows_html = ''
    best_band_label = None
    best_band_ems = -1
    for label, lo, hi in BANDS:
        items = band_groups[label]
        count = len(items)
        if count == 0:
            continue
        real_mins_all = [e.get('price_real_min') for e in comp_data if e.get('price_real_min') is not None]
        denom = len(real_mins_all) if real_mins_all else 1
        pct = round(count / denom * 100)
        reviews_vals = [e.get('reviews') for e in items if e.get('reviews') is not None]
        avg_ems = round(statistics.mean(reviews_vals)) if reviews_vals else None
        if avg_ems is not None and avg_ems > best_band_ems:
            best_band_ems = avg_ems
            best_band_label = label
        best_e = max(items, key=lambda e: e.get('reviews') or 0)
        example_url = best_e.get('url', '')
        avg_ems_str = str(avg_ems) if avg_ems is not None else '—'
        link = f'<a href="{example_url}" target="_blank">View →</a>' if example_url else '—'
        band_rows_html += (
            f'<tr>'
            f'<td><strong>{escape_html(label)}</strong></td>'
            f'<td style="text-align:right">{count}</td>'
            f'<td style="text-align:right">{pct}%</td>'
            f'<td style="text-align:right">{avg_ems_str}</td>'
            f'<td>{link}</td>'
            f'</tr>'
        )

    band_table = (
        '<div class="mi-table-wrap"><table class="mi-table">'
        '<thead><tr>'
        '<th>Price Band</th>'
        '<th style="text-align:right">Sellers</th>'
        '<th style="text-align:right">%</th>'
        '<th style="text-align:right">Avg Reviews</th>'
        '<th>Best Example</th>'
        '</tr></thead>'
        '<tbody>' + band_rows_html + '</tbody>'
        '</table></div>'
    )

    # Qualitative insight for price bands
    premium_items = band_groups.get('$28+', [])
    premium_ems_vals = [e.get('reviews') for e in premium_items if e.get('reviews') is not None]
    premium_avg_ems = round(statistics.mean(premium_ems_vals)) if premium_ems_vals else None
    premium_count = len(premium_items)

    if best_band_label:
        if best_band_label == '$28+':
            band_insight = (
                f'The <strong>{best_band_label}</strong> band has the highest avg reviews ({best_band_ems}), '
                f'suggesting buyers in this niche will pay a premium for perceived quality or personalization.'
            )
        elif best_band_label in ('Under $14', '$14–$20'):
            band_insight = (
                f'The <strong>{best_band_label}</strong> band has the highest avg reviews ({best_band_ems}), '
                f'suggesting buyers in this niche are price-sensitive — volume comes from accessible price points.'
            )
        else:
            band_insight = (
                f'The <strong>{best_band_label}</strong> band has the highest avg reviews ({best_band_ems}), '
                f'suggesting the sweet spot is mid-range pricing — not cheap enough to signal low quality, '
                f'not expensive enough to lose impulse buyers.'
            )
        if premium_avg_ems is not None:
            band_insight += (
                f' Only {premium_count} seller{"s" if premium_count != 1 else ""} operate above $28, '
                f'averaging {premium_avg_ems} reviews — {"a viable premium tier exists" if premium_avg_ems > best_band_ems * 0.7 else "premium positioning is difficult in this niche"}.'
            )
    else:
        band_insight = 'Insufficient price_real_min data to draw conclusions about price bands.'

    band_insight_p = f'<p class="mi-p">{band_insight}</p>'

    price_band_section = (
        f'<h3 class="mi-h3">What does a shirt actually cost here?</h3>'
        f'{band_table}'
        f'{band_insight_p}'
    )

    # ── Part 3: How search prices are manipulated ─────────────────────────────

    price_real_mins = [e.get('price_real_min') for e in comp_data if e.get('price_real_min') is not None]
    real_mins  = [e.get('price_real_min') for e in comp_data if e.get('price_real_min') is not None]

    if price_real_mins and real_mins:
        median_display = sorted(price_real_mins)[len(price_real_mins) // 2]
        median_real    = sorted(real_mins)[len(real_mins) // 2]
        gap_pct = round((median_real - median_display) / median_display * 100) if median_display else 0
        illusion_warn = (
            f'<div class="mi-warn">'
            f'Median price shown in Etsy search: <strong>${median_display:.2f}</strong> '
            f'&rarr; Median price buyers actually pay: <strong>${median_real:.2f}</strong> '
            f'&mdash; a gap of {gap_pct}% created by anchor variants that most buyers never purchase.'
            f'</div>'
        )
    else:
        illusion_warn = ''

    # Anchor strategy table
    ANCHOR_LABELS = {
        'youth':            'Youth / kids size anchor',
        'honest':           'Honest pricing',
        'size_anchor_low':  'Size anchor — potential (20–49% gap)',
        'size_anchor_high': 'Size anchor — confirmed (50%+ gap)',
        'digital_file':     'Digital file anchor',
        'bandana':          'Bandana / small item anchor',
        'embroidery_file':  'Embroidery file anchor',
        'quantity_pricing': 'Quantity / bulk pricing',
    }

    known_anchor_keys = set(ANCHOR_LABELS.keys()) - {'honest', 'quantity_pricing'}
    extra_types = set()
    for e in comp_data:
        at = e.get('anchor_type')
        if at and at not in known_anchor_keys:
            extra_types.add(at)

    def group_key(e):
        at = e.get('anchor_type')
        qp = e.get('quantity_pricing', False)
        if qp:
            return 'quantity_pricing'
        if at is None:
            return 'honest'
        return at

    anchor_groups = {}
    for e in comp_data:
        k = group_key(e)
        anchor_groups.setdefault(k, []).append(e)

    ordered_keys = list(ANCHOR_LABELS.keys()) + sorted(extra_types)
    anchor_rows_data = []
    for key in ordered_keys:
        items = anchor_groups.get(key, [])
        if not items:
            continue
        label = ANCHOR_LABELS.get(key, key.replace('_', ' ').title())
        count = len(items)
        pct = round(count / total * 100)
        ems_vals = [e.get('reviews') for e in items if e.get('reviews') is not None]
        avg_ems = round(statistics.mean(ems_vals)) if ems_vals else None
        best_e = max(items, key=lambda e: e.get('reviews') or 0)
        example_url = best_e.get('url', '')
        anchor_rows_data.append((label, count, pct, avg_ems, example_url, key))

    anchor_rows_data.sort(key=lambda r: r[1], reverse=True)

    anchor_rows_html = ''
    for label, count, pct, avg_ems, example_url, key in anchor_rows_data:
        avg_ems_str = str(avg_ems) if avg_ems is not None else '—'
        link = f'<a href="{example_url}" target="_blank">View →</a>' if example_url else '—'
        anchor_rows_html += (
            f'<tr>'
            f'<td>{escape_html(label)}</td>'
            f'<td style="text-align:right">{count}</td>'
            f'<td style="text-align:right">{pct}%</td>'
            f'<td style="text-align:right">{avg_ems_str}</td>'
            f'<td>{link}</td>'
            f'</tr>'
        )

    anchor_table = (
        '<div class="mi-table-wrap"><table class="mi-table">'
        '<thead><tr>'
        '<th>Strategy</th>'
        '<th style="text-align:right">Count</th>'
        '<th style="text-align:right">% of listings</th>'
        '<th style="text-align:right">Avg Reviews</th>'
        '<th>Example</th>'
        '</tr></thead>'
        '<tbody>' + anchor_rows_html + '</tbody>'
        '</table></div>'
    )

    # Qualitative anchor insight
    honest_items = anchor_groups.get('honest', [])
    honest_ems_vals = [e.get('reviews') for e in honest_items if e.get('reviews') is not None]
    honest_avg_ems = round(statistics.mean(honest_ems_vals)) if honest_ems_vals else None

    # Find dominant anchor type (excluding honest)
    dominant = next((r for r in anchor_rows_data if r[5] != 'honest'), None)
    if dominant:
        dom_label, dom_count, dom_pct, dom_ems, _, dom_key = dominant
        if honest_avg_ems is not None and dom_ems is not None:
            ratio = dom_ems / honest_avg_ems if honest_avg_ems > 0 else 1
            if ratio >= 1.15:
                ems_comparison = f'is {round((ratio-1)*100)}% higher than honest listings (avg {honest_avg_ems} reviews). This suggests the lower displayed price drives meaningful click-through advantages'
            elif ratio <= 0.87:
                ems_comparison = f'is {round((1-ratio)*100)}% lower than honest listings (avg {honest_avg_ems} reviews). The data suggests anchoring does not guarantee higher volume — design and reviews matter more'
            else:
                ems_comparison = f'is similar to honest listings (avg {honest_avg_ems} reviews). The data does not show a clear advantage from anchoring — quality and design matter more than the search price'
            anchor_insight = (
                f'{escape_html(dom_label)} {"is" if dom_count == 1 else "are"} the dominant strategy '
                f'({dom_pct}% of listings), and their avg reviews of {dom_ems} {ems_comparison}.'
            )
        elif dom_ems is not None:
            anchor_insight = (
                f'{escape_html(dom_label)} {"is" if dom_count == 1 else "are"} the dominant strategy '
                f'({dom_pct}% of listings) with avg {dom_ems} reviews.'
            )
        else:
            anchor_insight = (
                f'{escape_html(dom_label)} {"is" if dom_count == 1 else "are"} the dominant strategy '
                f'({dom_pct}% of listings).'
            )
    else:
        anchor_insight = 'Most sellers in this niche use honest pricing with no anchor variants.'

    anchor_insight_p = f'<p class="mi-p">{anchor_insight}</p>'

    manipulation_section = (
        f'<h3 class="mi-h3">How search prices are manipulated</h3>'
        f'{illusion_warn}'
        f'{anchor_table}'
        f'{anchor_insight_p}'
    )

    # ── Part 5: Multi-Product Listing Strategy (preserved existing logic) ─────

    has_product_types = any(e.get('product_types') for e in comp_data)
    if not has_product_types:
        multi_product_section = ''
    else:
        multi  = [e for e in comp_data if e.get('multi_product_listing')]
        single = [e for e in comp_data if not e.get('multi_product_listing')]

        if len(multi) == 0:
            multi_product_section = ''
        else:
            multi_pct  = round(len(multi) / total * 100) if total else 0
            single_pct = 100 - multi_pct

            combos = Counter()
            for e in multi:
                pt = e.get('product_types')
                if pt and isinstance(pt, list) and len(pt) > 0:
                    combo = ' + '.join(sorted(pt))
                    combos[combo] += 1

            single_types = Counter()
            for e in single:
                pt = e.get('product_types')
                if pt and isinstance(pt, list):
                    for t in pt:
                        single_types[t] += 1

            stats_html = (
                f'<div class="ls-stats">'
                f'<div class="ls-stat-box">'
                f'<div class="ls-stat-num">{multi_pct}%</div>'
                f'<div class="ls-stat-label">use multi-product listings</div>'
                f'<div class="ls-stat-sub">{len(multi)} of {total} listings</div>'
                f'</div>'
                f'<div class="ls-stat-box">'
                f'<div class="ls-stat-num">{single_pct}%</div>'
                f'<div class="ls-stat-label">single product only</div>'
                f'<div class="ls-stat-sub">{len(single)} of {total} listings</div>'
                f'</div>'
                f'</div>'
            )

            combo_rows = ''
            for combo, count in combos.most_common():
                pct_of_multi = round(count / len(multi) * 100) if multi else 0
                combo_rows += (
                    f'<tr><td>{escape_html(combo)}</td>'
                    f'<td style="text-align:right">{count}</td>'
                    f'<td style="text-align:right">{pct_of_multi}%</td></tr>'
                )

            combo_table = (
                '<div class="mi-table-wrap"><table class="mi-table">'
                '<tr><th>Combo</th><th style="text-align:right">Count</th>'
                '<th style="text-align:right">% of multi-product</th></tr>'
                + combo_rows +
                '</table></div>'
            )

            top4_combos = [combo for combo, _ in combos.most_common(4)]
            combo_to_listing = {}
            for combo_key in top4_combos:
                parts_set = set(combo_key.split(' + '))
                candidates = []
                for e in multi:
                    pt = e.get('product_types')
                    if pt and isinstance(pt, list) and set(pt) == parts_set:
                        candidates.append(e)
                if candidates:
                    best = max(candidates, key=lambda e: e.get('reviews') or 0)
                    combo_to_listing[combo_key] = best

            example_cells = ''
            for combo_key in top4_combos:
                ex = combo_to_listing.get(combo_key)
                if not ex:
                    continue
                url   = ex.get('url', '')
                img   = ex.get('image_url', '')
                title = escape_html((ex.get('title') or '')[:80])
                price = escape_html(ex.get('price') or '')
                ems   = ex.get('reviews')
                ems_label   = f'{ems:,} reviews' if ems else '—'
                combo_label = escape_html(combo_key)
                example_cells += (
                    f'<div style="display:flex;flex-direction:column;gap:6px;">'
                    f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
                    f'letter-spacing:0.5px;color:var(--text-muted);">{combo_label}</div>'
                    f'<a class="mi-top-card" href="{url}" target="_blank">'
                    f'<img class="mi-top-card-img" src="{img}" alt="" loading="lazy">'
                    f'<div class="mi-top-card-body">'
                    f'<div class="mi-top-card-title">{title}</div>'
                    f'<div class="mi-top-card-meta">{ems_label} &middot; {price}</div>'
                    f'</div></a>'
                    f'</div>'
                )

            if example_cells:
                examples_section = (
                    '<h3 class="mi-h3">Example listings per combo</h3>'
                    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:12px 0 24px;">'
                    + example_cells +
                    '</div>'
                )
            else:
                examples_section = ''

            if single_types:
                top_singles = ', '.join(f'{t} ({c})' for t, c in single_types.most_common(5))
                single_note = f'<p class="dp-subtitle">Top single-product types: {escape_html(top_singles)}</p>'
            else:
                single_note = ''

            seo_warn = (
                '<div class="mi-warn"><strong>SEO note:</strong> Etsy\'s algorithm de-ranks listings that compete '
                'against themselves. Multi-product listings consolidate reviews but each garment type loses its own '
                'search slot. Separate listings per garment type rank higher individually.</div>'
            )

            multi_product_section = (
                f'<h3 class="mi-h3">Multi-Product Listing Strategy</h3>'
                f'<p class="dp-subtitle">How competitors structure their listings — single garment vs multi-product bundles</p>'
                f'{stats_html}'
                f'{combo_table}'
                f'{examples_section}'
                f'{single_note}'
                f'{seo_warn}'
            )

    return (
        f'\n<div class="dp-section">'
        f'\n<h2 class="mi-h2">Pricing &amp; Listing Strategy</h2>'
        f'{intro_p}'
        f'{price_band_section}'
        f'<div class="mi-hr"></div>'
        f'{manipulation_section}'
        f'<div class="mi-hr"></div>'
        f'{multi_product_section}'
        f'\n</div>'
    )


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
    warn_pre = []

    if lines and lines[0].startswith('# '):
        page_title = lines[0][2:].strip()
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            s = lines[i].strip()
            if s.startswith('>'):
                warn_pre.append(s[2:] if s.startswith('> ') else s[1:].strip())
            elif s:
                meta_lines.append(s)
            i += 1

    if meta_lines:
        meta_html = ' &nbsp;·&nbsp; '.join(inline(m, lookup) for m in meta_lines)
        parts.append('<div class="mi-meta">' + meta_html + '</div>')
    if warn_pre:
        parts.append('<div class="mi-warn">' + '<br>'.join(inline(l, lookup) for l in warn_pre if l) + '</div>')

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

        elif line.startswith('>'):
            warn_lines = []
            while i < len(lines) and lines[i].startswith('>'):
                stripped = lines[i][2:] if lines[i].startswith('> ') else lines[i][1:].strip()
                if stripped:
                    warn_lines.append(stripped)
                i += 1
            if warn_lines:
                parts.append('<div class="mi-warn">' + '<br>'.join(inline(l, lookup) for l in warn_lines) + '</div>')

        elif line.strip() == '':
            i += 1

        else:
            parts.append('<p class="mi-p">' + inline(line, lookup) + '</p>')
            i += 1

    return page_title, '\n'.join(parts)


# ── HTML builder ───────────────────────────────────────────────────────────────

def build_top_strip(comp_data, ems_reliable=False):
    """Horizontal scrollable strip of top listings."""
    top = sorted(
        [e for e in comp_data if e.get('image_url')],
        key=lambda e: e.get('reviews') or 0, reverse=True
    )[:8]
    if not top:
        return ''
    cards = ''
    for item in top:
        if item.get('reviews'):
            meta_left = f'{item["reviews"]:,} reviews'
        else:
            meta_left = 'No reviews'
        title = item['title'][:55] + ('…' if len(item['title']) > 55 else '')
        cards += (
            '<a class="mi-top-card" href="' + item['url'] + '" target="_blank">'
            + '<img class="mi-top-card-img" src="' + item['image_url'] + '" alt="" loading="lazy">'
            + '<div class="mi-top-card-body">'
            + '<div class="mi-top-card-title">' + title + '</div>'
            + '<div class="mi-top-card-meta">' + meta_left + ' &middot; ' + item.get('price', '') + '</div>'
            + '</div></a>'
        )
    return (
        '<div class="mi-top-strip">'
        + '<div class="mi-top-strip-label">Top performing listings in this niche</div>'
        + '<div class="mi-top-scroll">' + cards + '</div>'
        + '</div>'
    )




def build_shop_intel_tab(watchlist, velocity=None):
    """Build the Shop Intelligence tab — single merged table combining watchlist + velocity data."""
    if not watchlist:
        return (
            '\n<div id="tab-shops" class="tab-panel">'
            '\n  <div class="si-outer"><p class="si-empty">No shop-watchlist.json found. '
            'Run: <code>python3 scripts/research-shops.py --niche &lt;niche&gt;</code></p></div>'
            '\n</div>'
        )

    shops = [s for s in watchlist if 'error' not in s]
    shops.sort(key=lambda s: s.get('estimated_monthly_sales') or s.get('method1_lifetime_avg_monthly') or 0, reverse=True)

    # Build velocity lookup by shop name
    vel_map = {}
    if velocity:
        for v in velocity:
            key = v.get('shop') or v.get('shop_name', '')
            vel_map[key] = v

    trend_icon  = {'growing': '↑', 'declining': '↓', 'stable': '→', 'unknown': '–'}
    trend_color = {'growing': 'si-trend-up', 'declining': 'si-trend-down', 'stable': 'si-trend-stable', 'unknown': 'si-trend-unknown'}
    conf_color  = {'high': 'si-conf-high', 'medium': 'si-conf-med', 'low': 'si-conf-low'}

    rows = ''
    for s in shops:
        name        = s.get('shop_name', '—')
        url         = s.get('etsy_url', '#')
        m2          = s.get('method2_current_momentum')
        m1          = s.get('method1_lifetime_avg_monthly')
        m2_window   = s.get('method2_window') or ''
        headline    = m2 or m1 or '—'
        trend       = s.get('trend_signal') or 'unknown'
        conf        = s.get('confidence') or 'low'
        total_sales = s.get('total_sales')
        total_str   = f'{total_sales:,}' if total_sales else '—'
        months      = s.get('months_active') or '—'
        m1_str      = f'{m1:,}' if m1 else '—'
        m2_str      = (f'<span title="{m2_window}">{m2:,}</span>'
                       f'<div class="si-window">{m2_window}</div>') if m2 else '—'
        headline_str = f'{headline:,}' if isinstance(headline, int) else headline
        notes       = s.get('confidence_notes') or []
        notes_html  = ('<div class="si-notes">' + ' &middot; '.join(notes[:2]) + '</div>') if notes else ''

        # Velocity columns — inline from vel_map, no separate table
        vel      = vel_map.get(name, {})
        r7       = vel.get('reviews_7d')
        momentum = vel.get('momentum_ratio')
        r7_str   = f'{r7:,}' if isinstance(r7, int) else '—'

        if momentum is not None:
            if momentum >= 1.5:   mc = '#C2410C'; ml = f'{momentum:.2f}x 🔥'
            elif momentum >= 1.1: mc = '#15803d'; ml = f'{momentum:.2f}x ↑'
            elif momentum >= 0.9: mc = '#6b7280'; ml = f'{momentum:.2f}x →'
            else:                 mc = '#1d4ed8'; ml = f'{momentum:.2f}x ↓'
            mom_str = f'<span style="font-weight:700;color:{mc}">{ml}</span>'
        else:
            mom_str = '—'

        trend_cls = trend_color.get(trend, 'si-trend-unknown')
        conf_cls  = conf_color.get(conf, 'si-conf-low')

        rows += f'''<tr>
  <td class="si-shop-cell"><a href="{url}" target="_blank" class="si-shop-link">{name} &#8599;</a>{notes_html}</td>
  <td class="si-num si-headline">{headline_str}</td>
  <td class="si-num">{m1_str}</td>
  <td class="si-num">{m2_str}</td>
  <td class="si-num">{r7_str}</td>
  <td class="si-num">{mom_str}</td>
  <td><span class="si-trend {trend_cls}">{trend_icon.get(trend,"–")} {trend.capitalize()}</span></td>
  <td><span class="si-conf {conf_cls}">{conf.capitalize()}</span></td>
  <td class="si-num si-muted">{total_str}</td>
  <td class="si-num si-muted">{months}</td>
</tr>'''

    scrape_date = velocity[0].get('scrape_date', '') if velocity else ''
    scrape_note = f' &nbsp;·&nbsp; <strong>Velocity scraped:</strong> {scrape_date}' if scrape_date else ''

    return (
        '\n<div id="tab-shops" class="tab-panel">'
        '\n<div class="si-outer">'
        '\n<div class="si-header">'
        '\n  <h1>Shop Intelligence</h1>'
        '\n  <p class="si-subtitle">Monthly sales estimates, current momentum, and confidence signals per competitor shop. '
        '<strong>Est/mo</strong> uses M2 (5-month review-rate window) as primary signal; falls back to M1 (lifetime average) if M2 is unavailable. '
        'All estimates assume 1-in-7 buyers leave a review (~14% review rate — apparel industry proxy). '
        'Review velocity and momentum columns are inline in this table. See legend below for methodology.</p>'
        '\n</div>'
        '\n<div class="si-table-wrap"><table class="si-table">'
        '\n<thead><tr>'
        '<th>Shop</th>'
        '<th title="Est monthly sales — M2 primary, M1 fallback. Assumes 1-in-7 buyers leave a review (~14% review rate).">Est/mo</th>'
        '<th title="M1 Lifetime avg: total Etsy lifetime sales ÷ months active. Historical average — not current pace. May use \'X years on Etsy\' as approximation if exact open date unavailable (flagged as relative).">M1 Lifetime</th>'
        '<th title="M2 Current pace: review rate over 5-month window × 30 × 7. Best signal for recent momentum. Hover cell for window detail.">M2 Current</th>'
        '<th title="Reviews left in the last 7 days. Confirms shop is actively selling this week.">7d Reviews</th>'
        '<th title="Momentum: 7d reviews ÷ (30d reviews ÷ 4). 1.0x = flat pace. Above 1.0x = accelerating vs 30d baseline; below = slowing. Note: 7d window is included in the 30d count, so true acceleration is slightly understated.">Momentum</th>'
        '<th title="Trend: M2 ÷ M1. ↑ Growing ≥1.3x · → Stable 0.6–1.3x · ↓ Declining ≤0.6x · Unknown if M1 missing.">Trend</th>'
        '<th title="Confidence: M1 vs M2 agreement. High = within 40% OR rapid growth (M2 ≥2x M1). Medium = 40–70% divergence or only one signal available. Low = &gt;70% divergence without clear growth explanation.">Confidence</th>'
        '<th title="Total lifetime sales across all products on the Etsy shop page. Not monthly.">Lifetime Sales</th>'
        '<th title="Months since shop opened on Etsy. Approximate if derived from \'X years on Etsy\' display text.">Age (mo)</th>'
        '</tr></thead>'
        '\n<tbody>' + rows + '</tbody>'
        '\n</table></div>'
        '\n<div class="si-legend">'
        '<strong>Est/mo</strong> M2 primary, M1 fallback — both assume 1-in-7 buyers leave a review (~14% rate; apparel industry proxy) &nbsp;·&nbsp; '
        '<strong>M1 Lifetime</strong> total lifetime Etsy sales ÷ months active — historical average, not current pace. May use "X years on Etsy" as approximation when exact open date is unavailable (precision flagged as relative in source data) &nbsp;·&nbsp; '
        '<strong>M2 Current</strong> review rate × 30 × 7 over 5-month window — best signal for what the shop is doing right now &nbsp;·&nbsp; '
        '<strong>7d Reviews</strong> reviews in the last 7 days — pulse check; confirms the shop is actively selling this week &nbsp;·&nbsp; '
        '<strong>Momentum</strong> 7d reviews ÷ (30d reviews ÷ 4) — 1.0x = flat pace; above = accelerating vs 30d baseline; below = slowing. '
        '&gt;1.5x 🔥 Surging &nbsp;·&nbsp; 1.1–1.5x ↑ Growing &nbsp;·&nbsp; 0.9–1.1x → Stable &nbsp;·&nbsp; &lt;0.9x ↓ Cooling. '
        '<em>Caveat: the 7-day window is included in the 30-day count, so true acceleration is slightly understated.</em> &nbsp;·&nbsp; '
        '<strong>Trend</strong> M2 ÷ M1 — ↑ Growing ≥1.3x · → Stable 0.6–1.3x · ↓ Declining ≤0.6x · Unknown if M1 missing &nbsp;·&nbsp; '
        '<strong>Confidence</strong> M1 vs M2 agreement: '
        'High = signals within 40% OR rapid growth (M2 ≥2x M1, flagged "Rapid growth detected") &nbsp;·&nbsp; '
        'Medium = 40–70% divergence or only one signal available &nbsp;·&nbsp; '
        'Low = &gt;70% divergence without a clear growth explanation &nbsp;·&nbsp; '
        '<strong>Age (mo)</strong> months since shop opened; approximate when derived from "X years on Etsy" display text (precision: relative) &nbsp;·&nbsp; '
        '<em>Review rate: M1/M2 use ~14% (1-in-7 buyers) for watchlist estimates; analyze-shop-velocity.py uses 10% by default — override with --review-rate if you want consistency.</em>'
        f'{scrape_note}'
        '</div>'
        '\n</div>'
        '\n</div>'
    )



def build_html(niche, comp_data, insights_md, watchlist, date_str, ems_reliable=True, patterns_config=None, velocity=None):
    # Deduplicate by listing ID
    seen_ids: set = set()
    deduped = []
    for e in comp_data:
        eid = e.get('id')
        if eid not in seen_ids:
            seen_ids.add(eid)
            deduped.append(e)
    comp_data = deduped

    # Nullify EMS/RPM when no date anchor exists
    if not ems_reliable:
        comp_data = [{**e, 'estimated_monthly_sales': None, 'reviews_per_month': None} for e in comp_data]

    niche_title = niche_to_title(niche)
    shirt_count = sum(1 for e in comp_data if e.get('is_shirt'))
    total = len(comp_data)
    data_json = json.dumps(comp_data, separators=(',', ':'))
    lookup = {e['id']: e for e in comp_data if e.get('id')}
    top_strip = build_top_strip(comp_data, ems_reliable)
    shop_intel_tab = build_shop_intel_tab(watchlist, velocity)

    if insights_md:
        insights_title, insights_body = md_to_html(insights_md, lookup)
    else:
        insights_title = 'Market Insights'
        insights_body = '<p class="mi-p" style="color:var(--text-muted)">No market-insights.md found for this project.</p>'

    # Inject design patterns + listing strategy visuals after the Niche Verdict section (before next h2)
    ls_section = build_listing_pricing_strategy_section(comp_data)

    if patterns_config:
        dp_section = build_design_patterns_section(comp_data, patterns_config)
    else:
        dp_section = ''

    # Replace computed-section placeholders in rendered markdown
    insights_body = insights_body.replace(
        '<p class="mi-p">{{COMPUTED_BLANKS}}</p>',
        build_garment_blanks_section(comp_data)
    )
    insights_body = insights_body.replace(
        '<p class="mi-p">{{COMPUTED_PRINT_METHODS}}</p>',
        build_print_methods_section(comp_data)
    )

    combined = dp_section + ls_section

    if combined:
        h2 = '<h2 class="mi-h2">'
        parts = insights_body.split(h2, 2)
        if len(parts) == 3:
            # parts[1] = Niche Verdict heading + content, parts[2] = rest
            insights_body = parts[0] + h2 + parts[1] + combined + h2 + parts[2]
        else:
            insights_body = combined + insights_body

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
  .est-sales-badge {{
    display: inline-flex; align-items: center;
    background: var(--blue-light); color: #1E40AF; border: 1px solid #BFDBFE;
    font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 4px;
    white-space: nowrap;
  }}
  .fav-badge {{
    display: inline-flex; align-items: center; gap: 3px;
    background: var(--green-light); color: #0D5C2E; border: 1px solid #A8D8BB;
    font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 4px;
    white-space: nowrap;
  }}
  .signals-row {{ display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }}
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
  .tag-shirt    {{ background: var(--green-light); color: #0D5C2E; border: 1px solid #A8D8BB; }}
  .tag-type     {{ background: var(--green-light); color: #0D5C2E; border: 1px solid #A8D8BB; }}
  .tag-inferred {{ background: var(--blue-light);  color: #1E40AF; border: 1px solid #BFDBFE; }}
  .tag-mockup   {{ background: #F3F4F6; color: #6B7280; border: 1px solid #D1D5DB; }}
  .design-style {{ font-size: 12px; color: var(--text-secondary); line-height: 1.5; }}
  .key-phrases {{ display: flex; flex-wrap: wrap; gap: 4px; }}
  .phrase {{
    font-size: 11px; color: var(--text-muted); background: var(--bg);
    border: 1px solid var(--border); padding: 2px 7px; border-radius: 4px;
  }}
  .shop-row {{ font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 5px; margin-top: auto; }}
  .shop-link {{ color: inherit; text-decoration: none; }}
  .shop-link:hover {{ color: var(--coral); text-decoration: underline; text-underline-offset: 2px; }}
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
  .mi-warn {{
    background: #FEF3C7; border: 1px solid #FCD34D; border-left: 3px solid #F59E0B;
    border-radius: 8px; padding: 10px 14px; margin: 12px 0;
    color: #92400E; font-size: 13px; line-height: 1.65;
  }}
  .mi-warn strong {{ color: #78350F; }}

  /* ══ SHOP INTELLIGENCE TAB ══ */
  .si-outer {{ max-width: 1100px; margin: 0 auto; padding: 36px 32px 72px; }}
  .si-header {{ margin-bottom: 24px; padding-bottom: 18px; border-bottom: 2px solid var(--coral-light); }}
  .si-header h1 {{ font-size: 22px; font-weight: 700; letter-spacing: -0.4px; }}
  .si-subtitle {{ font-size: 13px; color: var(--text-secondary); margin-top: 6px; line-height: 1.5; }}
  .si-empty {{ color: var(--text-muted); font-size: 14px; padding: 40px 0; }}
  .si-table-wrap {{ overflow-x: auto; border-radius: 10px; border: 1px solid var(--border); }}
  .si-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .si-table thead tr {{ background: var(--bg); }}
  .si-table th {{
    padding: 10px 14px; text-align: left; font-weight: 600; font-size: 12px;
    color: var(--text-secondary); border-bottom: 1px solid var(--border);
    white-space: nowrap; cursor: default;
  }}
  .si-table th[title] {{ text-decoration: underline dotted; text-underline-offset: 3px; }}
  .si-table td {{ padding: 12px 14px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  .si-table tbody tr:last-child td {{ border-bottom: none; }}
  .si-table tbody tr:hover {{ background: #FAFAF8; }}
  .si-shop-cell {{ min-width: 180px; }}
  .si-shop-link {{
    font-weight: 600; color: var(--text-primary); text-decoration: none; font-size: 13px;
  }}
  .si-shop-link:hover {{ color: var(--coral); }}
  .si-notes {{ font-size: 11px; color: var(--text-muted); margin-top: 3px; line-height: 1.4; }}
  .si-window {{ font-size: 10px; color: var(--text-muted); margin-top: 2px; }}
  .si-num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .si-headline {{ font-size: 15px; font-weight: 700; color: var(--text-primary); }}
  .si-muted {{ color: var(--text-muted); }}
  .si-trend {{
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 12px; font-weight: 600; padding: 3px 9px; border-radius: 999px;
    white-space: nowrap;
  }}
  .si-trend-up      {{ background: var(--green-light);  color: #0D5C2E; border: 1px solid #A8D8BB; }}
  .si-trend-down    {{ background: #FEE2E2;              color: #B91C1C; border: 1px solid #FCA5A5; }}
  .si-trend-stable  {{ background: var(--blue-light);   color: #1E40AF; border: 1px solid #BFDBFE; }}
  .si-trend-unknown {{ background: #F3F4F6;              color: #6B7280; border: 1px solid #D1D5DB; }}
  .si-conf {{
    display: inline-block; font-size: 11px; font-weight: 700;
    padding: 2px 8px; border-radius: 4px; white-space: nowrap;
  }}
  .si-conf-high {{ background: var(--green-light); color: #0D5C2E; }}
  .si-conf-med  {{ background: var(--amber-light);  color: var(--amber); }}
  .si-conf-low  {{ background: #FEE2E2;              color: #B91C1C; }}
  .si-legend {{
    margin-top: 14px; font-size: 12px; color: var(--text-muted); line-height: 1.7;
  }}

  /* ══ SHOP VELOCITY (Shop Intel tab, section 2) ══ */
  .sv-section {{ margin-top: 40px; padding-top: 32px; border-top: 2px solid var(--coral-light); }}
  .sv-section h2 {{ font-size: 17px; font-weight: 700; letter-spacing: -0.3px; margin-bottom: 4px; }}
  .sv-subtitle {{ font-size: 13px; color: var(--text-secondary); margin-bottom: 18px; line-height: 1.5; }}
  .sv-table-wrap {{ overflow-x: auto; border-radius: 10px; border: 1px solid var(--border); }}
  .sv-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .sv-table thead tr {{ background: var(--bg); }}
  .sv-table th {{ padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-secondary);
    border-bottom: 1px solid var(--border); white-space: nowrap; }}
  .sv-table th.sv-right {{ text-align: right; }}
  .sv-table td {{ padding: 12px 14px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
  .sv-table tbody tr:last-child td {{ border-bottom: none; }}
  .sv-table tbody tr:hover {{ background: #FAFAF8; }}
  .sv-right {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .sv-shop-link {{ font-weight: 600; color: var(--text-primary); text-decoration: none; }}
  .sv-shop-link:hover {{ color: var(--coral); }}
  .sv-momentum {{ font-weight: 700; }}
  .sv-momentum-surge  {{ color: #C2410C; }}
  .sv-momentum-up     {{ color: #0D5C2E; }}
  .sv-momentum-stable {{ color: #1E40AF; }}
  .sv-momentum-down   {{ color: var(--text-muted); }}
  .sv-trend {{ display: inline-block; padding: 2px 8px; border-radius: 20px;
    font-size: 11px; font-weight: 600; white-space: nowrap; }}
  .sv-trend-surge  {{ background: #FFF0EB; color: #C2410C; border: 1px solid #FDBA74; }}
  .sv-trend-up     {{ background: var(--green-light); color: #0D5C2E; border: 1px solid #A8D8BB; }}
  .sv-trend-stable {{ background: var(--blue-light); color: #1E40AF; border: 1px solid #BFDBFE; }}
  .sv-trend-down   {{ background: #F3F4F6; color: #6B7280; border: 1px solid #D1D5DB; }}
  .sv-legend {{ margin-top: 14px; font-size: 12px; color: var(--text-muted); line-height: 1.7; }}

  /* ══ DESIGN PATTERNS (Tab 1 section) ══ */
  .dp-section {{ margin-bottom: 8px; }}
  .dp-subtitle {{ font-size: 12px; color: var(--text-muted); margin: 4px 0 20px; }}
  .dp-row {{ margin-bottom: 32px; }}
  .dp-row-header {{ display: flex; align-items: baseline; gap: 10px;
                    border-left: 3px solid var(--dp-color); padding-left: 10px; }}
  .dp-row-label {{ font-size: 15px; font-weight: 700; }}
  .dp-row-count {{ font-size: 12px; color: var(--text-muted); }}
  .dp-row-desc {{ font-size: 12px; color: var(--text-secondary); margin-top: 4px; padding-left: 13px; }}
  .dp-scroll {{ display: flex; overflow-x: auto; gap: 12px; padding: 10px 0 14px;
                scrollbar-width: thin; scrollbar-color: var(--border-dark) transparent; }}
  .dp-scroll::-webkit-scrollbar {{ height: 5px; }}
  .dp-scroll::-webkit-scrollbar-thumb {{ background: var(--border-dark); border-radius: 99px; }}
  .dp-empty {{ font-size: 12px; color: var(--text-muted); padding: 20px 0; }}
  .dp-card {{ width: 230px; flex-shrink: 0; border-radius: 10px; overflow: hidden;
              background: var(--surface); border: 1px solid var(--border);
              text-decoration: none; color: inherit; display: block;
              transition: transform 0.15s ease, box-shadow 0.15s ease; }}
  .dp-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.12); }}
  .dp-card-img {{ position: relative; width: 100%; height: 220px; background: #f3f4f6; }}
  .dp-card-img img {{ width: 100%; height: 220px; object-fit: cover; display: block; }}
  .dp-badge-ems {{ position: absolute; top: 4px; right: 4px; font-size: 10px; font-weight: 700;
                   padding: 2px 7px; border-radius: 4px; color: #fff; }}
  .dp-badge-best {{ position: absolute; top: 4px; left: 4px; font-size: 9px;
                    background: #f59e0b; color: #fff; padding: 2px 6px; border-radius: 3px; font-weight: 700; }}
  .dp-card-body {{ padding: 8px 10px 10px; }}
  .dp-card-title {{ font-size: 12px; font-weight: 600; color: var(--text-primary);
                    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
                    overflow: hidden; line-height: 1.45; margin-bottom: 4px; }}
  .dp-card-meta {{ font-size: 10px; color: var(--text-secondary); }}

  /* ══ LISTING STRATEGY (Tab 1 section) ══ */
  .ls-stats {{ display: flex; gap: 20px; margin: 16px 0; flex-wrap: wrap; }}
  .ls-stat-box {{
    flex: 1; min-width: 160px; background: var(--surface);
    border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 20px; text-align: center;
  }}
  .ls-stat-num {{ font-size: 32px; font-weight: 700; color: var(--coral); line-height: 1; }}
  .ls-stat-label {{ font-size: 12px; color: var(--text-muted); margin-top: 6px; }}
  .ls-stat-sub {{ font-size: 11px; color: var(--text-muted); margin-top: 2px; }}


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
  <button class="tab-btn" onclick="switchTab('shops',this)">🏪 Shop Intelligence</button>
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
    <option value="reviews" selected>Most Reviews</option>
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

function printTag(m, confirmed) {
  if (!m||m==='unknown') return '';
  const labels = {'DTG':'DTG','screen print':'Screen Print','HTV':'HTV','embroidery':'Embroidery','sublimation':'Sublimation'};
  const label = labels[m] || m;
  const cls = confirmed ? 'tag-type' : 'tag-inferred';
  return '<span class="tag ' + cls + '">' + label + '</span>';
}

function parsePrice(p) { return parseFloat((p||'0').replace(/[^0-9.]/g,''))||0; }

function card(item) {
  const shirt = item.is_shirt;
  const revBadge = item.reviews > 0
    ? '<div class="reviews-badge"><span class="star">&#9733;</span> ' + item.reviews.toLocaleString() + '</div>' : '';
  const shirtBadge = shirt ? '<div class="shirt-badge">Shirt</div>' : '';
  const estSales = '';
  const favBadge = (item.favorites_count || 0) > 0
    ? '<span class="fav-badge">&#9829; ' + item.favorites_count.toLocaleString() + ' favorites</span>' : '';
  const revLine = item.reviews > 0
    ? '<span class="reviews-text"><strong>' + item.reviews.toLocaleString() + '</strong> reviews &middot; &#9733; ' + item.rating + '</span>'
    : '<span class="reviews-text" style="color:var(--text-muted)">No reviews yet &middot; &#9733; ' + item.rating + '</span>';
  const phrases = (item.key_phrases||[]).map(p=>'<span class="phrase">'+p+'</span>').join('');
  const signalParts = [
    ...(item.demand_signals||[]).map(s=>'<span class="demand-signal">&#128293; '+s+'</span>'),
    estSales,
    favBadge
  ].filter(Boolean);
  const signalsRow = signalParts.length > 0 ? '<div class="signals-row">' + signalParts.join('') + '</div>' : '';
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
    + printTag(item.print_method, item.print_method_confirmed)
    + (item.blank ? '<span class="tag tag-type">' + item.blank + '</span>' : '')
    + (item.mockup_style && item.mockup_style !== 'unknown' ? '<span class="tag tag-mockup">&#128247; ' + item.mockup_style.replace(/-/g,' ') + '</span>' : '')
    + '</div>'
    + '<div class="design-style">' + item.design_style + '</div>'
    + (phrases ? '<div class="key-phrases">' + phrases + '</div>' : '')
    + signalsRow
    + '<div class="shop-row"><svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="7" width="12" height="8" rx="1"/><path d="M5 7V5a3 3 0 116 0v2"/></svg>'
    + (item.shop_name ? '<a href="https://www.etsy.com/shop/' + item.shop_name + '" target="_blank" class="shop-link">' + item.shop_name + ' &#8599;</a>' : '—') + '</div>'
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

<footer style="max-width:1200px;margin:40px auto 24px;padding:0 20px;">
  <details style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:0;">
    <summary style="padding:14px 18px;cursor:pointer;font-size:13px;font-weight:600;color:#6B7280;user-select:none;">
      &#128202; How these numbers are calculated
    </summary>
    <div style="padding:6px 18px 22px;font-size:12.5px;color:#374151;line-height:1.7;">

      <!-- ── SECTION 1: LISTING LEVEL ── -->
      <p style="margin:14px 0 8px;font-size:13px;font-weight:700;color:#111;">📋 Listing-level  <span style="font-weight:400;font-size:12px;color:#6B7280;">(🔍 Competitor Report tab)</span></p>
      <table style="border-collapse:collapse;width:100%;font-size:12px;">
        <tr style="background:#F3F4F6;">
          <td style="padding:7px 10px;font-weight:600;white-space:nowrap;">favorites_per_review</td>
          <td style="padding:7px 10px;">favorites_count &divide; reviews. &nbsp;<strong>&gt;5.0</strong> = high saves, low conversion (people browse but don&rsquo;t buy) &nbsp;&middot;&nbsp; <strong>1&ndash;5</strong> = healthy active listing &nbsp;&middot;&nbsp; <strong>&lt;1.0</strong> = legacy listing, interest fading.</td>
        </tr>
      </table>

      <!-- ── SECTION 2: SHOP LEVEL ── -->
      <p style="margin:22px 0 8px;font-size:13px;font-weight:700;color:#111;">🏪 Shop-level  <span style="font-weight:400;font-size:12px;color:#6B7280;">(🏪 Shop Intelligence tab)</span></p>

      <p style="margin:0 0 6px;font-size:12px;font-weight:600;color:#374151;">Signals — two independent estimates cross-checked against each other</p>
      <table style="border-collapse:collapse;width:100%;font-size:12px;">
        <tr style="background:#F3F4F6;">
          <td style="padding:7px 10px;font-weight:600;white-space:nowrap;width:170px;">M1 — Lifetime avg</td>
          <td style="padding:7px 10px;"><strong>total_sales &divide; months_active.</strong> Scraped from the shop page. Stable signal but lags &mdash; a fast-growing shop will look underestimated here.</td>
        </tr>
        <tr>
          <td style="padding:7px 10px;font-weight:600;white-space:nowrap;">M2 — Current pace</td>
          <td style="padding:7px 10px;"><strong>(review_count &divide; span_days) &times; 30 &times; 7.</strong> Scrapes up to 20 pages of the shop&rsquo;s /reviews, stopping when the oldest review reaches 5 months ago. Counts every review occurrence including multiple reviews on the same day. Calculates a daily rate, projects to 30 days, multiplies by 7. 5-month window smooths seasonal spikes (Father&rsquo;s Day, Christmas). Most responsive signal &mdash; reflects what the shop is doing <em>right now</em>.</td>
        </tr>
        <tr style="background:#F3F4F6;">
          <td style="padding:7px 10px;font-weight:600;white-space:nowrap;">Headline (Est/mo)</td>
          <td style="padding:7px 10px;">Priority order: <strong>M2 &rarr; M1.</strong> M2 used first (most current). Falls back to M1 if too few reviews were scraped.</td>
        </tr>
      </table>

      <p style="margin:14px 0 6px;font-size:12px;font-weight:600;color:#374151;">Trend &mdash; is the shop accelerating or slowing down?</p>
      <p style="margin:0 0 8px;font-size:12px;color:#6B7280;">Formula: <strong>M2 &divide; M1</strong>. Compares current pace to lifetime average.</p>
      <table style="border-collapse:collapse;width:100%;font-size:12px;">
        <tr>
          <td style="padding:7px 10px;font-weight:600;white-space:nowrap;width:170px;"><span style="background:#D1FAE5;color:#065F46;padding:2px 9px;border-radius:999px;">↑ Growing</span></td>
          <td style="padding:7px 10px;">M2 &divide; M1 &ge; 1.3 &mdash; selling 30%+ faster than lifetime average. Accelerating.</td>
        </tr>
        <tr style="background:#F3F4F6;">
          <td style="padding:7px 10px;font-weight:600;white-space:nowrap;"><span style="background:#DBEAFE;color:#1E40AF;padding:2px 9px;border-radius:999px;">→ Stable</span></td>
          <td style="padding:7px 10px;">M2 &divide; M1 between 0.6 and 1.3 &mdash; current pace matches historical average.</td>
        </tr>
        <tr>
          <td style="padding:7px 10px;font-weight:600;white-space:nowrap;"><span style="background:#FEE2E2;color:#B91C1C;padding:2px 9px;border-radius:999px;">↓ Declining</span></td>
          <td style="padding:7px 10px;">M2 &divide; M1 &le; 0.6 &mdash; selling 40%+ slower than lifetime average. Slowing down.</td>
        </tr>
        <tr style="background:#F3F4F6;">
          <td style="padding:7px 10px;font-weight:600;white-space:nowrap;"><span style="background:#F3F4F6;color:#6B7280;padding:2px 9px;border-radius:999px;border:1px solid #D1D5DB;">– Unknown</span></td>
          <td style="padding:7px 10px;">M2 or M1 unavailable &mdash; cannot compute ratio.</td>
        </tr>
      </table>

      <p style="margin:14px 0 6px;font-size:12px;font-weight:600;color:#374151;">Confidence &mdash; how much do M1 and M2 agree?</p>
      <p style="margin:0 0 8px;font-size:12px;color:#6B7280;">Measured as: <strong>(max &minus; min) &divide; max</strong>. The further M1 and M2 diverge, the lower the confidence. If only one signal is available, confidence is capped at Medium.</p>
      <table style="border-collapse:collapse;width:100%;font-size:12px;">
        <tr style="background:#F3F4F6;">
          <td style="padding:7px 10px;font-weight:600;white-space:nowrap;width:170px;"><span style="background:#D1FAE5;color:#065F46;padding:2px 9px;border-radius:4px;">High</span></td>
          <td style="padding:7px 10px;">M1 and M2 diverge &lt;40%, or M2 &ge; 2&times; M1 (rapid growth detected) &mdash; estimate is reliable.</td>
        </tr>
        <tr>
          <td style="padding:7px 10px;font-weight:600;white-space:nowrap;"><span style="background:#FEF3C7;color:#92400E;padding:2px 9px;border-radius:4px;">Medium</span></td>
          <td style="padding:7px 10px;">Signals diverge 40&ndash;70%. Directionally correct &mdash; use with caution.</td>
        </tr>
        <tr style="background:#F3F4F6;">
          <td style="padding:7px 10px;font-weight:600;white-space:nowrap;"><span style="background:#FEE2E2;color:#B91C1C;padding:2px 9px;border-radius:4px;">Low</span></td>
          <td style="padding:7px 10px;">Signals diverge &gt;70% or only one signal available. Use the lower value as a conservative estimate.</td>
        </tr>
      </table>

      <p style="margin:18px 0 0;font-size:11.5px;color:#9CA3AF;border-top:1px solid #E5E7EB;padding-top:12px;">
        All estimates use publicly visible Etsy data. Etsy does not share real sales figures with third parties &mdash; no tool (eRank, Alura, Sale Samurai) has access to actual transaction data. These estimates use the same review-based methodology those tools use.
      </p>
    </div>
  </details>
</footer>

</body>
</html>"""

    return head + topbar + insights_tab + competitors_tab + shop_intel_tab + script


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--niche', required=True, help='Niche folder name, e.g. personalized-gift-for-dad')
    args = parser.parse_args()

    json_path      = BASE_DIR / 'projects' / args.niche / '01-research' / 'competitors.json'
    insights_path  = BASE_DIR / 'projects' / args.niche / '01-research' / 'market-insights.md'
    watchlist_path = BASE_DIR / 'projects' / args.niche / '01-research' / 'shop-watchlist.json'
    velocity_path  = BASE_DIR / 'projects' / args.niche / '01-research' / 'shop-velocity.json'
    patterns_path  = BASE_DIR / 'projects' / args.niche / '01-research' / 'patterns-config.json'
    dates_path     = BASE_DIR / 'projects' / args.niche / '01-research' / 'scrapes' / 'listing-dates.json'
    out_path       = BASE_DIR / 'projects' / args.niche / '01-research' / 'competitor-report.html'

    if not json_path.exists():
        print(f"✗ Not found: {json_path}")
        return

    comp_data       = json.load(open(json_path))
    insights_md     = insights_path.read_text() if insights_path.exists() else None
    watchlist       = json.loads(watchlist_path.read_text()) if watchlist_path.exists() else []
    velocity        = json.loads(velocity_path.read_text()) if velocity_path.exists() else []
    patterns_config = json.loads(patterns_path.read_text()) if patterns_path.exists() else None

    # Refresh Section 6 + 7 from live data before rendering
    if insights_md and patterns_config:
        insights_md = update_demand_signals_in_md(insights_md, comp_data, patterns_config)
    if insights_md:
        insights_md = update_listings_to_watch_in_md(insights_md, comp_data)
    if insights_md:
        insights_path.write_text(insights_md)
    date_str        = datetime.date.today().isoformat()

    ems_reliable = False

    html = build_html(args.niche, comp_data, insights_md, watchlist, date_str, ems_reliable, patterns_config, velocity)
    out_path.write_text(html)

    shirt_count = sum(1 for e in comp_data if e.get('is_shirt'))
    print(f"✓ Generated {out_path}")
    print(f"  {len(comp_data)} listings · {shirt_count} shirts · {date_str}")
    print(f"  Market insights:   {'✓ included' if insights_md else '✗ market-insights.md not found'}")
    print(f"  Design patterns:   {'✓ ' + str(len(patterns_config.get('patterns',[]))) + ' patterns' if patterns_config else '✗ patterns-config.json not found'}")
    print(f"  Shop intelligence: {'✓ ' + str(len(watchlist)) + ' shops' if watchlist else '✗ shop-watchlist.json not found'}")
    print(f"  Review velocity:   {'✓ ' + str(len(velocity)) + ' shops' if velocity else '✗ shop-velocity.json not found — run analyze-shop-velocity.py'}")


if __name__ == '__main__':
    main()
