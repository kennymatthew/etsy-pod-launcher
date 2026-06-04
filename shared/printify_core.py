"""
shared/printify_core.py — reusable Printify API functions.

Usage in any niche script:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../shared'))
    import printify_core as pc

    pc.load_env(__file__)
    pc.configure(token=os.environ["PRINTIFY_API_TOKEN"], shop_id=os.environ["PRINTIFY_SHOP_ID"])
"""

import os
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path

_token   = ""
_shop_id = ""
_base    = "https://api.printify.com/v1"
_headers: dict = {}


# ── Setup ─────────────────────────────────────────────────────────────────────

def load_env(from_file=None):
    """Walk up from from_file (or cwd) to find .env and load it into os.environ."""
    start = Path(from_file).resolve().parent if from_file else Path.cwd()
    p = start
    for _ in range(8):
        env = p / ".env"
        if env.exists():
            with open(env) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
            return
        p = p.parent


def configure(token: str, shop_id: str):
    """Call once at startup before any API call."""
    global _token, _shop_id, _headers
    _token   = token
    _shop_id = shop_id
    _headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "User-Agent":    "printify-bridge",
    }


# ── API helper ────────────────────────────────────────────────────────────────

def api(method: str, path: str, body=None):
    url  = f"{_base}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req  = urllib.request.Request(url, data=data, headers=_headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} → HTTP {e.code}: {e.read().decode()}") from e


# ── Images ────────────────────────────────────────────────────────────────────

def upload_image(filename: str, design_dir) -> str:
    """Upload a PNG from design_dir, return Printify image ID."""
    filepath = Path(design_dir) / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Design file not found: {filepath}")
    contents = base64.b64encode(filepath.read_bytes()).decode()
    result   = api("POST", "/uploads/images.json", {"file_name": filename, "contents": contents})
    return result["id"]


# ── Variants ──────────────────────────────────────────────────────────────────

def get_variant_groups(blueprint_id, print_provider_id, allowed_sizes, dark_colors, light_colors):
    """
    Returns (dark_ids, light_ids_by_color) from the catalog.
    dark_ids            — flat list of variant IDs for dark-colored shirts
    light_ids_by_color  — dict: color_name → [variant_ids]
    Raises if total > 100 (Printify cap) or == 0 (color name mismatch).
    """
    data = api("GET", f"/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json")
    dark_ids           = []
    light_ids_by_color: dict = {}
    seen               = set()

    for v in data["variants"]:
        color = v["options"]["color"]
        size  = v["options"]["size"]
        if size not in allowed_sizes:
            continue
        if color in dark_colors:
            dark_ids.append(v["id"])
            seen.add(color)
        elif color in light_colors:
            light_ids_by_color.setdefault(color, []).append(v["id"])
            seen.add(color)

    all_light = [vid for ids in light_ids_by_color.values() for vid in ids]
    total = len(dark_ids) + len(all_light)
    if total > 100:
        raise RuntimeError(f"{total} variants selected — over Printify's 100-variant cap")
    if total == 0:
        raise RuntimeError("0 variants selected — check that color names match API exactly")

    missing = (dark_colors | light_colors) - seen
    if missing:
        print(f"  ⚠️  Colors not found in catalog: {missing}")

    print(f"  Dark  shirts: {len(dark_ids):3d} variants")
    print(f"  Light shirts: {len(all_light):3d} variants  |  Total: {total}")

    return dark_ids, light_ids_by_color


def build_variants(all_ids: list, initial_price_cents: int = 2000) -> list:
    """Build the variants list for product creation (placeholder price, repriced later)."""
    return [{"id": vid, "price": initial_price_cents, "is_enabled": True} for vid in all_ids]


# ── Print areas ───────────────────────────────────────────────────────────────

def build_initial_print_areas(dark_ids, light_ids_by_color, dark_img_id, light_img_id, placement) -> list:
    """
    Temporary 2-group print_areas for the initial POST.
    Always follow immediately with rebuild_print_areas_dark_light().
    """
    all_light = [vid for ids in light_ids_by_color.values() for vid in ids]
    p = placement
    return [
        {
            "variant_ids": dark_ids,
            "placeholders": [{"position": "front", "decoration_method": "dtg",
                              "images": [{"id": dark_img_id, **p}]}],
        },
        {
            "variant_ids": all_light,
            "placeholders": [{"position": "front", "decoration_method": "dtg",
                              "images": [{"id": light_img_id, **p}]}],
        },
    ]


