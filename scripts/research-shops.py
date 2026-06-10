#!/usr/bin/env python3
"""
research-shops.py

Scrapes competitor Etsy shop pages and builds shop-watchlist.json.
Derives shop-level monthly sales estimates from three signals:

  Method 1 — total_sales ÷ months_active        (lifetime average, from shop page)
  Method 2 — rate-based projection × 7          (current momentum, from /reviews pages)
  Method 3 — sum of listing reviews from competitors.json (demand proxy, not sales estimate)

M2 scrapes /reviews pages dynamically until the oldest review is 5 months old (150 days),
up to a max of 20 pages. This smooths out seasonal spikes (e.g. Father's Day, Christmas).
Fast shops need more pages to reach 5 months; slow shops stop early.
Counts ALL review date occurrences (not unique) so multiple reviews per day are each counted.
Playwright is blocked by Etsy — Firecrawl is used for all scraping (has anti-bot measures).

Usage:
  # Auto-detect top N shops from competitors.json (default: top 8 by sum of listing reviews)
  python3 scripts/research-shops.py --niche personalized-gift-for-dad

  # Specific shops only
  python3 scripts/research-shops.py --niche personalized-gift-for-dad --shops EsseHomeDesign FunnyHAHAUSA

  # More shops
  python3 scripts/research-shops.py --niche personalized-gift-for-dad --top 12
"""

import subprocess, json, re, argparse, os, shutil, sys, time, datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).parent.parent


def _find_firecrawl():
    found = shutil.which('firecrawl')
    if found:
        return Path(found)
    for p in [Path.home() / '.npm-global/bin/firecrawl',
              Path('/usr/local/bin/firecrawl'),
              Path('/opt/homebrew/bin/firecrawl')]:
        if p.exists():
            return p
    print("✗ firecrawl CLI not found. Install: npm install -g firecrawl")
    sys.exit(1)


FIRECRAWL_BIN = _find_firecrawl()


def load_env():
    env = dict(os.environ)
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()
    return env


ENV = load_env()

TODAY = datetime.date.today()

MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


# ── Parsing helpers ────────────────────────────────────────────────────────────

def parse_number(text):
    """Extract first integer from a string like '3,842 sales'."""
    m = re.search(r'[\d,]+', text.replace(',', ''))
    return int(m.group().replace(',', '')) if m else None


def parse_shop_opened(text):
    """
    Parse 'Member since Jan 2019' or 'On Etsy since 2019' → datetime.date.
    Returns (date, precision) where precision is 'month' or 'year'.
    """
    # "Member since January 2019" or "Jan 2019"
    m = re.search(
        r'(?:member since|on etsy since|joined)\s+([a-z]+\.?\s+)?(\d{4})',
        text, re.IGNORECASE
    )
    if m:
        month_str = (m.group(1) or '').strip().rstrip('.').lower()[:3]
        year = int(m.group(2))
        month = MONTH_MAP.get(month_str, 1)
        precision = 'month' if month_str in MONTH_MAP else 'year'
        return datetime.date(year, month, 1), precision
    return None, None


def months_between(start_date, end_date=None):
    end_date = end_date or TODAY
    delta = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    return max(delta, 1)


def parse_review_dates_all(text):
    """
    Extract ALL review date occurrences from page text — including duplicates.
    Multiple reviews on the same day each appear as a separate match.
    Returns a list (not a set) sorted most-recent first.
    """
    pattern = re.compile(
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})\b',
        re.IGNORECASE
    )
    dates = []
    for m in pattern.finditer(text):
        try:
            month = MONTH_MAP[m.group(1)[:3].lower()]
            day = int(m.group(2))
            year = int(m.group(3))
            dates.append(datetime.date(year, month, day))
        except (ValueError, KeyError):
            continue
    return sorted(dates, reverse=True)


def reviews_in_window(dates, days=30):
    cutoff = TODAY - datetime.timedelta(days=days)
    return sum(1 for d in dates if d >= cutoff)


# ── Scraping ───────────────────────────────────────────────────────────────────

def scrape_shop(shop_name, raw_dir):
    url = f'https://www.etsy.com/shop/{shop_name}'
    out_path = raw_dir / f'{shop_name}.md'

    result = subprocess.run(
        [str(FIRECRAWL_BIN), 'scrape', url,
         '--only-main-content', '--wait-for', '2500',
         '-o', str(out_path)],
        capture_output=True, text=True, timeout=60, env=ENV
    )

    if not out_path.exists() or out_path.stat().st_size < 300:
        return shop_name, None, 'scrape returned minimal content'

    return shop_name, out_path.read_text(), None


