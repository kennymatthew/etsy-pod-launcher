#!/usr/bin/env python3
"""
research-autocomplete.py

Automates the Etsy autocomplete check (Phase 0 Step 0.1).
Opens a fresh US browser context, types each query variant into
Etsy's search box, and captures autocomplete suggestions.

Usage:
  python3 scripts/research-autocomplete.py --niche personalized-gift-for-dad --query "nurse"
  python3 scripts/research-autocomplete.py --niche personalized-gift-for-dad --query "nurse" --letters "abcfghst"
"""

import argparse, json, re, time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Selectors for autocomplete suggestions — tried in order until one returns results
SUGGESTION_SELECTORS = [
    '[role="option"]',
    '[role="listbox"] li',
    '[role="listbox"] a',
    '[data-search-suggestions] li',
    '[class*="search-suggestion"] li',
    '[class*="autocomplete"] li',
    '[class*="SearchSuggestion"] li',
]


def capture_suggestions(page, query):
    try:
        search_input = page.locator('input[name="search_query"]').first
        if not search_input.is_visible(timeout=3000):
            search_input = page.locator('input[type="search"]').first

        search_input.click()
        search_input.fill('')
        time.sleep(0.3)
        search_input.type(query, delay=60)
        time.sleep(1.2)

        for selector in SUGGESTION_SELECTORS:
            try:
                items = page.locator(selector).all()
                if not items:
                    continue
                texts = []
                for item in items:
                    t = item.inner_text().strip()
                    # Skip empty strings, UI chrome, and navigation items
                    if t and len(t) > 2 and not t.lower().startswith(('search for', 'in all', 'see all')):
                        texts.append(t)
                if texts:
                    return texts
            except Exception:
                continue

        return []

    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description='Capture Etsy autocomplete suggestions')
    parser.add_argument('--niche', required=True, help='Project slug, e.g. personalized-gift-for-dad')
    parser.add_argument('--query', required=True, help='Base keyword, e.g. "nurse"')
    parser.add_argument('--letters', default='abcfghst',
                        help='Letter suffixes to append (default: abcfghst)')
    args = parser.parse_args()

    out_dir = BASE_DIR / 'projects' / args.niche / '01-research'
    out_dir.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r'[^a-z0-9]+', '-', args.query.lower()).strip('-')
    out_path = out_dir / f'autocomplete-{slug}.json'

    variants = [args.query] + [f"{args.query} {c}" for c in args.letters]

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("✗ playwright not installed.")
        print("  Run: pip install playwright && playwright install chromium")
        return 1

    results = {}

    print(f"\n── Etsy Autocomplete: \"{args.query}\" ──")
    print(f"Variants : {len(variants)} queries  (base + letters: {args.letters})")
    print(f"Context  : US locale · New York geolocation · fresh session (not logged in)\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            locale='en-US',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # New York
            timezone_id='America/New_York',
            permissions=['geolocation'],
        )
        page = context.new_page()
        page.goto('https://www.etsy.com', wait_until='domcontentloaded')
        time.sleep(2)

        for i, variant in enumerate(variants):
            suggestions = capture_suggestions(page, variant)
            results[variant] = suggestions
            status = f"{len(suggestions)} suggestions" if suggestions else "no suggestions captured"
            print(f"  [{i+1:2d}/{len(variants)}] \"{variant}\" → {status}")
            for s in suggestions[:4]:
                print(f"            · {s}")
            time.sleep(0.6)

        browser.close()

    # Rank phrases by frequency across variants (appears in multiple = higher buyer intent)
    freq = {}
    for suggestions in results.values():
        for s in suggestions:
            key = s.lower().strip()
            freq[key] = freq.get(key, 0) + 1

    seen, ranked = set(), []
    for suggestions in results.values():
        for s in suggestions:
            key = s.lower().strip()
            if key not in seen:
                seen.add(key)
                ranked.append(s)
    ranked.sort(key=lambda s: freq[s.lower().strip()], reverse=True)

    output = {
        'query': args.query,
        'letters': args.letters,
        'total_unique_phrases': len(ranked),
        'all_phrases_ranked': ranked,
        'by_variant': results,
    }

    out_path.write_text(json.dumps(output, indent=2))

    print(f"\n── Top phrases (★ = appeared in 2+ letter variants) ──")
    for phrase in ranked[:20]:
        star = ' ★' if freq[phrase.lower().strip()] > 1 else ''
        print(f"  {phrase}{star}")

    print(f"\n✓ Saved → {out_path}")
    print(f"  {len(ranked)} unique phrases across {len(variants)} variants")
    return 0


if __name__ == '__main__':
    exit(main())
