# Print Provider & Blank Selection Guide

Use this at Phase 2.0 — before any design or mockup work begins.
The blank determines the mockup template, color palette, and pricing floor.
Changing it after mockups means redoing everything.

---

## Step 1 — Identify the starting blank candidate

Check `competitors.json` → look at the `blank` field across the top 3 listings sorted by `estimated_monthly_sales`.

- If the majority share one blank → start there.
- If mixed → default to **Gildan 5000** (widest color range, lowest cost, most common in POD apparel).

---

## Step 2 — Blank selection criteria

| Criterion | Guidance |
|---|---|
| Price tier | Gildan 5000 = budget ($8–10 cost). Bella+Canvas 3001 = mid ($12–15). Comfort Colors 1717 = premium ($16–20). Match to your niche's price ceiling from Phase 1. |
| Color range | More colors = more variant potential but approaches the 100-variant cap faster. Check how many colors Printify lists for the blank. |
| Unisex vs fitted | Default to unisex. Only choose fitted if competitor research explicitly shows it. |
| Competitor signal | If 2 of the top 3 competitors use the same blank, that blank is validated for this niche. |

**100-variant cap:** Printify enforces a hard cap of 100 variants per product (colors × sizes). If your blank has 30 colors × 6 sizes = 180 — you must cull colors. Plan this before setup. See `printify-listing-conventions.md`.

---

## Step 3 — Fetch real costs via API (never estimate)

Run:
```bash
python3 scripts/fetch-pp-costs.py --blueprint <blueprint_id>
```

This prints a comparison table of all print providers for the blueprint, sorted by average cost across S–2XL.

To find the blueprint ID: browse Printify's catalog in the dashboard or use:
```bash
python3 scripts/fetch-pp-costs.py --list-blueprints
```

---

## Step 4 — Print provider selection criteria

| Criterion | Guidance |
|---|---|
| Location | Prefer US-based PP if your target buyers are in the US. US PP = faster shipping = better review scores. |
| Quality score | Printify shows a 0–5 quality rating per PP. Prefer 4.5+. |
| Production time | Under 3 business days preferred. Check estimated production days shown in Printify catalog. |
| Cost | Read from the `fetch-pp-costs.py` output. Never estimate from the dashboard manually — costs vary by color and size. |

**Monster Digital** (PP ID: 29 for most blueprints) — US-based, confirmed working for Gildan 5000, quality score 4.8. Use as default unless cost comparison shows a clearly better option (>$1.50/unit cheaper at comparable quality).

---

## Step 5 — Margin check

Target: **60% margin** = list price must be at least **cost × 2.5**

| Blank | Avg cost | Min list price (×2.5) | Typical market price | Viable? |
|---|---|---|---|---|
| Gildan 5000 | ~$8.75 | $21.90 | $22–28 | ✅ Yes |
| Bella+Canvas 3001 | ~$13.50 | $33.75 | $28–35 | ⚠ Tight — check niche ceiling |
| Comfort Colors 1717 | ~$17.50 | $43.75 | $35–45 | ⚠ Premium niche only |

If the 60% margin target fails at the market price ceiling → try a lower-cost PP for the same blank before switching blanks.

---

## Step 6 — Lock the selection

Record at the top of `02-design/brief.md` before writing anything else:

```
Blank: [name]  |  Printify Blueprint ID: [id]  |  Print Provider: [name] (ID: [id])
Cost range (S–2XL): $[min]–$[max]  |  Avg cost: $[avg]
List price: $[price]  |  Target margin: [X]%  |  Margin at list price: [Y]%
```

Do NOT proceed to design brief text or mockups until this block is complete.