def scrape_reviews_pages(shop_name, raw_dir, max_pages=20, lookback_days=150):
    """
    Scrape /reviews pages dynamically until the oldest review found is at least
    lookback_days (default 150 = ~5 months) old, or max_pages is reached.

    Why 5 months: smooths seasonal spikes (Father's Day, Christmas, Valentine's).
    Fast shops need more pages to reach 5 months; slow shops stop early.
    Counts ALL occurrences (not unique) so multiple reviews per day are each counted.
    """
    cutoff = TODAY - datetime.timedelta(days=lookback_days)
    all_dates = []

    for page_num in range(1, max_pages + 1):
        url = f'https://www.etsy.com/shop/{shop_name}/reviews?page={page_num}'
        out_path = raw_dir / f'{shop_name}-reviews-p{page_num}.md'

        subprocess.run(
            [str(FIRECRAWL_BIN), 'scrape', url,
             '--only-main-content', '--wait-for', '3000',
             '-o', str(out_path)],
            capture_output=True, text=True, timeout=60, env=ENV
        )

        if not out_path.exists() or out_path.stat().st_size <= 300:
            break  # no more review pages or empty response

        page_dates = parse_review_dates_all(out_path.read_text())
        if not page_dates:
            break  # page had no parseable dates — end of reviews

        all_dates.extend(page_dates)

        # Stop once oldest review on this page is beyond our lookback window
        if min(page_dates) < cutoff:
            break

    return sorted(all_dates, reverse=True)


# ── Estimation ─────────────────────────────────────────────────────────────────

