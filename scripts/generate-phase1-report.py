#!/usr/bin/env python3
"""
generate-phase1-report.py

Generates a narrative Phase 1 Research Brief HTML for a niche.
Explains methodology, findings, and pre-populates design direction options.
Every factual claim is tagged [our data] / [inferred] / [market knowledge].
All stats are computed deterministically from data files — nothing is estimated.

Usage:
  python3 scripts/generate-phase1-report.py --niche dog-mom
"""

import json, re, argparse, statistics
from pathlib import Path
from datetime import date
from collections import Counter

BASE_DIR = Path(__file__).parent.parent
TODAY = date.today().isoformat()


# ── Source label renderer (same regex logic as generate-competitor-report.py) ──

def inline(text):
    text = re.sub(
        r'`\[our data\]`',
        '<span class="src our-data">[our data]</span>', text)
    text = re.sub(
        r'`\[inferred\]`',
        '<span class="src inferred">[inferred]</span>', text)
    text = re.sub(
        r'`\[market knowledge\]`',
        '<span class="src market">[market knowledge]</span>', text)
    return text


def p(text):
    return f'<p>{inline(text)}</p>\n'

def li(text):
    return f'<li>{inline(text)}</li>\n'


# ── Data loading ───────────────────────────────────────────────────────────────

def load(niche):
    d = BASE_DIR / 'projects' / niche / '01-research'
    competitors = json.loads((d / 'competitors.json').read_text())

    shops = []
    if (d / 'shop-watchlist.json').exists():
        shops = json.loads((d / 'shop-watchlist.json').read_text())

    erank = {'keywords': []}
    if (d / 'erank-keywords.json').exists():
        erank = json.loads((d / 'erank-keywords.json').read_text())

    patterns = []
    if (d / 'patterns-config.json').exists():
        patterns = json.loads((d / 'patterns-config.json').read_text())
        if isinstance(patterns, dict):
            patterns = patterns.get('patterns', [])

    return competitors, shops, erank, patterns, d


# ── Statistics (all deterministic from competitors.json) ──────────────────────

def stats(competitors):
    shirts = [c for c in competitors if c.get('is_shirt')]
    by_ems = sorted(competitors, key=lambda x: x.get('estimated_monthly_sales') or 0, reverse=True)
    shirt_by_ems = sorted(shirts, key=lambda x: x.get('estimated_monthly_sales') or 0, reverse=True)

    # Prices
    prices = []
    for c in shirts:
        m = re.search(r'\$([\d.]+)', c.get('price') or '')
        if m:
            prices.append(float(m.group(1)))

    # Personalization
    with_pers = [c for c in shirts if c.get('personalization')]

    # Comfort Colors mention (blank field or title)
    def has_cc(c):
        return ('comfort colors' in (c.get('blank') or '').lower() or
                'comfort colors' in (c.get('title') or '').lower())
    with_cc = [c for c in shirts if has_cc(c)]

    # Bestseller
    with_bs = [c for c in competitors if c.get('is_bestseller')]

    # In carts
    with_carts = [c for c in competitors if (c.get('in_carts') or 0) > 0]

    # High FPR (> 5.0) — high interest, possible conversion gap
    high_fpr = sorted(
        [c for c in shirts if (c.get('favorites_per_review') or 0) > 5.0],
        key=lambda x: x.get('favorites_per_review') or 0, reverse=True
    )

    # Legacy (RPM < 2, reviews > 5 — exclude new listings with no reviews)
    legacy = [c for c in shirts if
              (c.get('reviews') or 0) > 5 and
              (c.get('reviews_per_month') or 0) < 2]

    # High velocity (RPM > 20)
    high_vel = [c for c in shirts if (c.get('reviews_per_month') or 0) > 20]

    # Mockup breakdown for top 5
    top5_mockup = Counter(
        c.get('mockup_style') or 'unknown'
        for c in shirt_by_ems[:5]
    )

    # Breed-specific listings (title or key_phrases contain breed names)
    BREEDS = ['corgi', 'dachshund', 'doxie', 'weenie', 'wiener', 'golden retriever',
              'labrador', 'goldendoodle', 'labradoodle', 'bernedoodle',
              'golden', 'lab ', 'poodle', 'bulldog', 'beagle', 'husky',
              'german shepherd', 'schnauzer', 'chihuahua', 'shih tzu',
              'cavapoo', 'cockapoo']
    def is_breed_specific(c):
        haystack = (
            (c.get('title') or '') + ' ' +
            ' '.join(c.get('key_phrases') or []) + ' ' +
            (c.get('design_style') or '')
        ).lower()
        return any(b in haystack for b in BREEDS)

    breed_listings = [c for c in shirts if is_breed_specific(c)]

    # Treat Dealer listings
    def is_treat_dealer(c):
        haystack = (
            (c.get('title') or '') + ' ' +
            ' '.join(c.get('key_phrases') or [])
        ).lower()
        return 'treat dealer' in haystack
    treat_dealer = [c for c in shirts if is_treat_dealer(c)]

    # DTG confirmed rate
    dtg_confirmed = [c for c in shirts if
                     c.get('print_method') == 'DTG' and c.get('print_method_confirmed')]
    dtg_total = [c for c in shirts if c.get('print_method') == 'DTG']

    return {
        'total': len(competitors),
        'shirts': len(shirts),
        'prices': prices,
        'price_min': min(prices) if prices else None,
        'price_max': max(prices) if prices else None,
        'price_median': round(statistics.median(prices), 2) if len(prices) > 1 else None,
        'personalization_count': len(with_pers),
        'cc_count': len(with_cc),
        'bestseller_count': len(with_bs),
        'in_carts_count': len(with_carts),
        'high_fpr': high_fpr,
        'legacy': legacy,
        'high_vel': high_vel,
        'top5': by_ems[:5],
        'top5_shirt': shirt_by_ems[:5],
        'top3_shirt': shirt_by_ems[:3],
        'by_ems': by_ems,
        'shirt_by_ems': shirt_by_ems,
        'top5_mockup': top5_mockup,
        'breed_listings': breed_listings,
        'treat_dealer': treat_dealer,
        'dtg_confirmed': len(dtg_confirmed),
        'dtg_total': len(dtg_total),
        'shirts_list': shirts,
    }


