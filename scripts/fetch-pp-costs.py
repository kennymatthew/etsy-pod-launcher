#!/usr/bin/env python3
"""
fetch-pp-costs.py

Fetches print provider costs for a Printify blueprint from the Printify API.
Prints a comparison table sorted by average cost (S–2XL) so you can pick a PP
before committing to a product. Requires PRINTIFY_API_TOKEN in .env.

Usage:
  python3 scripts/fetch-pp-costs.py --blueprint 12
  python3 scripts/fetch-pp-costs.py --blueprint 12 --pp 29   # single PP detail
  python3 scripts/fetch-pp-costs.py --list-blueprints        # search catalog

Examples:
  Blueprint 12  = Gildan Heavy Cotton (5000)
  Blueprint 145 = Bella+Canvas 3001
  Blueprint 470 = Comfort Colors 1717
"""

import argparse, json, os, sys, re
from pathlib import Path

try:
    import requests
except ImportError:
    print("✗ requests not installed. Run: pip install requests")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.parent
API_BASE = 'https://api.printify.com/v1'

SIZE_ORDER = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL']


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


def get_token(env):
    token = env.get('PRINTIFY_API_TOKEN') or env.get('PRINTIFY_TOKEN')
    if not token:
        print("✗ PRINTIFY_API_TOKEN not found in .env")
        sys.exit(1)
    return token


def api_get(path, token):
    resp = requests.get(
        f'{API_BASE}{path}',
        headers={'Authorization': f'Bearer {token}'},
        timeout=20,
    )
    if resp.status_code != 200:
        print(f"✗ API error {resp.status_code}: {resp.text[:200]}")
        sys.exit(1)
    return resp.json()


def avg_cost_s_to_2xl(size_costs):
    """Average cost across S, M, L, XL, 2XL (standard POD range)."""
    target = {'S', 'M', 'L', 'XL', '2XL'}
    vals = [c for sz, c in size_costs.items() if sz in target]
    return round(sum(vals) / len(vals), 2) if vals else 0.0


def extract_size_costs(variants):
    """
    From a list of variant objects, extract a {size: cost_cents} map for
    the first color group (usually 'Black'). Costs are in cents.
    """
    # Group variants by color title
    by_color = {}
    for v in variants:
        opts = {o['name'].lower(): o['value'] for o in v.get('options', [])}
        color = opts.get('color', 'unknown')
        size = opts.get('size', '')
        cost = v.get('cost', 0)
        if color not in by_color:
            by_color[color] = {}
        if size:
            by_color[color][size] = cost

    # Use Black if available, otherwise first color
    color_key = 'Black' if 'Black' in by_color else next(iter(by_color), None)
    if not color_key:
        return {}

    return {sz: cost / 100 for sz, cost in by_color[color_key].items()}


def print_comparison_table(blueprint_id, token):
    blueprint = api_get(f'/catalog/blueprints/{blueprint_id}.json', token)
    print(f"\nBlueprint {blueprint_id}: {blueprint.get('title', 'Unknown')}")
    print('─' * 90)

    providers = api_get(
        f'/catalog/blueprints/{blueprint_id}/print_providers.json', token
    )

    rows = []
    for pp in providers:
        pp_id = pp['id']
        pp_name = pp.get('title', 'Unknown')
        pp_location = pp.get('location', {}).get('country', '?')

        try:
            variants_data = api_get(
                f'/catalog/blueprints/{blueprint_id}/print_providers/{pp_id}/variants.json',
                token,
            )
            variants = variants_data.get('variants', [])
        except SystemExit:
            continue

        if not variants:
            continue

        size_costs = extract_size_costs(variants)
        if not size_costs:
            continue

        avg = avg_cost_s_to_2xl(size_costs)
        margin_list_price = round(avg * 2.5, 2)

        rows.append({
            'pp_id': pp_id,
            'name': pp_name,
            'location': pp_location,
            'size_costs': size_costs,
            'avg': avg,
            'min_list_price': margin_list_price,
        })

    rows.sort(key=lambda r: r['avg'])

    # Determine which sizes to show
    all_sizes = set()
    for r in rows:
        all_sizes.update(r['size_costs'].keys())
    show_sizes = [s for s in SIZE_ORDER if s in all_sizes]

    # Header
    size_cols = '  '.join(f'{s:>6}' for s in show_sizes)
    print(f"{'PP ID':>6}  {'Provider':<28}  {'Loc':>4}  {size_cols}  {'Avg':>7}  {'Min $@60%':>9}")
    print('─' * 90)

    for r in rows:
        costs = '  '.join(
            f'${r["size_costs"].get(s, 0):>5.2f}' for s in show_sizes
        )
        flag = ' ← recommended' if r['avg'] == rows[0]['avg'] else ''
        print(
            f"{r['pp_id']:>6}  {r['name']:<28}  {r['location']:>4}  "
            f"{costs}  ${r['avg']:>6.2f}  ${r['min_list_price']:>8.2f}{flag}"
        )

    print()
    print('Min $@60% = minimum list price to hit 60% margin (cost × 2.5)')
    print()

    if rows:
        best = rows[0]
        print(f"Lowest avg cost: {best['name']} (ID {best['pp_id']}) @ ${best['avg']:.2f}/unit avg")
        print(f"  → List at ${best['min_list_price']:.2f} or higher to clear 60% margin")


def list_blueprints(token, query=None):
    data = api_get('/catalog/blueprints.json', token)
    blueprints = data if isinstance(data, list) else data.get('data', [])

    print(f"\n{'ID':>6}  {'Title'}")
    print('─' * 60)
    for bp in blueprints:
        title = bp.get('title', '')
        if query and query.lower() not in title.lower():
            continue
        print(f"{bp['id']:>6}  {title}")


def main():
    parser = argparse.ArgumentParser(description='Compare Printify print provider costs')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--blueprint', type=int, help='Blueprint ID to compare providers for')
    group.add_argument('--list-blueprints', action='store_true', help='List all catalog blueprints')
    parser.add_argument('--search', help='Filter blueprint list by keyword (use with --list-blueprints)')
    args = parser.parse_args()

    env = load_env()
    token = get_token(env)

    if args.list_blueprints:
        list_blueprints(token, query=args.search)
    else:
        print_comparison_table(args.blueprint, token)


if __name__ == '__main__':
    main()