def estimate_shop(shop_name, content, listing_rollup, review_dates=None):
    review_dates = review_dates or []
    result = {
        'shop_name': shop_name,
        'etsy_url': f'https://www.etsy.com/shop/{shop_name}',
        'total_sales': None,
        'active_listings': None,
        'total_reviews': None,
        'shop_opened': None,
        'shop_opened_precision': None,
        'months_active': None,
        # Method 1
        'method1_lifetime_avg_monthly': None,
        # Method 2
        'review_occurrences_found': 0,
        'reviews_last_30d': None,
        'reviews_last_90d': None,
        'method2_current_momentum': None,
        'method2_window': None,
        # Method 3
        'method3_listing_rollup': listing_rollup,
        # Combined
        'estimated_monthly_sales': None,
        'confidence': None,
        'confidence_notes': [],
        'trend_signal': None,
    }

    notes = result['confidence_notes']

    # Total sales
    sales_m = re.search(r'([\d,]+)\s+sales', content, re.IGNORECASE)
    if sales_m:
        result['total_sales'] = int(sales_m.group(1).replace(',', ''))

    # Active listings
    listings_m = re.search(r'(\d[\d,]*)\s+(?:listing|item|result)', content, re.IGNORECASE)
    if listings_m:
        val = listings_m.group(1).replace(',', '')
        if val:
            result['active_listings'] = int(val)

    # Total reviews
    reviews_m = re.search(r'([\d,]+)\s+review', content, re.IGNORECASE)
    if reviews_m:
        result['total_reviews'] = int(reviews_m.group(1).replace(',', ''))

    # Shop opened
    opened_date, precision = parse_shop_opened(content)
    if opened_date:
        result['shop_opened'] = opened_date.isoformat()
        result['shop_opened_precision'] = precision
        result['months_active'] = months_between(opened_date)

    # Method 1 — total_sales ÷ months_active
    if result['total_sales'] and result['months_active']:
        result['method1_lifetime_avg_monthly'] = round(
            result['total_sales'] / result['months_active']
        )
    else:
        notes.append('Method 1 unavailable: missing total_sales or shop_opened')

    # Method 2 — review page scraping
    # review_dates = ALL occurrences from /reviews pages 1-3 (not deduplicated).
    # Multiple reviews on the same day are each counted individually.
    result['review_occurrences_found'] = len(review_dates)

    if len(review_dates) >= 5:
        # Calculate daily rate from the actual span of scraped reviews,
        # then project to 30 days. This avoids the "42 reviews in 9 days = 42/month"
        # error that occurs when all scraped reviews fall within the 30d window.
        span_days = max((review_dates[0] - review_dates[-1]).days + 1, 1)
        daily_rate = len(review_dates) / span_days
        monthly_reviews = daily_rate * 30
        result['reviews_last_30d'] = round(monthly_reviews)
        result['method2_current_momentum'] = round(monthly_reviews * 7)
        result['method2_window'] = f'{span_days}d span (5mo window) → projected 30d'
        result['review_daily_rate'] = round(daily_rate, 2)
    else:
        notes.append(f'Method 2 skipped: only {len(review_dates)} review occurrences found (need 5+)')

    # Method 3 — bottom-up rollup (already passed in)
    if not listing_rollup:
        notes.append('Method 3 unavailable: no listings from this shop in competitors.json')

    # ── Combine ────────────────────────────────────────────────────────────────
    signals = [v for v in [
        result['method1_lifetime_avg_monthly'],
        result['method2_current_momentum'],
        result['method3_listing_rollup'],
    ] if v is not None]

    if not signals:
        result['confidence'] = 'low'
        notes.append('No signals available — page may not have scraped correctly')
        return result

    # Headline: prefer M2 (current) if it passed the reliability threshold, else M1, else M3
    if result['method2_current_momentum']:
        headline = result['method2_current_momentum']
    elif result['method1_lifetime_avg_monthly']:
        headline = result['method1_lifetime_avg_monthly']
    else:
        headline = result['method3_listing_rollup']

    result['estimated_monthly_sales'] = headline

    # Confidence: cross-validate only reliable signals (exclude M2 if it was skipped)
    reliable_signals = [v for v in [
        result['method1_lifetime_avg_monthly'],
        result['method2_current_momentum'],  # None if skipped
        result['method3_listing_rollup'],
    ] if v is not None]

    if len(reliable_signals) >= 2:
        lo, hi = min(reliable_signals), max(reliable_signals)
        divergence = (hi - lo) / hi if hi > 0 else 0
        if divergence <= 0.4:
            result['confidence'] = 'high'
        elif divergence <= 0.7:
            result['confidence'] = 'medium'
            notes.append(f'Signals diverge {round(divergence*100)}% — use with caution')
        else:
            result['confidence'] = 'low'
            notes.append(f'Signals diverge {round(divergence*100)}% — pick the lower value as conservative estimate')
    else:
        result['confidence'] = 'medium'
        notes.append('Only one signal available — cannot cross-validate')

    # Trend signal: only meaningful when M2 passed reliability threshold
    m1 = result['method1_lifetime_avg_monthly']
    m2 = result['method2_current_momentum']
    if m1 and m2:
        ratio = m2 / m1
        if ratio >= 1.3:
            result['trend_signal'] = 'growing'
        elif ratio <= 0.6:
            result['trend_signal'] = 'declining'
        else:
            result['trend_signal'] = 'stable'
    elif m1 and not m2:
        result['trend_signal'] = 'unknown'

    return result


# ── Load listing rollup from competitors.json ─────────────────────────────────

def build_listing_rollups(competitors_path):
    if not competitors_path.exists():
        return {}
    data = json.loads(competitors_path.read_text())
    rollup = {}
    for item in data:
        shop = item.get('shop_name', '').strip()
        rev_sum = item.get('reviews') or 0
        if shop:
            rollup[shop] = rollup.get(shop, 0) + rev_sum
    return rollup


# ── Top shops from competitors.json ───────────────────────────────────────────