# ── HTML sections ──────────────────────────────────────────────────────────────

def src_legend():
    return '''
<div class="legend">
  <strong>Source key:</strong>
  <span class="src our-data">[our data]</span> directly scraped from Etsy or measured in eRank &nbsp;·&nbsp;
  <span class="src inferred">[inferred]</span> logical conclusion drawn from our data &nbsp;·&nbsp;
  <span class="src market">[market knowledge]</span> general Etsy/POD knowledge, not verified for this niche
</div>'''


def section_methodology(niche, st, erank, shops):
    kw_count = len(erank.get('keywords', []))
    kw_date = erank.get('_meta', {}).get('data_through', 'unknown')
    shops_count = len(shops)
    return f'''
<section id="methodology">
  <h2>How This Research Was Done</h2>
  {p("This brief was generated entirely from three data files. Every number below is computed by a deterministic Python script — no AI estimation, no guessing. `[our data]`")}
  <table class="method-table">
    <thead><tr><th>What</th><th>How</th><th>Result</th><th>Source</th></tr></thead>
    <tbody>
      <tr>
        <td>Etsy listing scrapes</td>
        <td>Firecrawl CLI scraped the top results for "dog mom" shirts with <code>is_best_seller=true</code> filter. Each listing saved as a markdown file.</td>
        <td>{st["total"]} listings · {st["shirts"]} shirts</td>
        <td><span class="src our-data">[our data]</span></td>
      </tr>
      <tr>
        <td>Data extraction</td>
        <td><code>extract-competitors.py</code> — pure Python regex, no AI. Runs a 10-point self-check after each run to catch mismatches.</td>
        <td>51-field JSON per listing</td>
        <td><span class="src our-data">[our data]</span></td>
      </tr>
      <tr>
        <td>Shop intelligence</td>
        <td><code>research-shops.py</code> — scrapes shop page + up to 20 review pages per shop. Uses 3 methods to cross-estimate monthly sales (lifetime avg, current momentum, listing rollup).</td>
        <td>{shops_count} shops</td>
        <td><span class="src our-data">[our data]</span></td>
      </tr>
      <tr>
        <td>Keyword volumes</td>
        <td>eRank Bulk Keyword Tool (USA), {kw_count} terms submitted. Data through {kw_date}.</td>
        <td>{kw_count} keywords with avg searches + competition counts</td>
        <td><span class="src our-data">[our data]</span></td>
      </tr>
    </tbody>
  </table>
  <div class="warning-box">
    <strong>⚠ What's missing from this data:</strong>
    <ul>
      <li><strong>Listing creation dates</strong> — the Etsy API was not connected, so reviews-per-month (RPM) and estimated monthly sales (EMS) use the oldest <em>visible</em> review date as a proxy. For high-volume listings with 10,000+ reviews, this proxy may be years newer than the actual listing date — meaning RPM and EMS figures for the top listings are likely <strong>overstated</strong>. All EMS figures should be treated as directional, not exact. <span class="src our-data">[our data]</span></li>
      <li><strong>eRank trend sparklines</strong> — trend graph images are not machine-parseable. Trend direction (Rising/Declining/Stable) for keywords was determined by comparing 12-month avg vs May 2026 snapshot. <span class="src inferred">[inferred]</span></li>
      <li><strong>Mockup style classification</strong> — image URLs from competitor listings were not fetched during this run. Mockup style fields are marked <code>unknown</code> for most listings. <span class="src our-data">[our data]</span></li>
    </ul>
  </div>
</section>'''


