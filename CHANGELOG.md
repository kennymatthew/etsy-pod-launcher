# Changelog

All notable changes to this project are documented here.

Version numbering:
- **MAJOR** (v1→v2) — big restructure, workflow changes that break existing projects
- **MINOR** (v1.0→v1.1) — new feature, new script, new workflow phase
- **PATCH** (v1.1.0→v1.1.1) — bug fix, small doc correction

---

## [v1.11.0] — 2026-06-12

### Changed
- **Trend now uses velocity ÷ M1 at report render time** (`generate-competitor-report.py`). Previously, Trend was read directly from `shop-watchlist.json` where it was calculated as M2÷M1. M2 has a variable scrape window (10–60 days depending on shop pace), making it unreliable as an absolute sales number — the same shop could show "declining" or "growing" depending purely on how many review pages were scraped. New formula: `velocity est_sales_30d ÷ M1` (fixed 30-day window ÷ lifetime average). Thresholds unchanged: ≥1.3x Growing · 0.6–1.3x Stable · ≤0.6x Declining. `trend_signal` in the JSON is kept as-is for backward compatibility and cross-validation.
- Updated Trend column header tooltip to explain the 30d-vs-lifetime frame and contrast with Momentum (this week vs this month).
- Updated Momentum column header tooltip to clarify it measures this week vs last 30 days and contrast with Trend.
- Updated si-legend Trend entry to describe vel÷M1 formula, time frame, and contrast with Momentum.
- **`generate-phase1-report.py`** — added caption note below the shop trend table clarifying that trend shown there is M2-based (directional only) and that the authoritative velocity-based trend is in the competitor report's Shop Intelligence tab.
- **`research-shops.py`** — added comment explaining that `trend_signal` (M2÷M1) is intentionally kept unchanged and that report-time recalculation happens in `generate-competitor-report.py`.

---

## [v1.10.0] — 2026-06-12

### Changed
- **Est/mo headline now uses velocity `est_sales_30d` as primary signal** (reviews in last 30 calendar days ÷ 10% review rate) — fixed window, consistent across all shops regardless of review pace. M2 → M1 remain as fallbacks. M2 is still used for Trend and Confidence cross-validation.
- Shop Intelligence table now sorts by velocity `est_sales_30d` first, falling back to M2/M1 if unavailable.
- Updated all legends, tooltips, subtitles, and "How is this calculated?" footer to reflect new priority order and explain why velocity is more accurate than M2 extrapolation.
- `generate-phase1-report.py` — removed M3 reference; updated shop methodology note to reflect velocity → M2 → M1 priority.

---

## [v1.9.0] — 2026-06-12

### Added
- **Section 7 signal commentary** (`generate-competitor-report.py`) — after each tier table, auto-generates a "What these listings have in common" block comparing Tier 1 / Tier 2 listings against the remaining field on five measurable signals: Comfort Colors blank, personalization, Bestseller badge, in-carts, and reviews in the last 7 days. Only surfaces findings where the gap is ≥ 20 percentage points; falls back to a "no signals exceed threshold" note if none qualify. All findings tagged `[our data]`.
- **`analyze-shop-velocity.py`** — new standalone script that parses raw-shops review pages to compute per-shop review velocity; outputs a momentum table to console and `shop-velocity.json` for downstream use. Supports `--review-rate` and `--scrape-date` overrides.

### Changed
- **`research-shops.py`** — removed Method 3 (listing-rollup from `competitors.json`); field kept in schema as `null` for backwards compatibility. Added relative shop-age fallback parser: "3 years on Etsy" → subtract from current month (precision: `relative`). `estimate_shop()` signature simplified (no `listing_rollup` arg).

### Fixed
- `research-shops.py` — shop-opened parser now handles Etsy's "X years on Etsy" format in addition to absolute "Member since" / "On Etsy since" patterns, preventing `None` shop-age on shops that display relative age.

---

## [v1.8.0] — 2026-06-11

### Added
- **Section 7 fast-mover flag** — Confidence column now appends ⚡ when a shop is ≤ 1 year old with ≥ 20 reviews, signalling high review velocity relative to shop age; legend explained inline in section intro

### Fixed
- `extract-competitors.py` — shop age regex now catches "X months on Etsy" and converts to fractional years (e.g. 11 months → 0.92); previously these showed `?` in the report
- `generate-competitor-report.py` — pipe characters (`|`) in listing titles now replaced with `–` so markdown table cells don't break

---

## [v1.7.0] — 2026-06-11