def top_shops_from_competitors(competitors_path, top_n):
    if not competitors_path.exists():
        return []
    data = json.loads(competitors_path.read_text())
    best = {}
    for item in data:
        shop = item.get('shop_name', '').strip()
        rev_sum = item.get('reviews') or 0
        if shop:
            best[shop] = best.get(shop, 0) + rev_sum
    ranked = sorted(best.items(), key=lambda x: -x[1])
    return [s for s, _ in ranked[:top_n]]


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Build shop-watchlist.json for a niche')
    parser.add_argument('--niche', required=True, help='Project slug, e.g. personalized-gift-for-dad')
    parser.add_argument('--shops', nargs='+', help='Specific shop names to scrape')
    parser.add_argument('--top', type=int, default=8,
                        help='Auto-pick top N shops from competitors.json (default: 8)')
    parser.add_argument('--workers', type=int, default=3,
                        help='Parallel Firecrawl workers (default: 3)')
    args = parser.parse_args()

    research_dir = BASE_DIR / 'projects' / args.niche / '01-research'
    raw_dir = research_dir / 'raw-shops'
    raw_dir.mkdir(parents=True, exist_ok=True)

    competitors_path = research_dir / 'competitors.json'
    out_path = research_dir / 'shop-watchlist.json'

    # Determine which shops to scrape
    if args.shops:
        shop_names = args.shops
    else:
        shop_names = top_shops_from_competitors(competitors_path, args.top)
        if not shop_names:
            print("✗ No shop names found in competitors.json and no --shops provided")
            return 1

    rollups = build_listing_rollups(competitors_path)

    print(f"\n── Shop Watchlist: {args.niche} ──")
    print(f"Shops to scrape : {len(shop_names)}")
    print(f"Firecrawl calls : 1 shop page + up to 20 review pages per shop (stops at 5mo lookback)")
    print(f"Workers         : {args.workers}\n")

    # Phase 1 — scrape shop pages in parallel
    print("Phase 1/2 — Shop pages")
    raw_results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(scrape_shop, s, raw_dir): s for s in shop_names}
        for i, fut in enumerate(as_completed(futures), 1):
            shop, content, err = fut.result()
            if err:
                print(f"  [{i:2d}/{len(shop_names)}] {shop:<35} ✗ {err}")
                raw_results[shop] = None
            else:
                size_kb = len(content) // 1024
                print(f"  [{i:2d}/{len(shop_names)}] {shop:<35} ✓ {size_kb}KB")
                raw_results[shop] = content

    # Phase 2 — scrape review pages in parallel
    print(f"\nPhase 2/2 — Review pages (dynamic, up to 20 pages / 5mo per shop)")
    review_results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(scrape_reviews_pages, s, raw_dir): s for s in shop_names}
        for i, fut in enumerate(as_completed(futures), 1):
            shop = futures[fut]
            dates = fut.result()
            review_results[shop] = dates
            pages_scraped = len(list((raw_dir).glob(f'{shop}-reviews-p*.md')))
            span = (dates[0] - dates[-1]).days if len(dates) >= 2 else 0
            print(f"  [{i:2d}/{len(shop_names)}] {shop:<35} {len(dates)} reviews · {span}d span · {pages_scraped}p scraped")

    # Estimate each shop
    print()
    watchlist = []
    for shop in shop_names:
        content = raw_results.get(shop)
        if not content:
            watchlist.append({
                'shop_name': shop,
                'etsy_url': f'https://www.etsy.com/shop/{shop}',
                'error': 'scrape failed',
            })
            continue
        entry = estimate_shop(shop, content, rollups.get(shop), review_results.get(shop, []))
        watchlist.append(entry)

        m1 = entry.get('method1_lifetime_avg_monthly')
        m2 = entry.get('method2_current_momentum')
        m3 = entry.get('method3_listing_rollup')
        headline = entry.get('estimated_monthly_sales', '?')
        trend = entry.get('trend_signal', '') or ''
        conf = entry.get('confidence', '?')
        trend_icon = {'growing': '↑', 'declining': '↓', 'stable': '→'}.get(trend, ' ')
        trend_short = trend.split()[0] if trend else '?'

        print(f"  {shop:<35}  est={headline}/mo  M1={m1} M2={m2} M3={m3}  {trend_icon} {trend_short}  [{conf}]")

    # Sort by estimated_monthly_sales descending
    watchlist.sort(
        key=lambda x: x.get('estimated_monthly_sales') or 0,
        reverse=True
    )

    out_path.write_text(json.dumps(watchlist, indent=2))
    print(f"\n✓ Saved → {out_path}")
    print(f"  {len(watchlist)} shops · sorted by estimated monthly sales (shop-level)")

    # Summary table
    print()
    print(f"  {'Shop':<35}  {'Est/mo':>7}  {'Trend':>9}  {'Conf':>6}  {'Total Sales':>11}")
    print('  ' + '─' * 78)
    for e in watchlist:
        if 'error' in e:
            print(f"  {e['shop_name']:<35}  {'ERROR':>7}")
            continue
        trend_display = (e.get('trend_signal') or 'unknown').split()[0]
        print(
            f"  {e['shop_name']:<35}"
            f"  {str(e.get('estimated_monthly_sales') or '?'):>7}"
            f"  {trend_display:>9}"
            f"  {(e.get('confidence') or '?'):>6}"
            f"  {str(e.get('total_sales') or '?'):>11}"
        )

    return 0


if __name__ == '__main__':
    exit(main())