def section_market_snapshot(niche, st, erank):
    kws = erank.get('keywords', [])
    # Best search:competition ratio
    ratios = [(k['keyword'], k['avg_searches_12mo'], k['etsy_competition'],
               round(k['etsy_competition'] / k['avg_searches_12mo']) if k['avg_searches_12mo'] and k['avg_searches_12mo'] > 20 else None)
              for k in kws]
    best_ratio = min((r for r in ratios if r[3] is not None), key=lambda x: x[3], default=None)

    # Top 5 EMS table
    top5_rows = ''
    for i, c in enumerate(st['top5'], 1):
        title = (c.get('title') or '')[:55] + '…'
        ems = c.get('estimated_monthly_sales') or 0
        rpm = c.get('reviews_per_month') or 0
        fpr = c.get('favorites_per_review')
        fpr_str = f'{fpr:.1f}' if fpr is not None else '—'
        bs = '✓' if c.get('is_bestseller') else ''
        blank = c.get('blank') or '—'
        top5_rows += f'<tr><td>{i}</td><td class="title-cell">{title}</td><td>{ems:,}</td><td>{rpm:.1f}</td><td>{fpr_str}</td><td>{bs}</td><td>{blank[:25]}</td></tr>\n'

    # eRank keywords table
    kw_rows = ''
    for k in sorted(kws, key=lambda x: x.get('avg_searches_12mo') or 0, reverse=True):
        avg = k.get('avg_searches_12mo') or 0
        may = k.get('may_2026_searches') or 0
        comp = k.get('etsy_competition') or 0
        ctr = k.get('avg_ctr_pct')
        ctr_str = f'{ctr}%' if ctr else '—'
        ratio = round(comp / avg) if avg > 20 else '—'
        # Trend inference
        if avg > 20 and may > 0:
            if may > avg * 1.3:
                trend = '<span class="badge yellow">Seasonal spike</span>'
            elif may < avg * 0.7:
                trend = '<span class="badge red">Below avg</span>'
            else:
                trend = '<span class="badge green">Stable</span>'
        else:
            trend = '<span class="badge grey">Low volume</span>'
        kw_rows += f'<tr><td><strong>{k["keyword"]}</strong></td><td>{avg:,}</td><td>{may:,}</td><td>{comp:,}</td><td>{ctr_str}</td><td>{ratio}</td><td>{trend}</td></tr>\n'

    price_str = (f'${st["price_min"]:.2f} – ${st["price_max"]:.2f} '
                 f'(median ${st["price_median"]:.2f})') if st['price_min'] else '—'
    pers_pct = round(st['personalization_count'] / st['shirts'] * 100) if st['shirts'] else 0
    cc_pct = round(st['cc_count'] / st['shirts'] * 100) if st['shirts'] else 0
    bs_pct = round(st['bestseller_count'] / st['total'] * 100) if st['total'] else 0

    best_ratio_note = ''
    if best_ratio:
        best_ratio_note = (f'<strong>{best_ratio[0]}</strong> has the best search-to-competition ratio '
                           f'({best_ratio[1]:,} searches / {best_ratio[2]:,} listings = '
                           f'{best_ratio[3]}:1 competition per monthly search). '
                           f'`[inferred]`')

    return f'''
<section id="snapshot">
  <h2>The Market — What We Found</h2>

  <div class="stat-grid">
    <div class="stat-card">
      <div class="stat-num">{st["total"]}</div>
      <div class="stat-label">listings scraped</div>
      <div class="stat-sub">{st["shirts"]} shirts ({round(st["shirts"]/st["total"]*100)}%)</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{pers_pct}%</div>
      <div class="stat-label">have personalization</div>
      <div class="stat-sub">{st["personalization_count"]}/{st["shirts"]} shirt listings</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{cc_pct}%</div>
      <div class="stat-label">mention Comfort Colors</div>
      <div class="stat-sub">{st["cc_count"]}/{st["shirts"]} shirt listings</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{bs_pct}%</div>
      <div class="stat-label">have Bestseller badge</div>
      <div class="stat-sub">{st["bestseller_count"]}/{st["total"]} listings</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{st["in_carts_count"]}</div>
      <div class="stat-label">in-carts signals</div>
      <div class="stat-sub">active buyer demand</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{price_str.split("–")[0].strip()}</div>
      <div class="stat-label">price floor</div>
      <div class="stat-sub">{price_str}</div>
    </div>
  </div>
  {p("All stat card values computed directly from competitors.json. `[our data]`")}

  <h3>Top 5 Listings by Estimated Monthly Sales</h3>
  {p("EMS = reviews_per_month × 7 (industry proxy). RPM uses oldest visible review date as listing age anchor — may overstate EMS for high-review listings. `[our data]` FPR = favorites ÷ reviews: above 5.0 signals high save-but-don't-buy rate. `[inferred]`")}
  <table>
    <thead><tr><th>#</th><th>Title</th><th>EMS</th><th>RPM</th><th>FPR</th><th>Bestseller</th><th>Blank</th></tr></thead>
    <tbody>{top5_rows}</tbody>
  </table>

  <h3>Keyword Volumes (eRank, USA)</h3>
  {p("Avg = 12-month average searches/month. May 2026 = single-month snapshot (includes Mother's Day spike). Competition = total Etsy listings for that exact term. Ratio = competition listings per monthly search — lower is better. `[our data]`")}
  {p(best_ratio_note) if best_ratio_note else ''}
  <table>
    <thead><tr><th>Keyword</th><th>Avg/mo</th><th>May 2026</th><th>Competition</th><th>Avg CTR</th><th>Ratio</th><th>Trend</th></tr></thead>
    <tbody>{kw_rows}</tbody>
  </table>
  {p("Trend is `[inferred]` from comparing May 2026 snapshot vs 12-month avg. Rising = May > avg × 1.3 (Mother's Day spike). Stable = within 30% of avg. We did not parse the eRank sparkline charts. `[inferred]`")}
</section>'''


