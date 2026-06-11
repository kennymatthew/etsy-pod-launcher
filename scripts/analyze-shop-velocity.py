#!/usr/bin/env python3
"""
analyze-shop-velocity.py

Parses raw-shops review pages to compute per-shop review velocity.
Uses reviews as a sales proxy (industry standard: ~10% review rate for apparel).

Outputs:
  - Console: momentum table sorted by momentum ratio
  - shop-velocity.json: full data for downstream use

Usage:
  python3 scripts/analyze-shop-velocity.py --niche dog-mom
  python3 scripts/analyze-shop-velocity.py --niche dog-mom --review-rate 0.08
  python3 scripts/analyze-shop-velocity.py --niche dog-mom --scrape-date 2026-06-06
"""

import argparse
import datetime
import json
import re
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}

# Etsy apparel review rate: ~10% of buyers leave a review
DEFAULT_REVIEW_RATE = 0.10


def parse_date(date_str):
    """Parse 'Jun 6, 2026' → datetime.date"""
    m = re.match(r'(\w+)\s+(\d+),\s+(\d{4})', date_str.strip())
    if not m:
        return None
    month = MONTH_MAP.get(m.group(1).lower())
    if not month:
        return None
    return datetime.date(int(m.group(3)), month, int(m.group(2)))


def extract_review_dates(md_text):
    """Extract reviewer dates from raw shop review page markdown.
    Excludes seller 'responded on' lines."""
    dates = []
    for line in md_text.splitlines():
        # Skip seller response lines
        if 'responded on' in line.lower():
            continue
        m = re.search(r'\bon\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+,\s+\d{4})', line)
        if m:
            d = parse_date(m.group(1))
            if d:
                dates.append(d)
    return dates


def load_shop_dates(raw_dir, shop_name):
    """Load all review dates across all pages for a shop."""
    pages = sorted(raw_dir.glob(f"{shop_name}-reviews-p*.md"))
    all_dates = []
    for page in pages:
        text = page.read_text(encoding='utf-8', errors='ignore')
        all_dates.extend(extract_review_dates(text))
    return all_dates


def compute_velocity(dates, scrape_date, window_7=7, window_30=30):
    """Count reviews in 7d and 30d windows ending on scrape_date."""
    cutoff_7 = scrape_date - datetime.timedelta(days=window_7)
    cutoff_30 = scrape_date - datetime.timedelta(days=window_30)
    reviews_7d = sum(1 for d in dates if cutoff_7 <= d <= scrape_date)
    reviews_30d = sum(1 for d in dates if cutoff_30 <= d <= scrape_date)
    return reviews_7d, reviews_30d



def main():
    parser = argparse.ArgumentParser(description='Analyze shop review velocity as sales proxy')
    parser.add_argument('--niche', required=True)
    parser.add_argument('--review-rate', type=float, default=DEFAULT_REVIEW_RATE,
                        help='Fraction of buyers who leave a review (default: 0.10)')
    parser.add_argument('--scrape-date', default=None,
                        help='Date scrape was taken YYYY-MM-DD (default: auto-detect from newest review date)')
    args = parser.parse_args()

    research_dir = BASE_DIR / 'projects' / args.niche / '01-research'
    raw_dir = research_dir / 'raw-shops'

    if not raw_dir.exists():
        print(f"✗ raw-shops directory not found: {raw_dir}")
        return

    # Load shop-watchlist for favorites_per_review and lifetime avg
    watchlist_path = research_dir / 'shop-watchlist.json'
    watchlist_by_shop = {}
    if watchlist_path.exists():
        for entry in json.loads(watchlist_path.read_text()):
            watchlist_by_shop[entry['shop_name']] = entry

    # Discover shops
    shop_names = sorted(set(
        p.name.split('-reviews-p')[0]
        for p in raw_dir.glob('*-reviews-p*.md')
    ))

    if not shop_names:
        print(f"✗ No review pages found in {raw_dir}")
        return

    print(f"\nParsing {len(shop_names)} shops from raw-shops/...\n")

    # Auto-detect scrape date from newest review date across all files
    if args.scrape_date:
        scrape_date = datetime.date.fromisoformat(args.scrape_date)
    else:
        all_sample_dates = []
        for shop in shop_names:
            pages = sorted(raw_dir.glob(f"{shop}-reviews-p1.md"))
            for page in pages:
                text = page.read_text(encoding='utf-8', errors='ignore')
                all_sample_dates.extend(extract_review_dates(text))
        scrape_date = max(all_sample_dates) if all_sample_dates else datetime.date.today()
        print(f"  Auto-detected scrape date: {scrape_date}\n")

    results = []

    for shop in shop_names:
        dates = load_shop_dates(raw_dir, shop)
        if not dates:
            print(f"  ⚠  {shop}: no dates found, skipping")
            continue

        reviews_7d, reviews_30d = compute_velocity(dates, scrape_date)
        expected_weekly = reviews_30d / 4.0  # expected 7d if pace were flat
        momentum_ratio = (reviews_7d / expected_weekly) if expected_weekly > 0 else 0

        # Sales estimates
        est_sales_7d = round(reviews_7d / args.review_rate)
        est_sales_30d = round(reviews_30d / args.review_rate)

        # Favorites per review from watchlist
        w = watchlist_by_shop.get(shop, {})
        lifetime_monthly_avg = w.get('method1_lifetime_avg_monthly')

        # Trend label
        if momentum_ratio >= 1.5:
            trend = '🔥 SURGING'
        elif momentum_ratio >= 1.1:
            trend = '↑ growing'
        elif momentum_ratio >= 0.9:
            trend = '→ stable'
        elif momentum_ratio >= 0.5:
            trend = '↓ cooling'
        else:
            trend = '❄  slow'

        results.append({
            'shop': shop,
            'reviews_7d': reviews_7d,
            'reviews_30d': reviews_30d,
            'expected_weekly_from_30d': round(expected_weekly, 1),
            'momentum_ratio': round(momentum_ratio, 2),
            'trend': trend,
            'est_sales_7d': est_sales_7d,
            'est_sales_30d': est_sales_30d,
            'lifetime_monthly_avg_sales': lifetime_monthly_avg,
            'total_review_dates_found': len(dates),
            'scrape_date': str(scrape_date),
            'review_rate_used': args.review_rate,
        })

    results.sort(key=lambda x: x['momentum_ratio'], reverse=True)

    # Print table
    print(f"{'Shop':<25} {'7d rev':>6} {'30d rev':>7} {'Momentum':>9} {'Est Sales/mo':>13}  Trend")
    print('─' * 78)
    for r in results:
        print(
            f"{r['shop']:<25} "
            f"{r['reviews_7d']:>6} "
            f"{r['reviews_30d']:>7} "
            f"{r['momentum_ratio']:>9.2f}x "
            f"{r['est_sales_30d']:>13,}  {r['trend']}"
        )

    print(f"\n  Scrape date: {scrape_date}  |  Review rate assumed: {args.review_rate:.0%}")
    print(f"  Est sales = reviews ÷ {args.review_rate:.0%} (industry avg for apparel)")
    print(f"  Momentum = 7d reviews ÷ (30d reviews ÷ 4)  —  1.0x = flat pace\n")

    # Save JSON
    out_path = research_dir / 'shop-velocity.json'
    out_path.write_text(json.dumps(results, indent=2))
    print(f"  Saved → {out_path.relative_to(BASE_DIR)}\n")


if __name__ == '__main__':
    main()