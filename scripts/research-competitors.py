#!/usr/bin/env python3
"""
research-competitors.py

Flow:
  1. Scrape 1 page of Etsy best-seller search results for the query (US, physical items only)
  2. Extract all listing IDs from that page (~30-48 listings)
  3. Scrape each listing individually with --only-main-content for full details
  4. Save manifest so Claude can build competitors.json

Usage:
  python3 scripts/research-competitors.py --niche personalized-gift-for-dad --query "personalized gift for dad"
  python3 scripts/research-competitors.py --niche dad-shirt --query "custom dad shirt" --count 10
"""

import subprocess, json, re, argparse, datetime, os, shutil, sys, urllib.parse
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

def build_etsy_search_url(query):
    """Build Etsy best-seller search URL: US sellers, physical items, best sellers only."""
    encoded = urllib.parse.quote(query)
    return (
        f"https://www.etsy.com/search?q={encoded}"
        f"&instant_download=false&explicit=1&is_best_seller=true&locationQuery=6252001"
    )

def scrape_search_page(query, scrapes_dir):
    """
    Scrape 1 page of Etsy best-seller results.
    Returns list of listing URLs extracted from the page.
    """
    url = build_etsy_search_url(query)
    slug = re.sub(r'[^a-z0-9]+', '-', query.lower()).strip('-')
    output_path = scrapes_dir / f"search-{slug}-p1.md"

    print(f"  URL: {url}")

    result = subprocess.run(
        [str(FIRECRAWL_BIN), 'scrape', url, '-o', str(output_path)],
        capture_output=True, text=True, timeout=90, env=ENV
    )

    if not output_path.exists() or output_path.stat().st_size < 200:
        print("  ✗ Search page scrape failed or returned empty content")
        return url, []

    content = output_path.read_text()

    # Extract listing IDs in order, deduplicated
    seen, ids = set(), []
    for match in re.finditer(r'etsy\.com/listing/(\d+)/', content):
        lid = match.group(1)
        if lid not in seen:
            seen.add(lid)
            ids.append(lid)

    listing_urls = [f"https://www.etsy.com/listing/{lid}/" for lid in ids]
    print(f"  Found {len(listing_urls)} listings")
    return url, listing_urls

def scrape_one_listing(args):
    url, idx, scrapes_dir = args
    listing_id = re.search(r'/listing/(\d+)/', url).group(1)
    output = scrapes_dir / f'etsy-listing-{listing_id}.md'

    if output.exists() and output.stat().st_size > 500:
        print(f"  [{idx+1}] cached   — {listing_id}")
        return url, str(output), True

    print(f"  [{idx+1}] scraping — {listing_id} ...")
    result = subprocess.run(
        [str(FIRECRAWL_BIN), 'scrape', url, '--only-main-content',
         '--wait-for', '2500', '-o', str(output)],
        capture_output=True, text=True, timeout=90, env=ENV
    )

    if not output.exists() or output.stat().st_size < 200:
        print(f"  [{idx+1}] ✗         — {listing_id} (empty)")
        return url, None, False

    content_start = output.read_text()[:500].lower()
    if 'this item is unavailable' in content_start:
        output.unlink()
        print(f"  [{idx+1}] ✗         — {listing_id} (unavailable)")
        return url, None, False

    print(f"  [{idx+1}] ✓         — {listing_id}")
    return url, str(output), True

def main():
    parser = argparse.ArgumentParser(description='Scrape Etsy best-seller competitors')
    parser.add_argument('--niche', required=True, help='Project slug, e.g. personalized-gift-for-dad')
    parser.add_argument('--query', required=True, help='Search term, e.g. "custom dad shirt"')
    parser.add_argument('--count', type=int, default=None, help='Max listings to scrape (default: all found on page)')
    args = parser.parse_args()

    project_dir = BASE_DIR / 'projects' / args.niche / '01-research'
    scrapes_dir = project_dir / 'scrapes'
    scrapes_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n── Competitor Research: {args.niche} ──")
    print(f"Query  : {args.query}")
    print(f"Scrapes: projects/{args.niche}/01-research/scrapes/\n")

    # Step 1: scrape the Etsy best-seller search page
    print("Step 1/2  Scraping Etsy best-seller search page...")
    search_url, listing_urls = scrape_search_page(args.query, scrapes_dir)

    if not listing_urls:
        print("  ✗ No listing URLs found. Check your API key or try a different query.")
        return 1

    if args.count:
        listing_urls = listing_urls[:args.count]
        print(f"  Limiting to {args.count} listings (--count flag)")

    # Step 2: scrape each listing individually
    print(f"\nStep 2/2  Scraping {len(listing_urls)} listings in parallel (max 3 concurrent)...")
    raw_results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(scrape_one_listing, (url, i, scrapes_dir)): i
            for i, url in enumerate(listing_urls)
        }
        for future in as_completed(futures):
            raw_results.append(future.result())

    raw_results.sort(key=lambda r: listing_urls.index(r[0]) if r[0] in listing_urls else 99)
    scraped = [(url, path) for url, path, ok in raw_results if ok and path]

    # Save manifest
    manifest = {
        "niche": args.niche,
        "query": args.query,
        "etsy_search_url": search_url,
        "scraped_date": datetime.date.today().isoformat(),
        "listing_urls": listing_urls,
        "scraped_files": [{"url": u, "file": p} for u, p in scraped],
        "output_target": str(project_dir / 'competitors.json'),
        "next_step": f"Ask Claude: 'Read projects/{args.niche}/01-research/scrapes/manifest.json and create competitors.json'"
    }
    (scrapes_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2))

    print(f"\n── Done ──")
    print(f"Scraped : {len(scraped)}/{len(listing_urls)} listings")
    print(f"Saved   : projects/{args.niche}/01-research/scrapes/")
    print(f"\nNext step — tell Claude:")
    print(f'  "Read projects/{args.niche}/01-research/scrapes/manifest.json and create competitors.json"')
    return 0

if __name__ == '__main__':
    exit(main())
