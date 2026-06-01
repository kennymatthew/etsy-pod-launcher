#!/usr/bin/env python3
"""
research-competitors.py

Scrapes top Etsy competitor listings for a niche using Firecrawl.
Saves clean markdown files to .firecrawl/ cache, then outputs a manifest
so Claude can read the files and produce competitors.json.

Usage:
  python3 scripts/research-competitors.py --niche save-the-date-tshirts --query "save the date t shirts"
  python3 scripts/research-competitors.py --niche funny-cat-shirts --query "funny cat shirt" --count 5
"""

import subprocess, json, re, argparse, datetime, os, shutil, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).parent.parent

def _find_firecrawl():
    found = shutil.which('firecrawl')
    if found:
        return Path(found)
    # fallback: common npm global locations
    for p in [Path.home() / '.npm-global/bin/firecrawl',
              Path('/usr/local/bin/firecrawl'),
              Path('/opt/homebrew/bin/firecrawl')]:
        if p.exists():
            return p
    print("✗ firecrawl CLI not found. Install it with: npm install -g firecrawl")
    print("  Then get a free API key at https://www.firecrawl.dev/app/api-keys")
    print("  and set FIRECRAWL_API_KEY in your .env file.")
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

def firecrawl_scrape(url, output_path, wait_ms=3000):
    result = subprocess.run(
        [str(FIRECRAWL_BIN), 'scrape', url, '--only-main-content',
         '--wait-for', str(wait_ms), '-o', str(output_path)],
        capture_output=True, text=True, timeout=90, env=ENV
    )
    if not output_path.exists() or output_path.stat().st_size < 200:
        return False
    # reject Etsy "item unavailable" pages — file exists but listing is dead
    content_start = output_path.read_text()[:500].lower()
    if 'this item is unavailable' in content_start:
        output_path.unlink()
        return False
    return True

def firecrawl_search(query, limit=5):
    """Use firecrawl search (backed by Google) to find Etsy listing URLs."""
    result = subprocess.run(
        [str(FIRECRAWL_BIN), 'search',
         f'{query} site:etsy.com/listing',
         '--limit', str(limit)],
        capture_output=True, text=True, timeout=30, env=ENV
    )
    pattern = r'https://www\.etsy\.com/listing/(\d+)/[^\s\)\"]*'
    seen, urls = set(), []
    for listing_id in re.findall(pattern, result.stdout):
        if listing_id not in seen:
            seen.add(listing_id)
            urls.append(f"https://www.etsy.com/listing/{listing_id}/")
    return urls[:limit]

def scrape_one_listing(args):
    url, idx, scrapes_dir = args
    listing_id = re.search(r'/listing/(\d+)/', url).group(1)
    output = scrapes_dir / f'etsy-listing-{listing_id}.md'
    if output.exists() and output.stat().st_size > 500:
        print(f"  [{idx+1}] cached  — {listing_id}")
        return url, str(output), True
    print(f"  [{idx+1}] scraping — {listing_id} ...")
    ok = firecrawl_scrape(url, output, wait_ms=2500)
    status = "✓" if ok else "✗"
    print(f"  [{idx+1}] {status}       — {listing_id}")
    return url, str(output) if ok else None, ok

def main():
    parser = argparse.ArgumentParser(description='Scrape Etsy competitors with Firecrawl')
    parser.add_argument('--niche', required=True, help='Project slug, e.g. save-the-date-tshirts')
    parser.add_argument('--query', required=True, help='Etsy search query, e.g. "save the date t shirts"')
    parser.add_argument('--count', type=int, default=5, help='Number of listings to scrape (default 5)')
    args = parser.parse_args()

    project_dir = BASE_DIR / 'projects' / args.niche / '01-research'
    scrapes_dir = project_dir / 'scrapes'
    scrapes_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n── Competitor Research: {args.niche} ──")
    print(f"Query : {args.query}")
    print(f"Scrapes: projects/{args.niche}/01-research/scrapes/")
    print(f"Output : {project_dir / 'competitors.json'}\n")

    # Step 1: use firecrawl search to find listing URLs (avoids Etsy bot detection)
    print("Step 1/3  Finding top Etsy listings via Firecrawl search...")
    urls = firecrawl_search(args.query, limit=args.count)
    if not urls:
        print("  ✗ No listing URLs found. Check your Firecrawl API key or try a different query.")
        return 1
    print(f"  Found {len(urls)} listings:")
    for i, u in enumerate(urls, 1):
        print(f"    {i}. {u}")

    # Step 3: scrape listings in parallel (max 3 concurrent)
    print(f"\nStep 3/3  Scraping {len(urls)} listings in parallel...")
    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(scrape_one_listing, (url, i, scrapes_dir)): i for i, url in enumerate(urls)}
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: urls.index(r[0]) if r[0] in urls else 99)
    scraped = [(url, path) for url, path, ok in results if ok and path]

    # Save manifest
    manifest = {
        "niche": args.niche,
        "query": args.query,
        "scraped_date": datetime.date.today().isoformat(),
        "listing_urls": urls,
        "scraped_files": [{"url": u, "file": p} for u, p in scraped],
        "output_target": str(project_dir / 'competitors.json'),
        "next_step": f"Ask Claude: 'Read projects/{args.niche}/01-research/scrapes/manifest.json and create competitors.json'"
    }
    manifest_path = scrapes_dir / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"\n── Done ──")
    print(f"Scraped : {len(scraped)}/{len(urls)} listings")
    print(f"Manifest: {manifest_path}")
    print(f"\nNext step — tell Claude:")
    print(f'  "Read projects/{args.niche}/01-research/scrapes/manifest.json and create competitors.json"')
    return 0

if __name__ == '__main__':
    exit(main())
