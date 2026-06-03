# Changelog

All notable changes to this project are documented here.

Version numbering:
- **MAJOR** (v1→v2) — big restructure, workflow changes that break existing projects
- **MINOR** (v1.0→v1.1) — new feature, new script, new workflow phase
- **PATCH** (v1.1.0→v1.1.1) — bug fix, small doc correction

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
