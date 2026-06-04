#!/usr/bin/env python3
"""
Calculate Printify placement values (x, y, scale) for any design image.

Fetches the exact print area dimensions from the Printify API per blank type,
then computes placement so the design sits at a specified physical size and
vertical position on the shirt — no visual trial and error needed.

Usage:
    # Basic — calculate for one image
    python scripts/calculate_placement.py path/to/design.png

    # Calculate for multiple images at once (shows a comparison table)
    python scripts/calculate_placement.py design1-black.png design1-white.png design2-black.png design2-white.png

    # Adjust desired print width or top margin
    python scripts/calculate_placement.py design.png --width 10 --top 2.5

    # Calibrate from a known-good Printify placement (avoids guessing top margin)
    python scripts/calculate_placement.py design.png --calibrate-y 0.5477 --calibrate-scale 0.8777 --calibrate-image save-the-date.png

    # Save results to a JSON file for use by product-creation scripts
    python scripts/calculate_placement.py design1-black.png design2-black.png --save projects/my-niche/placement.json

    # Skip the API call (use known dimensions)
    python scripts/calculate_placement.py design.png --pa-width 4500 --pa-height 5100

Environment:
    PRINTIFY_API_TOKEN — required unless --pa-width/--pa-height are provided
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Auto-load .env from project root (two levels up from this script)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists() and not os.getenv("PRINTIFY_API_TOKEN"):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

# ── Constants ──────────────────────────────────────────────────────────────────

API_BASE        = "https://api.printify.com/v1"
API_TOKEN       = os.getenv("PRINTIFY_API_TOKEN")

# Gildan 5000 / Monster Digital (verified from API 2026-06-04)
DEFAULT_BLUEPRINT_ID = 6    # Unisex Heavy Cotton Tee (Gildan 5000)
DEFAULT_PROVIDER_ID  = 29   # Monster Digital

# Reference size to use for the calculation. L/XL/2XL/3XL all share the same
# print area dimensions — we use L as the reference. S and M are smaller but
# have the same 1.133 aspect ratio, so proportional placement looks identical.
REFERENCE_SIZE  = "L"
PRINT_DPI       = 300

# Sensible defaults for a standard chest print on a Gildan 5000
DEFAULT_PRINT_WIDTH_IN = 10.0   # desired design width on shirt, in inches
DEFAULT_TOP_MARGIN_IN  = 2.5    # inches from top of print area to TOP edge of design


# ── API helpers ────────────────────────────────────────────────────────────────

def fetch_print_area(blueprint_id: int, provider_id: int) -> tuple[int, int]:
    """Return (width_px, height_px) for the front print area of the reference size."""
    if not API_TOKEN:
        raise EnvironmentError(
            "PRINTIFY_API_TOKEN not set. "
            "Either export it or pass --pa-width and --pa-height manually."
        )

    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    url = f"{API_BASE}/catalog/blueprints/{blueprint_id}/print_providers/{provider_id}/variants.json"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    variants = data.get("variants", [])
    for variant in variants:
        size = variant.get("options", {}).get("size", "")
        if size == REFERENCE_SIZE:
            for ph in variant.get("placeholders", []):
                if ph["position"] == "front":
                    return ph["width"], ph["height"]

    # Fallback: use any variant's front placeholder
    for variant in variants:
        for ph in variant.get("placeholders", []):
            if ph["position"] == "front":
                print(
                    f"  Warning: size '{REFERENCE_SIZE}' not found, "
                    f"using '{variant['options'].get('size')}' as reference.",
                    file=sys.stderr
                )
                return ph["width"], ph["height"]

    raise ValueError("No front print area found in API response.")


# ── Core calculation ────────────────────────────────────────────────────────────

def calculate(
    image_path: Path,
    pa_width_px: int,
    pa_height_px: int,
    print_width_in: float,
    top_margin_in: float,
) -> dict:
    """
    Calculate x, y, scale for a design image.

    All values are fractions of the print area (0.0–1.0).

    Print area is treated as a 300-DPI canvas:
        pa_width_in  = pa_width_px  / 300
        pa_height_in = pa_height_px / 300

    Placement intent:
        - Design is centred horizontally                → x = 0.5
        - Design is scaled to fill print_width_in       → scale = print_width_in / pa_width_in
        - Top edge of design is at top_margin_in from
          the top of the print area                     → y = (top_margin + design_height/2) / pa_height_in
    """
    img       = Image.open(image_path)
    img_w, img_h = img.size
    aspect    = img_h / img_w          # height-to-width ratio

    pa_width_in  = pa_width_px  / PRINT_DPI
    pa_height_in = pa_height_px / PRINT_DPI

    scale         = print_width_in / pa_width_in
    design_h_in   = print_width_in * aspect        # design height on the shirt at this scale
    center_y_in   = top_margin_in + design_h_in / 2
    y             = center_y_in / pa_height_in
    x             = 0.5

    # Bounds checking
    top_edge_frac    = top_margin_in / pa_height_in
    bottom_edge_frac = (top_margin_in + design_h_in) / pa_height_in

    warnings = []
    if scale > 1.0:
        warnings.append(f"scale {scale:.3f} > 1.0 — design wider than print area, will be clipped")
    if bottom_edge_frac > 1.0:
        overshoot = (bottom_edge_frac - 1.0) * pa_height_in
        warnings.append(f"design extends {overshoot:.2f}\" past the bottom of the print area")
    if y > 1.0:
        warnings.append("y > 1.0 — design centre is outside the print area")

    return {
        "image":             str(image_path),
        "image_px":          f"{img_w} × {img_h}",
        "image_aspect":      round(aspect, 4),
        "pa_px":             f"{pa_width_px} × {pa_height_px}",
        "pa_width_in":       round(pa_width_in, 2),
        "pa_height_in":      round(pa_height_in, 2),
        "print_width_in":    print_width_in,
        "design_height_in":  round(design_h_in, 3),
        "top_margin_in":     top_margin_in,
        "top_edge_frac":     round(top_edge_frac, 4),
        "bottom_edge_frac":  round(bottom_edge_frac, 4),
        "x":                 round(x, 10),
        "y":                 round(y, 10),
        "scale":             round(scale, 10),
        "angle":             0,
        "warnings":          warnings,
    }


# ── Calibration mode ───────────────────────────────────────────────────────────

def calibrate_top_margin(
    known_image_path: Path,
    known_y: float,
    known_scale: float,
    pa_width_px: int,
    pa_height_px: int,
) -> tuple[float, float]:
    """
    Given a confirmed working y + scale from Printify UI, reverse-engineer
    the effective top_margin and print_width_in that produced those values.

    Returns (top_margin_in, print_width_in).
    """
    img     = Image.open(known_image_path)
    img_w, img_h = img.size
    aspect  = img_h / img_w

    pa_width_in  = pa_width_px  / PRINT_DPI
    pa_height_in = pa_height_px / PRINT_DPI

    print_width_in  = known_scale * pa_width_in
    design_h_in     = print_width_in * aspect
    center_y_in     = known_y * pa_height_in
    top_margin_in   = center_y_in - design_h_in / 2

    return round(top_margin_in, 4), round(print_width_in, 4)


# ── Output helpers ─────────────────────────────────────────────────────────────

def print_result(r: dict, index: int = None) -> None:
    label = f"Image {index}: " if index is not None else ""
    name  = Path(r["image"]).name

    print()
    print(f"  {'─' * 54}")
    print(f"  {label}{name}")
    print(f"  {'─' * 54}")
    print(f"  Image size:    {r['image_px']} px  (aspect H/W = {r['image_aspect']})")
    print(f"  Print area:    {r['pa_width_in']}\" × {r['pa_height_in']}\"  ({r['pa_px']} px at {PRINT_DPI} DPI)")
    print()
    print(f"  Desired width on shirt:  {r['print_width_in']}\"")
    print(f"  Resulting print size:    {r['print_width_in']}\" wide × {r['design_height_in']}\" tall")
    print(f"  Top edge position:       {r['top_margin_in']}\" from top of print area")
    print(f"  Bottom edge position:    {round(r['bottom_edge_frac'] * r['pa_height_in'], 2)}\" from top of print area")
    print()
    print(f"  ── Placement values ──────────────────────────────")
    print(f"  x     = {r['x']}")
    print(f"  y     = {r['y']}")
    print(f"  scale = {r['scale']}")
    print(f"  angle = {r['angle']}")
    print(f"  ─────────────────────────────────────────────────")

    if r["warnings"]:
        for w in r["warnings"]:
            print(f"  ⚠  WARNING: {w}")
    else:
        print(f"  ✓  Design fits within print area")


def print_comparison_table(results: list[dict]) -> None:
    print()
    print(f"  {'Image':<30} {'Size px':>20}  {'scale':>8}  {'y':>8}  {'Print size':>18}  {'Fits?':>6}")
    print(f"  {'─'*30} {'─'*20}  {'─'*8}  {'─'*8}  {'─'*18}  {'─'*6}")
    for r in results:
        name   = Path(r["image"]).name[:30]
        size   = r["image_px"]
        scale  = f"{r['scale']:.6f}"
        y      = f"{r['y']:.6f}"
        psize  = f"{r['print_width_in']}\" × {r['design_height_in']}\""
        fits   = "✓" if not r["warnings"] else "⚠"
        print(f"  {name:<30} {size:>20}  {scale:>8}  {y:>8}  {psize:>18}  {fits:>6}")
    print()


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Calculate Printify placement (x, y, scale) for design images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("images", nargs="+", help="Path(s) to design PNG files")
    parser.add_argument("--width", type=float, default=DEFAULT_PRINT_WIDTH_IN,
                        metavar="INCHES",
                        help=f"Desired print width on shirt in inches (default: {DEFAULT_PRINT_WIDTH_IN}\")")
    parser.add_argument("--top", type=float, default=DEFAULT_TOP_MARGIN_IN,
                        metavar="INCHES",
                        help=f"Distance from top of print area to TOP edge of design in inches (default: {DEFAULT_TOP_MARGIN_IN}\")")
    parser.add_argument("--blueprint", type=int, default=DEFAULT_BLUEPRINT_ID,
                        help=f"Printify blueprint ID (default: {DEFAULT_BLUEPRINT_ID} = Gildan 5000)")
    parser.add_argument("--provider", type=int, default=DEFAULT_PROVIDER_ID,
                        help=f"Printify print provider ID (default: {DEFAULT_PROVIDER_ID} = Monster Digital)")
    parser.add_argument("--pa-width", type=int, default=None,
                        help="Override: print area width in px (skips API call)")
    parser.add_argument("--pa-height", type=int, default=None,
                        help="Override: print area height in px (skips API call)")
    parser.add_argument("--calibrate-y", type=float, default=None,
                        metavar="Y",
                        help="Known-good y value from Printify UI — used with --calibrate-image to reverse-engineer top margin")
    parser.add_argument("--calibrate-scale", type=float, default=None,
                        metavar="SCALE",
                        help="Known-good scale value from Printify UI")
    parser.add_argument("--calibrate-image", type=str, default=None,
                        metavar="PATH",
                        help="Image that --calibrate-y/--calibrate-scale was measured from")
    parser.add_argument("--save", type=str, default=None,
                        metavar="PATH",
                        help="Save results to this JSON file")
    args = parser.parse_args()

    # ── Get print area dimensions ──
    if args.pa_width and args.pa_height:
        pa_w, pa_h = args.pa_width, args.pa_height
        source = "manual override"
    else:
        print(f"Fetching print area from Printify API "
              f"(blueprint {args.blueprint}, provider {args.provider}, size {REFERENCE_SIZE})...")
        try:
            pa_w, pa_h = fetch_print_area(args.blueprint, args.provider)
            source = "Printify API"
        except Exception as e:
            print(f"  Error fetching from API: {e}", file=sys.stderr)
            print("  Falling back to known Gildan 5000 / Monster Digital dimensions (L size).")
            pa_w, pa_h = 4500, 5100
            source = "hardcoded fallback (Gildan 5000 / Monster Digital, L)"

    print(f"  Print area: {pa_w} × {pa_h} px = {pa_w/300:.2f}\" × {pa_h/300:.2f}\" at 300 DPI  [{source}]")

    # ── Calibration mode ──
    top_margin = args.top
    print_width = args.width
    if args.calibrate_y and args.calibrate_scale and args.calibrate_image:
        cal_path = Path(args.calibrate_image)
        if not cal_path.exists():
            print(f"Error: calibration image not found: {cal_path}", file=sys.stderr)
            sys.exit(1)
        cal_top, cal_width = calibrate_top_margin(cal_path, args.calibrate_y, args.calibrate_scale, pa_w, pa_h)
        print(f"\n  Calibration from '{cal_path.name}' (y={args.calibrate_y}, scale={args.calibrate_scale}):")
        print(f"    → Effective print width:  {cal_width:.3f}\"")
        print(f"    → Effective top margin:   {cal_top:.3f}\" from top of print area")
        print(f"  Using these calibrated values for all images.")
        top_margin  = cal_top
        print_width = cal_width

    # ── Calculate for each image ──
    results = []
    for img_path_str in args.images:
        img_path = Path(img_path_str)
        if not img_path.exists():
            print(f"  Warning: image not found, skipping: {img_path}", file=sys.stderr)
            continue
        r = calculate(img_path, pa_w, pa_h, print_width, top_margin)
        results.append(r)

    if not results:
        print("No valid images found.", file=sys.stderr)
        sys.exit(1)

    # ── Print output ──
    if len(results) == 1:
        print_result(results[0])
    else:
        print()
        print("  Comparison table:")
        print_comparison_table(results)
        print("  Detailed values:")
        for i, r in enumerate(results, 1):
            print_result(r, index=i)

    # ── Summary of API payload values ──
    print()
    print("  ── How to read these values ──────────────────────")
    print("  x     = horizontal centre (0.5 = centred always)")
    print("  y     = vertical centre as fraction of print area height")
    print("          (e.g. y=0.35 → design centre is 35% down from top)")
    print("  scale = design width as fraction of print area width")
    print("          (e.g. scale=0.67 → design is 67% as wide as the print area)")
    print()
    print("  These values are the same regardless of shirt size because")
    print("  all sizes share the same 1.133 H/W aspect ratio —")
    print("  the print area simply scales proportionally with the shirt.")
    print()
    print("  ⚠  Always verify visually on ONE product in Printify UI")
    print("     before pushing placement to all 96 variants.")
    print()

    # ── Save to JSON ──
    if args.save:
        save_path = Path(args.save)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing file if present
        existing = {}
        if save_path.exists():
            with open(save_path) as f:
                try:
                    existing = json.load(f)
                except json.JSONDecodeError:
                    pass

        existing.setdefault("blueprint_id", args.blueprint)
        existing.setdefault("provider_id", args.provider)
        existing.setdefault("print_area_px", {"width": pa_w, "height": pa_h})
        existing.setdefault("images", {})

        for r in results:
            key = Path(r["image"]).name
            existing["images"][key] = {
                "x":     r["x"],
                "y":     r["y"],
                "scale": r["scale"],
                "angle": r["angle"],
                "image_px":          r["image_px"],
                "print_width_in":    r["print_width_in"],
                "design_height_in":  r["design_height_in"],
                "top_margin_in":     r["top_margin_in"],
                "warnings":          r["warnings"],
            }

        with open(save_path, "w") as f:
            json.dump(existing, f, indent=2)

        print(f"  Saved to: {save_path}")


if __name__ == "__main__":
    main()