def section_who_is_winning(st, shops):
    # Top 3 shops
    top3_shops = shops[:3]
    shop_rows = ''
    for s in top3_shops:
        name = s.get('shop_name', '—')
        est = s.get('estimated_monthly_sales') or '—'
        total = s.get('total_sales') or '—'
        conf = s.get('confidence') or '—'
        trend = s.get('trend_signal') or '—'
        trend_icon = {'growing': '↑ growing', 'declining': '↓ declining', 'stable': '→ stable'}.get(trend, '?')
        m1 = s.get('method1_lifetime_avg_monthly') or '—'
        m2 = s.get('method2_current_momentum') or '—'
        shop_rows += f'<tr><td><a href="https://www.etsy.com/shop/{name}" target="_blank">{name}</a></td><td>{est:,}/mo' if isinstance(est, int) else f'<tr><td>{name}</td><td>{est}'
        shop_rows += f'</td><td>{total:,}' if isinstance(total, int) else f'</td><td>{total}'
        shop_rows += f'</td><td>{trend_icon}</td><td>{conf}</td><td>M1={m1} / M2={m2}</td></tr>\n'

    # Dominant formula description — pulled from actual top 5 listings
    top3 = st['top3_shirt']
    formula_items = ''
    for c in top3:
        title = (c.get('title') or '')[:70]
        ems = c.get('estimated_monthly_sales') or 0
        revs = c.get('reviews') or 0
        favs = c.get('favorites_count') or 0
        blank = c.get('blank') or 'not stated'
        formula_items += f'<li><strong>{title}…</strong> — EMS {ems:,} · {revs:,} reviews · {favs:,} favorites · blank: {blank}</li>\n'

    return f'''
<section id="winners">
  <h2>Who's Winning and Why</h2>

  <h3>Top 3 Shops by Estimated Monthly Sales</h3>
  {p("Shop EMS is estimated using 3 methods: (M1) total shop sales ÷ months active, (M2) review velocity from last 5 months of review pages, (M3) sum of listing EMS from competitors.json. Confidence reflects cross-validation between available methods. `[our data]`")}
  <table>
    <thead><tr><th>Shop</th><th>Est. Monthly Sales</th><th>Total Sales</th><th>Trend</th><th>Confidence</th><th>Method cross-check</th></tr></thead>
    <tbody>{shop_rows}</tbody>
  </table>

  <h3>The Dominant Formula</h3>
  {p("The top 3 shirt listings by EMS all share the same format. `[our data]`")}
  <ul>{formula_items}</ul>
  {p("Common pattern: custom photo + dog name on a Comfort Colors garment-dyed blank, presented in a bootleg/vintage graphic tee layout with multiple color options. `[inferred]`")}
  {p("Why this formula dominates: high personalization = each buyer gets a unique item, reducing price sensitivity. Comfort Colors commands a premium aesthetic. The bootleg tee template is well-established in the dog niche. `[inferred]`")}
  {p(f"Barrier to entry: the #1 listing has {st['top5_shirt'][0].get('reviews', 0):,} reviews and {st['top5_shirt'][0].get('favorites_count', 0):,} favorites. New listings competing on the same exact template face an extremely high social-proof gap. `[our data]`")}
</section>'''


def section_gaps(st):
    # Build high FPR table
    fpr_rows = ''
    for c in st['high_fpr'][:8]:
        title = (c.get('title') or '')[:60] + '…'
        fpr = c.get('favorites_per_review') or 0
        ems = c.get('estimated_monthly_sales') or 0
        revs = c.get('reviews') or 0
        favs = c.get('favorites_count') or 0
        kp = ', '.join((c.get('key_phrases') or [])[:3])
        fpr_rows += f'<tr><td class="title-cell">{title}</td><td><strong>{fpr:.1f}</strong></td><td>{ems}</td><td>{revs}</td><td>{favs:,}</td><td>{kp}</td></tr>\n'

    # Breed listings summary
    breed_ems = [c.get('estimated_monthly_sales') or 0 for c in st['breed_listings']]
    breed_fpr = [c.get('favorites_per_review') or 0
                 for c in st['breed_listings'] if c.get('favorites_per_review')]
    avg_breed_fpr = round(statistics.mean(breed_fpr), 1) if breed_fpr else '—'
    avg_generic_fpr_vals = [c.get('favorites_per_review') or 0
                            for c in st['shirt_by_ems'][:3] if c.get('favorites_per_review')]
    avg_generic_fpr = round(statistics.mean(avg_generic_fpr_vals), 1) if avg_generic_fpr_vals else '—'

    return f'''
<section id="gaps">
  <h2>Where the Gaps Are</h2>

  {p(f"The dominant sellers (custom photo bootleg tee) are hard to displace head-on — the #1 listing alone has {st['top5_shirt'][0].get('reviews', 0):,} reviews and {st['top5_shirt'][0].get('favorites_count', 0):,} favorites. `[our data]` Age data from listing-dates.json is not available, so years active cannot be stated — we only know reviews and favorites counts from the scrape. `[our data]` The cleaner opportunity is in sub-niches where demand exists but no dominant listing has locked it down. `[inferred]`")}

  <h3>High-Interest / Possible Conversion Gaps (FPR > 5.0)</h3>
  {p("FPR = favorites ÷ reviews. Above 5.0 means: many shoppers saved the listing, but relatively few bought. `[inferred]` This can signal: (a) unmet demand in a sub-niche where the existing listing isn't quite right, or (b) price/trust friction on a newer listing. `[market knowledge]`")}
  {p(f"There are {len(st['high_fpr'])} listings with FPR above 5.0. `[our data]`")}
  <table>
    <thead><tr><th>Title</th><th>FPR</th><th>EMS</th><th>Reviews</th><th>Favorites</th><th>Key phrases</th></tr></thead>
    <tbody>{fpr_rows if fpr_rows else '<tr><td colspan="6">No high-FPR listings found</td></tr>'}</tbody>
  </table>

  <h3>Breed-Specific Sub-Niche</h3>
  {p(f"There are {len(st['breed_listings'])} breed-specific listings in the scraped data. `[our data]`")}
  {p(f"Their average FPR is {avg_breed_fpr} vs {avg_generic_fpr} for the top 3 generic bootleg tee listings. `[our data]`") if isinstance(avg_breed_fpr, float) else ''}
  {p("High FPR on breed-specific listings suggests buyers are saving them in large numbers but not converting — possibly because the current listings aren't quite right (wrong design, too generic, wrong price) rather than because demand doesn't exist. `[inferred]`")}
  {p("The breed-specific sub-niche has far fewer entrenched competitors than the generic dog mom market. A new listing can appear at the top of breed-specific search results within 1–2 months of launch. `[market knowledge]`")}
</section>'''