### Changed
- **Section 7 — Listings to Watch**: replaced arbitrary top-5 FPR cap with a two-tier threshold filter
  - Tier 1: FPR > 5.0 AND reviews ≥ 20 (statistically reliable)
  - Tier 2: FPR > 10.0 AND reviews < 20 (directional only, higher bar to compensate for noise)
- Dog-mom result: 17 Tier 1 + 14 Tier 2 listings (was 5 total previously)
- Dynamic data quality warning: auto-counts how many Tier 2 listings have < 5 reviews and flags them

---

## [v1.6.0] — 2026-06-11

### Added
- **Section 7 — Listings to Watch** fully auto-generated by `generate-competitor-report.py` on every run — no AI fill-in slots
  - Deterministic FPR confidence tiers: ✅ High (reviews ≥ 20), ⚠️ Medium (5–19), ❌ Low (< 5)
  - Columns: Rank, ID (thumbnail chip), Title, FPR, Reviews, Favorites, Bestseller, In-Carts, Shop Sales, Shop Yrs, Confidence
  - Auto-commentary: accessible shop count, bestseller count across both tiers

---

## [v1.5.0] — 2026-06-11

### Added
- **Section 6 — Demand Signals Summary** fully auto-generated by `generate-competitor-report.py` on every run — zero AI fill-in slots
  - Verdict sentence: entrenchment-aware, cites bestseller count + top review count
  - Bestseller badge holder entrenchment table (entrenched / mid / accessible) with percentages
  - Cleaned Etsy Demand Labels table: Rare Find and In High Demand removed (no official Etsy docs); "N bought in 24h" flagged as snapshot only
  - In-Carts Heat table (20+ / 11–19 / 1–10 / null buckets)
  - Demand by Pattern Segment table with Entry Score column (bestseller_pct ÷ listing_count)
  - Auto pattern commentary: best and worst entry pattern named with scores
- `extract-competitors.py` — added `shop_years_on_etsy` field parsed from "X years on Etsy" in raw scrape markdown
- `_entrenchment_tier()` — classifies shops as entrenched (100k+ sales or 5+ years) / mid (20k–100k or 2–5 years) / accessible (under 20k and under 2 years)
- `_fpr_confidence()` — deterministic FPR confidence tier based on review count

### Changed
- `write-market-insights-prompt.md` — Section 6 documented as fully auto-generated; no [FILL IN] slots remain

---

## [v1.4.0] — 2026-06-11

### Added
- **Color Strategy section** now groups Comfort Colors palette into Light and Dark sub-tables
  - `_luminance()` + `_classify_color()` functions using hex values from `CC_HEX` dict
  - Light colors = recommended for dark ink designs; Dark colors = recommended for light/white ink designs
- `generate-niche-verdict.py` — updated `compute_color_strategy()` to output two sub-tables with light/dark classification
- `generate-niche-verdict.py` — updated `compute_fpr_stats()` to carry full entry context (reviews, favorites, bestseller, in_carts, shop_sales, shop_years_on_etsy, confidence tier) and output two-tier tables

### Changed
- EMS/RPM fields fully removed from all scripts and prompts (listing creation date not available via scraping)

---

## [v1.3.0] — 2026-06-04

### Added
- `shared/printify_core.py` — reusable Printify API library imported by all niche creation scripts; functions: `load_env`, `configure`, `api`, `upload_image`, `get_variant_groups`, `build_variants`, `build_initial_print_areas`, `rebuild_print_areas_dark_light`, `get_product_placement`, `sync_placement_across_print_areas`, `create_product`, `reprice`, `usd`
- `scripts/calculate_placement.py` — calculates x/y/scale from design image dimensions + print area pixel dimensions; supports calibration from known-good values, comparison tables across multiple designs, and JSON output
- `projects/[niche]/scripts/create-[niche]-listings.py` pattern — per-niche creation script that imports `printify_core`; `--listing N` creates one design at a time; `--finalize <product_id>` syncs verified placement to all print_areas
- `04-listing/listing-strategy.html` — 6-tab decision doc consolidating all listing copy (Strategy, Titles, Tags, Price, Colors, Personalization); generated in Phase 4 before the creation script runs
- `04-listing/listing-preview.html` — 3-tab final approval checkpoint (one tab per design showing exact Etsy listing view + one Printify Setup tab); must be approved before running the creation script

