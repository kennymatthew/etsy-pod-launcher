# Supplier / Print Provider Notes (reusable across all projects)
**Last updated:** 2026-05-31

---

## Print Provider Selection Criteria
1. DTG quality — check review photos on Printify marketplace
2. Production time — target 2–3 business days
3. Ships from USA — reduces delivery time for US buyers (majority of Etsy)
4. Blank availability — Comfort Colors 1717 is preferred if available
5. Wide size range — XS to 4XL minimum

## Blanks to Check on Printify
| Blank | Notes |
|---|---|
| Comfort Colors 1717 | Premium DTG blank — top sellers use it, buyers search for it |
| Bella+Canvas 3001 | Standard quality, reliable, widely available |
| Gildan 64000 | Budget option — avoid for premium-priced listings |
| Next Level 3600 | Soft, good fit — alternative to Comfort Colors |

## Known-Good Print Placements (front, per blank)

| Blank | x | y | scale | Notes |
|---|---|---|---|---|
| Gildan 5000 | 0.5 | 0.547735567085003 | 0.8777092933600811 | Verified 2026-05-31 — default scale=1 clips edges |

**Workflow for new batches:**
1. Create first product and set placement manually in Printify editor until preview looks correct
2. Read that product's placement via API: `GET /v1/shops/{shop_id}/products/{id}.json` → `print_areas[].placeholders[].images[]`
3. Copy exact x/y/scale to all other products in the batch via PUT

## Notes
- TBD: confirm which providers offer Comfort Colors blank and turnaround time
- Always order a sample before launching — check print quality and sizing yourself
- Note the print area dimensions per provider — affects design sizing