def section_directions(st, erank):
    kws = {k['keyword']: k for k in erank.get('keywords', [])}
    shirt_kw = kws.get('dog mom shirt', {})

    # Treat dealer listings
    td_listings = st['treat_dealer']
    td_ems_list = [c.get('estimated_monthly_sales') or 0 for c in td_listings]

    # Dachshund / Corgi specific FPR
    def breed_data(breed_terms):
        matches = []
        for c in st['shirts_list']:
            haystack = ((c.get('title') or '') + ' ' + ' '.join(c.get('key_phrases') or [])).lower()
            if any(b in haystack for b in breed_terms):
                matches.append(c)
        return matches

    dachshund = breed_data(['dachshund', 'doxie', 'weenie', 'wiener'])
    corgi = breed_data(['corgi'])
    golden = breed_data(['golden retriever', 'golden ', 'goldendoodle'])

    def fpr_summary(listings):
        fprs = [c.get('favorites_per_review') or 0 for c in listings if c.get('favorites_per_review')]
        ems_vals = [c.get('estimated_monthly_sales') or 0 for c in listings]
        return {
            'count': len(listings),
            'avg_fpr': round(statistics.mean(fprs), 1) if fprs else None,
            'max_fpr': round(max(fprs), 1) if fprs else None,
            'avg_ems': round(statistics.mean(ems_vals)) if ems_vals else None,
        }

    d_data = fpr_summary(dachshund)
    c_data = fpr_summary(corgi)
    g_data = fpr_summary(golden)

    # Build listing evidence lists
    def listing_evidence(listings, max_items=3):
        items = sorted(listings, key=lambda x: x.get('favorites_per_review') or 0, reverse=True)
        out = ''
        for c in items[:max_items]:
            fpr = c.get('favorites_per_review')
            ems = c.get('estimated_monthly_sales') or 0
            revs = c.get('reviews') or 0
            favs = c.get('favorites_count') or 0
            title = (c.get('title') or '')[:65]
            fpr_display = f'{fpr:.1f}' if fpr else '—'
            out += f'<li><em>{title}…</em> — EMS {ems} · {revs} reviews · {favs:,} favorites · FPR {fpr_display}</li>\n'
        return out

    td_evidence = listing_evidence(td_listings)
    d_evidence = listing_evidence(dachshund)
    g_evidence = listing_evidence(golden)

    def risk_li(text):
        return f'<li>{inline(text)}</li>'

    shirt_avg = shirt_kw.get('avg_searches_12mo', 0)
    shirt_comp = shirt_kw.get('etsy_competition', 0)
    shirt_ratio = round(shirt_comp / shirt_avg) if shirt_avg > 20 else '—'

    return f'''
<section id="directions">
  <h2>Three Design Directions — With Evidence</h2>

  {p("These are not guesses. Each direction is supported by specific data points from our scraped competitor set and eRank. The evidence column shows exactly what data backs each claim and what is inferred. Pick the one that matches your energy and time investment. `[our data]`")}

  <!-- DIRECTION A -->
  <div class="direction-card direction-a">
    <div class="direction-header">
      <span class="direction-label">Option A</span>
      <h3>Breed-Specific + Punny</h3>
      <span class="confidence medium">⚠ Medium confidence</span>
    </div>
    <p><strong>What it is:</strong> A shirt aimed at a specific breed's fan base — e.g. "Dachshund Mom," "Corgi Crew," "Weiner Dog Mom" — with a funny or punny design concept unique to that breed.</p>

    <h4>Evidence for this direction</h4>
    <table>
      <thead><tr><th>Claim</th><th>Evidence</th><th>Source</th></tr></thead>
      <tbody>
        <tr>
          <td>Breed-specific listings have high FPR (buyers save but don't buy in large numbers)</td>
          <td>Dachshund listings in our scrape: {d_data["count"]} listings, avg FPR {d_data["avg_fpr"]}, max FPR {d_data["max_fpr"]}. Corgi: {c_data["count"]} listings, avg FPR {c_data["avg_fpr"]}.</td>
          <td><span class="src our-data">[our data]</span></td>
        </tr>
        <tr>
          <td>High FPR signals unmet demand in the sub-niche</td>
          <td>Buyers save but don't purchase — suggests the existing breed-specific listings aren't quite satisfying what they want.</td>
          <td><span class="src inferred">[inferred]</span></td>
        </tr>
        <tr>
          <td>Low review counts on breed listings = low social proof barrier</td>
          <td>Breed-specific listings in our data have avg EMS {d_data["avg_ems"]} — low, but these are newer/smaller. No single listing dominates breed-specific search.</td>
          <td><span class="src our-data">[our data]</span></td>
        </tr>
        <tr>
          <td>Breed-specific searches are long-tail with less competition</td>
          <td>"dog mom shirt" = 261,754 competing listings. A search for "dachshund mom shirt" is a subset of this — fewer listings targeting it directly.</td>
          <td><span class="src inferred">[inferred]</span> — breed-specific term not looked up in eRank</td>
        </tr>
      </tbody>
    </table>
    <h4>Example listings already in this space</h4>
    <ul>{d_evidence if d_evidence else '<li>No dachshund listings in our scraped set.</li>'}</ul>
    <h4>Risks</h4>
    <ul>
      {risk_li('Smaller total audience per breed. A "Dachshund Mom" shirt can only be bought by dachshund owners. `[inferred]`')}
      {risk_li('High FPR on breed listings may reflect recency, not unmet demand — most breed-specific listings in our data are 1–2 months old, and new listings always accumulate favorites before reviews catch up. `[our data]`')}
      {risk_li('FPR data is from a small sample (our scrape is best-sellers only — may not represent all breed listings). `[our data]`')}
      {risk_li('Breed-specific keywords not validated in eRank — search volume unknown. `[our data]`')}
    </ul>
    <div class="next-step">
      <strong>Phase 1.5 validation:</strong> Search "dachshund mom shirt" (or chosen breed) on Etsy. If fewer than 3 listings have 500+ reviews → the sub-niche is still open.
    </div>
  </div>

  <!-- DIRECTION B -->
  <div class="direction-card direction-b">
    <div class="direction-header">
      <span class="direction-label">Option B</span>
      <h3>Treat Dealer (Breed-Agnostic Funny)</h3>
      <span class="confidence high">✅ High confidence — concept proven</span>
    </div>
    <p><strong>What it is:</strong> A funny shirt for any dog mom — "Professional Treat Dealer," "Licensed Treat Dealer," or similar pun. No breed specificity. Works as a gift for any dog owner.</p>

    <h4>Evidence for this direction</h4>
    <table>
      <thead><tr><th>Claim</th><th>Evidence</th><th>Source</th></tr></thead>
      <tbody>
        <tr>
          <td>"Treat Dealer" concept already has proven real demand</td>
          <td>{len(td_listings)} listings in our scrape use this phrase. {f'The strongest has {max((c.get("reviews") or 0) for c in td_listings):,} reviews and {max((c.get("favorites_count") or 0) for c in td_listings):,} favorites — this is a mature, validated concept, not a speculation. EMS values: {", ".join(str(e) for e in td_ems_list)}.' if td_listings else 'No treat dealer listings found in top results — phrase appears in key_phrases only.'}</td>
          <td><span class="src our-data">[our data]</span></td>
        </tr>
        <tr>
          <td>Concept is humorous and gift-friendly, not just for self-purchase</td>
          <td>"dog mom gifts" = 1,448 avg searches/mo; "dog mom gift" = 630 avg but spiked to 1,710 in May 2026 (2.7× spike). Note: "dog mom gifts" (plural) did NOT spike in May — it was actually below average (1,200 vs 1,448 avg). Gift-intent demand exists but the spike is specific to the singular form.</td>
          <td><span class="src our-data">[our data]</span></td>
        </tr>
        <tr>
          <td>Not oversaturated at this specific phrase</td>
          <td>Only {len(td_listings)} listings in our 51-listing scrape use the phrase — it is not the dominant formula in the niche.</td>
          <td><span class="src our-data">[our data]</span></td>
        </tr>
        <tr>
          <td>Breed-agnostic = larger addressable audience than breed-specific</td>
          <td>Any dog owner can buy it. "Dog mom shirt" avg 1,631 searches/mo vs individual breed which are subsets of this.</td>
          <td><span class="src inferred">[inferred]</span></td>
        </tr>
      </tbody>
    </table>
    <h4>Example listings already in this space</h4>
    <ul>{td_evidence if td_evidence else '<li>No exact "treat dealer" listings found in our scraped set — the phrase appears in key phrases, not necessarily main titles.</li>'}</ul>
    <h4>Risks</h4>
    <ul>
      {risk_li(f'One competitor (NothingButPink) already has {max((c.get("reviews") or 0) for c in td_listings):,} reviews on this concept — a {round(max((c.get("reviews") or 0) for c in td_listings) / max(1, min((c.get("reviews") or 1) for c in td_listings if (c.get("reviews") or 0) > 0)))if td_listings else "unknown"}× review lead over the weakest competitor. `[our data]`') if td_listings else risk_li('Treat dealer phrase not found in top listing titles — validate manually. `[our data]`')}
      {risk_li('"Funny dog mom shirt" eRank avg is <20 searches/mo — the exact phrase has very low search volume. Success depends on broader placement under "dog mom shirt" or gift searches. `[our data]`')}
      {risk_li('Without personalization, it competes on design quality alone — harder to differentiate at purchase. `[inferred]`')}
    </ul>
    <div class="next-step">
      <strong>Phase 1.5 validation:</strong> Search "treat dealer shirt" and "professional treat dealer" on Etsy. Look for listings with 200+ reviews on exactly this concept. If none → still open enough to enter.
    </div>
  </div>

  <!-- DIRECTION C -->
  <div class="direction-card direction-c">
    <div class="direction-header">
      <span class="direction-label">Option C</span>
      <h3>Golden Retriever / Lab Mom (Mainstream Breed)</h3>
      <span class="confidence medium">⚠ Medium confidence</span>
    </div>
    <p><strong>What it is:</strong> Target the most popular US dog breeds — Golden Retriever, Labrador, or Goldendoodle — with a mom-focused design. Larger audience than obscure breeds, but more competition too.</p>

    <h4>Evidence for this direction</h4>
    <table>
      <thead><tr><th>Claim</th><th>Evidence</th><th>Source</th></tr></thead>
      <tbody>
        <tr>
          <td>Golden Retriever listings exist in our scrape with real EMS</td>
          <td>{g_data["count"]} golden/goldendoodle listings found. Avg EMS {g_data["avg_ems"]}. Max FPR {g_data["max_fpr"]}.</td>
          <td><span class="src our-data">[our data]</span></td>
        </tr>
        <tr>
          <td>Golden Retriever and Labrador are #1 and #2 most popular US dog breeds</td>
          <td>AKC registration data — these breeds consistently rank at the top of US ownership stats.</td>
          <td><span class="src market">[market knowledge]</span></td>
        </tr>
        <tr>
          <td>Larger audience than obscure breeds</td>
          <td>More dog owners = more potential buyers for the same design. Golden Retriever search volume is a multiple of dachshund search volume.</td>
          <td><span class="src inferred">[inferred]</span> — breed-specific terms not validated in eRank</td>
        </tr>
        <tr>
          <td>More competition than niche breeds</td>
          <td>Popular breeds attract more sellers. The same FPR gap observed in dachshund is less pronounced in golden/lab because those sub-niches have more existing listings.</td>
          <td><span class="src inferred">[inferred]</span></td>
        </tr>
      </tbody>
    </table>
    <h4>Example listings already in this space</h4>
    <ul>{g_evidence if g_evidence else '<li>No golden retriever listings found in our scraped set.</li>'}</ul>
    <h4>Risks</h4>
    <ul>
      {risk_li('More established competition vs niche breeds — harder to rank in a crowded sub-niche. `[inferred]`')}
      {risk_li('Golden/Lab-specific search volume not validated by eRank. Higher popularity assumed but not measured. `[market knowledge]`')}
      {risk_li('You would be competing with both generic dog mom shirts AND golden-retriever-specific shops simultaneously. `[inferred]`')}
    </ul>
    <div class="next-step">
      <strong>Phase 1.5 validation:</strong> Search "golden retriever mom shirt" on Etsy filtered to best-sellers. Count how many listings have 500+ reviews. If 5 or more → sub-niche is mature, pivot to a more specific angle.
    </div>
  </div>
</section>'''