### Changed
- **Workflow phase order** — Phase 4 is now "Listing" (write copy → listing-strategy.html → listing-preview.html approval); Phase 5 is now "Printify" (script-driven product creation); listing copy must be finalized before the creation script runs since title/description are baked in
- `WORKFLOW.md` Phase 5 — completely rewritten as script-driven flow: `--listing N` to create each design, verify placement in editor, `--finalize <product_id>` to sync; replaces manual UI approach
- `WORKFLOW.md` Phase 2.3 — updated design file naming to `design[N]-black.png` / `design[N]-white.png` (was `design-name-black.png` / `design-name-offwhite.png`)
- `README.md` — updated Phase 4/5 flowchart and phase list to reflect new order; fixed "Cost × 2.5" → "Cost × 5 list / 50% sale" in What AI Does table; added new files to folder structure

### Technical notes
- Per-color print_area structure: 1 default print_area (all non-light colors, white-ink design) + 1 per light color (black-ink design) — mirrors Printify's "Make a specific design for [color]" UI feature; required for the editor and auto-generated Etsy mockups to show correct ink color per shirt color
- `sync_placement_across_print_areas()` uses `collections.Counter` to identify the outlier placement (the print_area the user edited in the visual editor) and pushes it to all print_areas — you only need to adjust placement once

---

## [v1.2.0] — 2026-06-03

### Added
- `generate-competitor-report.py` now produces a **two-tab HTML report**: Tab 1 = Market Insights (rendered from market-insights.md), Tab 2 = Competitor Report (existing card grid)
- **Top performers strip** at the top of Tab 1 — top 8 listings by reviews across all product types, horizontally scrollable with real product images, titles, review counts, and prices; each card links to Etsy
- **Inline listing ID chips** — every 10-13 digit listing ID in market-insights.md auto-renders as a small image chip (product thumbnail + review count); hover shows title + price; click opens Etsy listing; works in paragraphs, bullet lists, and tables
- **Source label dot mode** — `[our data]` / `[inferred]` / `[market knowledge]` tags default to compact colored dots (● green / ● blue / ● gray) with hover tooltips; "Show labels" toggle in the legend expands all dots to full pill form throughout the document
- **Source label legend** — compact one-liner below the page title explaining the three dot/pill types with a toggle button (Show labels / Hide labels)
- **Source labeling convention** — every claim in market-insights.md must be tagged `[our data]`, `[inferred]`, or `[market knowledge]`; gap/opportunity tables must include a Confidence column

### Changed
- `generate-competitor-report.py` — backward compatible: if market-insights.md is absent, Tab 1 shows a placeholder; Tab 2 (Competitor Report) is unaffected
- `WORKFLOW.md` Phase 1.2 — updated to describe the two-tab report and clarify that Tab 1 is a placeholder until Phase 1.3
- `WORKFLOW.md` Phase 1.3 — added instruction to regenerate the HTML after writing market-insights.md, with full description of Tab 1 features

---

## [v1.1.0] — 2026-06-03

### Added
- `scripts/extract-competitors-prompt.md` — schema + field-by-field rules for building competitors.json from Etsy listing scrapes; covers demand signals, image URLs, rating gotcha (star widget vs numeric average), color completeness, and print method inference
- `scripts/generate-competitor-report.py` — generates a self-contained HTML competitor report from any niche's competitors.json; includes 8 category filters, demand badges (🔥 In 20+ carts), product images, sort by price/reviews/rating, and coral theme; reusable across all future projects
- `competitors.json` schema — two new fields: `demand_signals` (array, e.g. `["In 20+ carts"]`) and `image_url` (highest-res Etsy image)

### Changed
- `scripts/research-competitors.py` — upgraded from top-5 scrape to full Etsy best-seller results page (~30–48 listings); now uses correct Etsy URL format (`is_best_seller=true`, US locale `locationQuery=6252001`)
- `WORKFLOW.md` Phase 1.2 — updated to document the full scrape → extract → HTML report flow; fixed output path (`.firecrawl/` → `01-research/scrapes/`)
- `README.md` — corrected phase count (7 → 9), fixed pricing formula (`cost×2.5` → `cost×5 list / permanent 50% off`), added new scripts to folder reference, fixed Quick Start design path

---

## [v1.0.0] — 2026-05-31

### Added
- Initial release — 9-phase POD workflow (Research → Design → Mockups → Printify → Listing → Sample → Go Live → Diagnostics → Scale)
- `scripts/research-competitors.py` — scrapes Etsy competitor listings via Firecrawl
- Printify API automation: product creation, placement copy, variant reduction to ≤100
- Playwright + eRank integration for keyword search volume extraction
- AI-assisted listing copy (title, tags, description) based on real keyword data
- Project folder structure: `/projects/<niche>/01-research` through `06-performance`
- `shared/` — placement values, SEO rules, and knowledge base carried across projects
