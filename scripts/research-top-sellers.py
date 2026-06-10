#!/usr/bin/env python3
"""
research-top-sellers.py

Scrapes Alura's public best-selling Clothing page (no login required).
Returns a ranked list of top Etsy listings with estimated sales data.

Usage:
  python3 scripts/research-top-sellers.py --niche personalized-gift-for-dad

Stability note: Alura could restructure this page at any time.
If the scrape returns minimal content, fall back to the in-house
estimate from competitors.json (reviews field).
"""

import subprocess, json, re, argparse, os, shutil, sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

ALURA_URL = 'https://www.alura.io/best-selling-etsy-items/clothing'


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


def main():
    parser = argparse.ArgumentParser(description='Scrape Alura top-selling Clothing listings')
    parser.add_argument('--niche', required=True, help='Project slug, e.g. personalized-gift-for-dad')
    args = parser.parse_args()

    out_dir = BASE_DIR / 'projects' / args.niche / '01-research'
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / 'top-sellers-clothing-raw.md'
    json_path = out_dir / 'top-sellers-clothing.json'

    print(f"\n── Alura Top Sellers: {args.niche} ──")
    print(f"URL: {ALURA_URL}\n")
    print("Scraping... (4s JS wait for page render)")

    result = subprocess.run(
        [str(FIRECRAWL_BIN), 'scrape', ALURA_URL,
         '--only-main-content', '--wait-for', '4000',
         '-o', str(raw_path)],
        capture_output=True, text=True, timeout=60, env=ENV
    )

    if not raw_path.exists() or raw_path.stat().st_size < 500:
        print("✗ Scrape returned minimal content.")
        print("  Alura may have changed their page layout.")
        print("  Fall back to in-house estimate: competitors.json → reviews")
        return 1

    content = raw_path.read_text()

    # Sanity check: look for sales figures like "13,179"
    has_data = bool(re.search(r'\d{1,3},\d{3}', content))
    size_kb = raw_path.stat().st_size // 1024

    if not has_data:
        print(f"⚠  Scraped {size_kb}KB but no sales figures found — page may have changed.")
        print(f"   Raw file saved for manual inspection: {raw_path}")
        print("   Fall back to in-house estimate: competitors.json → reviews")
        return 1

    print(f"✓ Scraped {size_kb}KB — sales data present")
    print(f"  Raw saved: {raw_path}\n")
    print("── Next step ──")
    print(f'Tell Claude:')
    print()
    print(f'  "Read {raw_path}')
    print(f'   Extract each listing row as a JSON object with fields:')
    print(f'     rank (integer), title (string), etsy_url (string),')
    print(f'     total_sales (integer), monthly_sales (integer), revenue_estimate (string).')
    print(f'   Skip any placeholder/header row (the one with \'Shop name\' and \'123,123\').')
    print(f'   Return a JSON array, no explanation.')
    print(f'   Save to: {json_path}"')
    print()
    print('Then search the saved JSON:')
    print('  "Search top-sellers-clothing.json for [your keyword].')
    print('   Report how many listings match and their monthly_sales."')
    print()
    print('Demand signal:')
    print('  3+ matches with monthly_sales > 100  →  demand confirmed at top-seller level')
    print('  0 matches                             →  niche may be new/underserved — proceed to Phase 1 cautiously')
    return 0


if __name__ == '__main__':
    exit(main())