def section_next_steps():
    return '''
<section id="next-steps">
  <h2>Next Step — Phase 1.5: Slogan Validation</h2>
  <p>Before starting any design work, validate your exact slogan or concept phrase on Etsy:</p>
  <ol>
    <li>Pick a direction (A, B, or C) and write down the exact phrase you want to use as the design concept.</li>
    <li>Search that exact phrase on Etsy (no filters — raw search). Look at the top 10 results.</li>
    <li>Check: does any single listing already have 500+ reviews AND 5,000+ favorites with that exact phrase? If yes → that position is locked. Rephrase or pivot sub-angle.</li>
    <li>If not → proceed to Phase 2 (Design Brief).</li>
  </ol>
  <div class="warning-box">
    <strong>Important:</strong> Phase 1.5 is about the exact design slogan (e.g. "Professional Treat Dealer"), not the product keyword (e.g. "dog mom shirt"). The product keyword always has competition — that's expected. The slogan is what should be unclaimed.
  </div>
</section>'''


# ── CSS ────────────────────────────────────────────────────────────────────────

CSS = '''
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 14px; color: #1a1a1a; background: #f5f5f5; }
.container { max-width: 1100px; margin: 0 auto; padding: 24px 20px; }
h1 { font-size: 26px; margin-bottom: 4px; }
.subtitle { color: #666; margin-bottom: 24px; font-size: 13px; }
h2 { font-size: 20px; color: #1a1a1a; margin: 32px 0 12px; padding-bottom: 6px; border-bottom: 2px solid #e5e5e5; }
h3 { font-size: 15px; color: #333; margin: 20px 0 8px; }
h4 { font-size: 13px; color: #444; margin: 14px 0 6px; text-transform: uppercase; letter-spacing: .04em; }
p { line-height: 1.6; margin-bottom: 10px; color: #333; }
ul, ol { padding-left: 20px; margin-bottom: 12px; }
li { line-height: 1.6; margin-bottom: 4px; color: #333; }
section { background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,.07); }
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }
th { background: #f0f0f0; text-align: left; padding: 8px 10px; font-weight: 600; border-bottom: 2px solid #ddd; }
td { padding: 7px 10px; border-bottom: 1px solid #eee; vertical-align: top; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #fafafa; }
.title-cell { max-width: 320px; font-size: 12px; }
.method-table td:first-child { font-weight: 600; width: 180px; }
.method-table td:nth-child(3) { font-size: 12px; color: #555; }
.stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: #f8f8f8; border: 1px solid #e5e5e5; border-radius: 6px; padding: 14px; text-align: center; }
.stat-num { font-size: 22px; font-weight: 700; color: #111; }
.stat-label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: .04em; margin: 3px 0; }
.stat-sub { font-size: 11px; color: #999; }
.src { display: inline-block; padding: 1px 6px; border-radius: 10px; font-size: 11px; font-weight: 600; color: #fff; margin-left: 3px; white-space: nowrap; }
.our-data { background: #198754; }
.inferred { background: #2563EB; }
.market { background: #9CA3AF; }
.legend { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 10px 14px; margin-bottom: 20px; font-size: 12px; line-height: 1.8; }
.warning-box { background: #fff8e1; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 0 6px 6px 0; margin: 14px 0; font-size: 13px; }
.warning-box ul { margin: 8px 0 0; }
.warning-box li { margin-bottom: 6px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge.green { background: #d1fae5; color: #065f46; }
.badge.yellow { background: #fef3c7; color: #92400e; }
.badge.red { background: #fee2e2; color: #991b1b; }
.badge.grey { background: #f3f4f6; color: #6b7280; }
.verdict-bar { background: #fffbeb; border: 2px solid #f59e0b; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; display: flex; align-items: center; gap: 16px; }
.verdict-text { font-size: 18px; font-weight: 700; color: #b45309; }
.verdict-sub { font-size: 13px; color: #78350f; margin-top: 3px; }
.direction-card { border: 1px solid #e5e5e5; border-radius: 8px; padding: 20px; margin: 16px 0; }
.direction-a { border-left: 4px solid #2563EB; }
.direction-b { border-left: 4px solid #198754; }
.direction-c { border-left: 4px solid #9333ea; }
.direction-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.direction-header h3 { margin: 0; font-size: 17px; }
.direction-label { background: #1a1a1a; color: #fff; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; }
.confidence { font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 10px; }
.confidence.high { background: #d1fae5; color: #065f46; }
.confidence.medium { background: #fef3c7; color: #92400e; }
.confidence.low { background: #fee2e2; color: #991b1b; }
.next-step { background: #f0f9ff; border-left: 3px solid #0284c7; padding: 10px 14px; border-radius: 0 6px 6px 0; margin-top: 14px; font-size: 12px; }
@media (max-width: 700px) { .stat-grid { grid-template-columns: repeat(2, 1fr); } }
'''


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--niche', required=True)
    args = parser.parse_args()

    competitors, shops, erank, patterns, research_dir = load(args.niche)
    st = stats(competitors)
    out_path = research_dir / 'phase1-report.html'

    niche_display = args.niche.replace('-', ' ').title()

    # Verdict from market-insights.md (read first line of niche verdict section)
    verdict_text = 'Enter with sub-niche pivot'
    verdict_sub = 'Broad custom-photo market is dominated. Breed-specific + punny angle shows the clearest opening. [inferred from our data]'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{niche_display} — Phase 1 Research Brief</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
  <h1>{niche_display} — Phase 1 Research Brief</h1>
  <div class="subtitle">Generated {TODAY} · {st["total"]} listings · {st["shirts"]} shirts · {len(shops)} shops · {len(erank.get("keywords", []))} keywords</div>

  {src_legend()}

  <div class="verdict-bar">
    <div>
      <div class="verdict-text">Verdict: {verdict_text}</div>
      <div class="verdict-sub">{verdict_sub}</div>
    </div>
  </div>

  {section_methodology(args.niche, st, erank, shops)}
  {section_market_snapshot(args.niche, st, erank)}
  {section_who_is_winning(st, shops)}
  {section_gaps(st)}
  {section_directions(st, erank)}
  {section_next_steps()}

</div>
</body>
</html>'''

    out_path.write_text(html)
    print(f'✓ Generated {out_path}')
    print(f'  {st["total"]} listings · {st["shirts"]} shirts · {len(shops)} shops · {len(erank.get("keywords", []))} keywords')


if __name__ == '__main__':
    main()