def rebuild_print_areas_dark_light(product_id, dark_img_id, light_img_id, placement, light_colors) -> int:
    """
    After creation, fetch the product's full variant list and rebuild print_areas as:
      print_area[0]   (default)  — all non-light variants         → dark-ink design (white ink on dark shirts)
      print_area[1..N](specific) — one per light color, 8 each   → light-ink design (black ink on light shirts)

    Must be called immediately after create_product(). Uses the product variant list (not catalog)
    because Printify adds ~7 discontinued variants post-creation (~255 total vs ~248 in catalog).
    Printify's editor and auto-generated Etsy mockups only render correctly with this per-color structure.

    Returns the number of print_areas created (1 default + N light colors).
    """
    p_obj = api("GET", f"/shops/{_shop_id}/products/{product_id}.json")

    by_color: dict = {}
    for v in p_obj["variants"]:
        color = v["title"].rsplit(" / ", 1)[0]
        by_color.setdefault(color, []).append(v["id"])

    light_by_color = {c: ids for c, ids in by_color.items() if c in light_colors}
    all_light_ids  = {vid for ids in light_by_color.values() for vid in ids}
    non_light_ids  = [v["id"] for v in p_obj["variants"] if v["id"] not in all_light_ids]

    p = placement
    print_areas = [
        {
            "variant_ids": non_light_ids,
            "placeholders": [{"position": "front", "decoration_method": "dtg",
                              "images": [{"id": dark_img_id, **p}]}],
        }
    ]
    for color in sorted(light_by_color):
        print_areas.append({
            "variant_ids": light_by_color[color],
            "placeholders": [{"position": "front", "decoration_method": "dtg",
                              "images": [{"id": light_img_id, **p}]}],
        })

    api("PUT", f"/shops/{_shop_id}/products/{product_id}.json", {"print_areas": print_areas})
    return len(print_areas)


# ── Product ───────────────────────────────────────────────────────────────────

def get_product_placement(product_id) -> dict:
    """
    Fetch x/y/scale/angle from an existing product's first print_area.
    Use this after verifying placement in the Printify editor, when you want
    to apply the same verified placement to additional listings (same design template).
    Returns {"x": ..., "y": ..., "scale": ..., "angle": ...}
    """
    p_obj = api("GET", f"/shops/{_shop_id}/products/{product_id}.json")
    img   = p_obj["print_areas"][0]["placeholders"][0]["images"][0]
    return {"x": img["x"], "y": img["y"], "scale": img["scale"], "angle": img["angle"]}


def sync_placement_across_print_areas(product_id) -> dict:
    """
    After the user adjusts placement in the Printify editor, fetch the product and
    find which print_area was changed (the editor only updates the one variant being viewed).
    Apply that placement to ALL print_areas, preserving each area's image ID.

    Detection: collect all placements, find the outlier (the one that differs from the
    majority). If all are identical, nothing changed — returns the unchanged placement.

    Returns the placement dict that was synced.
    """
    p_obj = api("GET", f"/shops/{_shop_id}/products/{product_id}.json")

    def _placement(pa):
        img = pa["placeholders"][0]["images"][0]
        return (img["x"], img["y"], img["scale"], img["angle"])

    placements = [_placement(pa) for pa in p_obj["print_areas"]]

    # Find the placement that appears least often (the outlier = what the user changed)
    from collections import Counter
    counts = Counter(placements)
    canonical_tuple = min(counts, key=lambda k: counts[k])  # least common = the edited one

    # If there's a tie (e.g. all identical), fall back to print_area[0]
    if len(counts) == 1:
        canonical_tuple = placements[0]

    placement = {"x": canonical_tuple[0], "y": canonical_tuple[1],
                 "scale": canonical_tuple[2], "angle": canonical_tuple[3]}

    updated_print_areas = []
    for pa in p_obj["print_areas"]:
        img = pa["placeholders"][0]["images"][0]
        updated_print_areas.append({
            "variant_ids": pa["variant_ids"],
            "placeholders": [{"position": "front", "decoration_method": "dtg",
                              "images": [{"id": img["id"], **placement}]}],
        })

    api("PUT", f"/shops/{_shop_id}/products/{product_id}.json", {"print_areas": updated_print_areas})
    return placement


def create_product(title, description, blueprint_id, print_provider_id, variants, print_areas, tags) -> dict:
    """POST a new product draft. Returns the created product dict."""
    return api("POST", f"/shops/{_shop_id}/products.json", {
        "title":             title,
        "description":       description,
        "blueprint_id":      blueprint_id,
        "print_provider_id": print_provider_id,
        "variants":          variants,
        "print_areas":       print_areas,
        "tags":              tags,
    })


# ── Pricing ───────────────────────────────────────────────────────────────────

def reprice(product: dict, multiplier: float) -> dict:
    """
    Set each enabled variant's price to cost × multiplier.
    Returns summary dict: count, cost_min/max, price_min/max (all in cents).
    """
    enabled = [v for v in product["variants"] if v.get("is_enabled")]
    if not enabled:
        raise RuntimeError("No enabled variants — cannot reprice")

    updated = []
    for v in enabled:
        cost = v.get("cost", 0)
        if cost <= 0:
            print(f"  ⚠️  Variant {v['id']} has cost={cost} — skipping")
            continue
        updated.append({"id": v["id"], "price": round(cost * multiplier), "is_enabled": True})

    api("PUT", f"/shops/{_shop_id}/products/{product['id']}.json", {"variants": updated})

    costs  = [v["cost"]  for v in enabled if v.get("cost", 0) > 0]
    prices = [u["price"] for u in updated]
    return {
        "count":     len(updated),
        "cost_min":  min(costs),
        "cost_max":  max(costs),
        "price_min": min(prices),
        "price_max": max(prices),
    }


def usd(cents: int) -> str:
    return f"${cents / 100:.2f}"
