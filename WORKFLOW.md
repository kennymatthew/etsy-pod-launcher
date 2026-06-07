# Step-by-Step Workflow — Etsy POD with AI

Detailed instructions for each phase. Read README.md first for the overview.

---

## Sub-agent Strategy (context management)

Sub-agents run as separate processes with their own context window. Use them when input is large but output is small — they do the heavy reading without filling up the main conversation.

| Task | How to run | Signal |
|---|---|---|
| Scrape competitors + build competitors.json | **Sub-agent** | Reads 50+ large markdown files |
| eRank keyword extraction via Playwright | **Sub-agent** | Large DOM snapshots |
| Analysing all listing files before recommending | **Sub-agent** | Reading many files at once |
| Single Printify API GET or PUT | Inline | Small payload, fast |
| Updating one markdown file | Inline | Data already in context |
| Variant filtering + API updates | Inline | Single script, small result |

**Rule of thumb:** If the task will read more than ~500 lines of content, use a sub-agent.

How to trigger: tell Claude *"use a sub-agent to..."* or *"spawn an Explore/general-purpose agent to..."*

---

## Phase 0 · Niche Discovery

**Goal:** Confirm a niche has real buyer demand and a viable entry window before running Phase 1.
Run Phase 0 for every new niche — it takes 15 minutes and prevents wasting Phase 1 resources on a dead or oversaturated niche.

### 0.1 Etsy Autocomplete — buyer language check (free, 5 min)

Run the autocomplete script:
```bash
python3 scripts/research-autocomplete.py --niche your-niche-name --query "your broad keyword"
```

This opens a fresh US browser session (New York locale, not logged in), types each variant into Etsy's search box, and captures all autocomplete suggestions. Saves to `projects/[niche]/01-research/autocomplete-[query].json`.

Phrases marked ★ in the terminal output appeared across multiple letter variants — those are the highest buyer-intent terms. Use them as your Phase 1 `--query` argument and your Phase 4 keyword starting point.

**Why US context:** Logged-in sessions skew autocomplete toward your history. US context ensures results reflect the US buyer market regardless of where you're physically located.

**Manual fallback (if script fails):** Open etsy.com in an incognito window, not logged in. Type the broad word, record every suggestion. Repeat with the word + each of these letters: a, b, c, f, g, h, s, t.

### 0.2 Cross-niche substitution (free, 2 min)

If you already have a proven design format, list 10 other identity words that slot into it. Prefer less-saturated identities (ICU tech, arborist, disc golf) over dominant ones (nurse, teacher). Run each strong candidate through Step 0.1 to confirm buyer phrases exist.

### 0.3 eRank Keyword Ideas — volume check (1 daily credit, 5 min)

Only spend an eRank credit once Step 0.1 has already produced a strong candidate phrase.

1. In eRank Keyword Tool, enter the top phrase from your autocomplete results.
2. Scroll to "Keyword Ideas". Sort by competition low → high.
3. Look for green competition + meaningful volume — these are sub-niche entry points.
4. Note the top 3 phrases — they become the Phase 1.4 starting point.

### 0.4 Timing check — seasonal niches

Before committing to a seasonal niche, confirm today is at least **35 days before the event**.
Reference `shared/seasonal-calendar.md` for "start by" dates.

- Within window → proceed
- Outside window → choose an evergreen niche instead, or start immediately and accept lower ranking on first launch

### 0.5 Optional — Alura top-sellers check (2 min, uses Firecrawl credits)

```bash
python3 scripts/research-top-sellers.py --niche your-niche-name
```

Scrapes Alura's public best-selling Clothing page (no login required). Pass the saved markdown to Claude:
> "Read `top-sellers-clothing-raw.md`, extract each listing row as JSON (rank, title, etsy_url, total_sales, monthly_sales, revenue_estimate). Save to `top-sellers-clothing.json`."

Then search it:
> "Search top-sellers-clothing.json for [your keyword]. Report how many listings match and their monthly_sales."

- 3+ matches with monthly_sales above 100 → demand confirmed at top-seller level
- 0 matches → niche may be new or underserved — proceed to Phase 1 but treat as uncertain

**Stability note:** If the scrape returns no sales figures, Alura's page may have changed — fall back to the in-house estimate from `competitors.json` (`estimated_monthly_sales` field).

### Phase 0 output

One confirmed niche keyword that appeared in Etsy autocomplete AND passed an eRank volume check. Only after Phase 0 is complete does Phase 1 begin.

---

## Phase 1 · Research

**Goal:** Know exactly what's selling before you design anything.

### 1.1 Create project folder structure

```bash
python3 scripts/create-project.py --niche your-niche-name
```

Creates `/projects/[niche]/01-research/` through `05-performance/` plus stub files for `keywords.md` and `brief.md`. Prints next-step commands.

### 1.2 Scrape competitor listings

Run the research script:
```bash
python3 scripts/research-competitors.py --niche your-niche-name --query "your etsy search term"
```

This uses Firecrawl to:
1. Search Etsy for best-seller listings matching your query
2. Scrape each listing page in parallel (3 at a time)
3. Save clean markdown files to `projects/[niche]/01-research/scrapes/`
4. Write a manifest file at `projects/[niche]/01-research/scrapes/manifest.json`

Run the extraction script:
```bash
python3 scripts/extract-competitors.py --niche your-niche-name
```

This reads every scraped page in `scrapes/` and extracts:
- Price range, rating, review count, sales count
- Title keywords
- All colors listed in the dropdown
- Print method (confirmed vs inferred)
- Personalization type
- Design style and key phrases
- Demand signals (e.g. "In 20+ carts", "In high demand")
- First product image URL
- Shop name, Star Seller status, ships from

The script runs a self-check after extraction and warns on: duplicate image URLs, arithmetic inconsistencies, date sanity errors, schema completeness gaps, and cross-listing data leakage. Fix any warnings before proceeding.

**Output:** `01-research/scrapes/etsy-listing-*.md` (raw) + `01-research/competitors.json` (structured)

### 1.3 Research competitor shops

```bash
python3 scripts/research-shops.py --niche your-niche-name
```

Auto-detects the top shops from `competitors.json` and scrapes their shop pages. Builds `shop-watchlist.json` with three independent monthly sales estimates per shop (M1 lifetime average, M2 current momentum, M3 listing rollup). Used for the Niche Verdict and Tab 3 Shop Intelligence.

**Output:** `01-research/shop-watchlist.json`

### 1.4 Get keyword search volumes from eRank

*(Step numbering continues below — eRank is step 1.4 in the original workflow. Steps are reordered here for clarity.)*

See section 1.4 below.

### 1.5 Build patterns-config.json (in conversation with Claude)

After `competitors.json` exists, tell Claude:
> "Read competitors.json for [niche] and propose a patterns-config.json — group the listings into 4–7 visually distinct design patterns based on titles and descriptions."

Claude will read the titles and descriptions, identify recurring themes, and propose a `patterns-config.json` with keyword rules. Review and approve the config before saving it to `projects/[niche]/01-research/patterns-config.json`.

**This is a conversation step, not a script.** The config is created once per niche and reused on every report regeneration.

**Mandatory self-check before finalising (Claude must do this):**

After proposing the initial patterns, Claude must run the classification against `competitors.json` and report:
1. How many listings fall into each pattern (including P0)
2. If P0 > 15% of total listings — STOP. Print all P0 listing titles and investigate for hidden sub-patterns before saving the config. Common hiding spots: personalization style (photo vs name-only), product type outliers (non-shirt products), seasonal/holiday angles, cross-niche designs (e.g. plant+dog, books+dog).
3. Only save `patterns-config.json` after P0 is ≤ 15% OR after explicitly confirming each remaining P0 listing is genuinely uncategorizable and noting why.

**Personalization signal check (run this every time):**

Count titles containing any of: `personalized`, `personalize`, `custom pet`, `photo and name`, `pet photo`, `with names`, `with photo`. If 3 or more listings match → propose a Custom Personalization pattern. Fewer than 3 → skip it, not a meaningful segment in this niche.

**Output:** `01-research/patterns-config.json`

### 1.6 Write market-insights.md

Read and follow the locked prompt exactly:
```
scripts/prompts/write-market-insights-prompt.md
```

The prompt covers required sections, source tagging rules, and a self-check. Do not skip the self-check — it catches missing or unformatted tags before the HTML is generated.

**Do NOT write a "Top Design Patterns" prose section** — it is replaced by the visual from `patterns-config.json`.

**Output:** `01-research/market-insights.md`

### 1.7 Generate the complete report

Once all inputs exist (`competitors.json`, `market-insights.md`, `shop-watchlist.json`, `patterns-config.json`), run once:

```bash
python3 scripts/generate-competitor-report.py --niche your-niche-name
```

This produces `competitor-report.html` — a self-contained three-tab HTML report:

**Tab 1 (Market Insights):**
- Top-performing listings strip (top 8 by EMS, scrollable with images)
- Niche Verdict (from market-insights.md)
- **Design Patterns visual** — Netflix-style horizontal scroll rows, one per pattern (from patterns-config.json + competitors.json), listed in no particular order
- Sections 1–10 from market-insights.md
- Source label dots (● green = our data, ● blue = inferred, ● gray = market knowledge) — click "Show labels" to expand

**Tab 2 (Competitor Report):** Card grid with 8 category filters, demand badges, product images, sort by price/reviews/rating/EMS.

**Tab 3 (Shop Intelligence):** M1/M2/M3 monthly sales estimates per shop, trend signal, confidence.

**Output:** `01-research/competitor-report.html` (all three tabs fully populated)

**Source labeling rule (applies to every market-insights.md):**
Every sentence that makes a claim must be tagged with a backtick-wrapped source label. Tags without backticks render as plain text — the color dots will not appear.

| Write it as | Meaning |
|---|---|
| `` `[our data]` `` | Directly observed in competitors.json, keywords.md, or other scraped files |
| `` `[inferred]` `` | Logical conclusion drawn from our data — not directly observed |
| `` `[market knowledge]` `` | General POD/Etsy knowledge from AI training data — not verified for this niche |

Rules:
- Tag every sentence — not just section endings or paragraph endings
- Never use hybrid tags (`[our data + inferred]`) — split into two separately tagged sentences
- Bullet list items and table Notes cells each need their own tag
- After saving, click "Show labels" in the HTML report and verify colored dots appear throughout — if a section has no dots, a tag is missing or backticks are missing

Gap/opportunity sections must include a confidence column in any summary table:
- ✅ High — backed by `` `[our data]` ``
- ⚠️ Medium — `` `[inferred]` `` or partially backed
- ❌ Low — primarily `` `[market knowledge]` ``, demand unverified

### 1.5 Validate your slogan/phrase (sub-niche check)
Before designing anything, search the **exact phrase** your design will use on Etsy.

Tell the AI:
> "Search Etsy for '[exact slogan]' and check how many shops with 3,000+ reviews are selling this phrase"

If multiple large shops each style the same saying differently → demand is proven AND no single copyright owner → safe to proceed.
If only one dominant shop exists → copyright risk, find a different phrase.
If no shops → untested demand, research more before committing.

**Output:** Note added to `01-research/market-insights.md`

### 1.4 Get keyword search volumes from eRank
1. Go to [erank.com](https://erank.com) and log in (free account = 5 searches/day)
2. Tell the AI: *"I'm logged into eRank, help me research keywords"*
3. AI uses Playwright to extract search volume data from the eRank table
4. Run searches for: your main keyword, variations, and long-tail phrases
5. **While already in eRank, record trend direction for each keyword.** Look for a trend line or graph below the search volume number. Add a `Trend` column to the keyword table in `keywords.md`:

   ```
   Trend: [keyword] → Rising | Stable | Declining | Seasonal (peak: [month]) | Unknown (graph locked on free plan)
   ```

   **If the trend graph is locked on free plan:** check eRank's "Top 10 Trending Keywords" list — if your main keyword appears there, mark it Rising.

   **Apply this adjustment when writing the Niche Verdict:**
   - Main keyword trending **Rising** → upgrade Demand Signal one level (Low → Medium, Medium → High)
   - Main keyword trending **Declining** → downgrade Demand Signal one level (High → Medium, Medium → Low)
   - Main keyword trending **Seasonal** → note the peak month in the Verdict basis line
   - **Unknown** → leave Demand Signal unadjusted, note the gap in Verdict confidence

**Free plan limit:** 5 searches per day — plan which keywords matter most before you start.

**Output:** Data added to `01-research/keywords.md` including a Trend column for each keyword.

### Gotchas
- eRank free tier shows search volume for the main keyword but locks competition data with "xxx" — that's fine, volume is what matters most
- Always check both the exact phrase ("save the date shirt") AND broader terms ("save the date") — the broader term often gets 10× more searches

---

## ⛔ Stop Check — Niche Verdict (Phase 1.3 + 1.4 must be complete first)

**Do not start Phase 2 until the Niche Verdict is written and the Recommendation is "Enter" or "Enter with sub-niche pivot".**

Both inputs must be ready before running this:
- `competitors.json` complete (Phase 1.2 done — provides `estimated_monthly_sales` and `reviews_per_month`)
- `keywords.md` trend column filled in (Phase 1.4 done — provides trend direction for Demand Signal adjustment)

Run the verdict script:
```bash
python3 scripts/generate-niche-verdict.py --niche your-niche-name
```

This reads `competitors.json` and `keywords.md`, computes all the math (EMS rankings, 15/month check, RPM distribution, trend adjustment), and outputs a pre-filled verdict block. The only things left to fill in are the one-sentence reasoning lines marked `[FILL IN]`.

Paste the output at the **top of `market-insights.md`**, fill in the `[FILL IN]` lines, then remove the generator note at the bottom.

**Read the Recommendation field:**

| Recommendation | Action |
|---|---|
| **Enter** | Proceed to Phase 2 |
| **Enter with sub-niche pivot** | Update the niche angle in `02-design/brief.md` before Phase 2. Do not design for the original broad niche. |
| **Do not enter** | Stop. Start a new project folder for a different niche or the recommended sub-niche. Do not proceed to Phase 2. |

---

## Phase 2 · Design

**Goal:** A print-ready design file based on research.

### 2.0 Lock product + print provider (do this before any design work)

**Do not write a brief or touch Canva until this step is complete.** The blank determines the mockup template, color palette, and pricing floor — changing it after mockups means redoing everything.

1. Check `competitors.json` → look at the `blank` field for the top 3 listings by `estimated_monthly_sales`. If the majority share one blank, start there. If mixed, default to Gildan 5000.
2. Run the cost comparison:
   ```bash
   python3 scripts/fetch-pp-costs.py --blueprint <id>
   # Find blueprint IDs:
   python3 scripts/fetch-pp-costs.py --list-blueprints --search "gildan"
   ```
3. Pick the print provider with the lowest avg cost at quality 4.5+, preferring US-based. See `shared/pp-selection-guide.md` for the full decision criteria.
4. Confirm margin: `avg_cost × 2.5 ≤ market price ceiling` from Phase 1. If it fails, try a cheaper PP before switching blanks.
5. Record the selection at the top of `02-design/brief.md`:
   ```
   Blank: [name]  |  Blueprint ID: [id]  |  Print Provider: [name] (ID: [id])
   Avg cost: $[X]  |  List price: $[Y]  |  Margin: [Z]%
   ```

**Output:** Lock block written at top of `02-design/brief.md`.

### 2.1 Write a design brief
Tell the AI:
> "Based on the research, write a design brief for our product"

The brief covers: design concept, colors, garment style, and what makes it different from competitors.

**Output:** `02-design/brief.md`

### 2.2 Create the design
Create your design file (PNG recommended, transparent background).
- Design size: **4500 × 5400 px** for DTG printing (Printify's recommended resolution)
- Keep the design within the **safe print area** — avoid edges

**Design principles checklist** (both courses agree on these):
- [ ] Readable from 10 feet away
- [ ] 1–3 colors maximum
- [ ] Negative space used — shirt fabric is part of the design, not filled with ink
- [ ] No color gradients
- [ ] No large solid-ink blocks
- [ ] One clear message

### 2.3 Export two design versions
Every design needs **two PNG exports** before uploading to Printify:
1. **Black-ink design** (`design1-black.png`) → for light shirts (white, ivory, natural, sand, sport grey, light blue, etc.)
2. **White-ink design** (`design1-white.png`) → for dark shirts (black, navy, dark heather, forest green, maroon, etc.)

Name files sequentially per design concept: `design1-black.png` + `design1-white.png`, `design2-black.png` + `design2-white.png`, etc.

For dark shirts, the DTG printer lays a white under-base before printing — this is why white-ink designs need a fully transparent background (no white fill on the PNG). The creation script assigns the correct file to each color group automatically.

Save both files to `02-design/print-files/`.

### Gotchas
- **Transparent background is required.** Export as PNG with transparent background — NOT white. A white background PNG prints a white rectangle around your design on every colored shirt. To check: open the product in Printify and preview it on a dark shirt color — if you see a white box around the design, re-export with transparency.
- Don't design to the full canvas edge — there is a bleed area that gets cut off in print
- Use **Canva** or **Kittl** to create and export designs — both work; Canva is more widely known, Kittl has Etsy-specific POD templates. Export as PNG, transparent background, 300 DPI.

---

## Phase 3 · Mockups

**Goal:** Listing photos proven to convert — not guessed from personal taste.

Alek: *"The mockup image is just as important as the design you make. If you don't get the mockup right, your product is absolutely never going to sell."*

### 3.1 Research winning mockup styles
1. Check the **Recommended Mockup Style** section in `01-research/market-insights.md` — this is derived from the Phase 1 competitor scrape (`mockup_style` field) and is the primary input for slot 1. Use it as your starting point.
2. If the majority of entries are `unknown` (description text had no signals), fall back to the manual method: open eRank → Listing View, overlay outlier scores, and note what style the high-outlier listings use.
3. You may still browse eRank Listing View to confirm the scraped recommendation — but scraped data takes precedence over visual browsing.

### 3.2 Source the mockup pack
- Search Etsy directly for the mockup style you found (e.g. "comfort colors sage mockup flatlay")
- The top result is usually the exact pack you saw performing well
- Buy it — typically $3–5
- Save the raw mockup files to `03-mockups/`

**Do NOT use Placeit.** It is immediately identifiable as non-handmade and no best-selling Etsy listings use it.

### 3.3 Build listing photos
Composite your design onto the mockup using Canva, Kittl, Figma, or Photoshop.

Target: **5–10 listing photos** using these slots:

| Slot | Content |
|---|---|
| 1 (main) | Best-performing mockup style — the scroll-stopper |
| 2–3 | Additional styles (flat lay, lifestyle, close-up) |
| 4 | Different colorway or angle |
| 5–6 | Extra variants (e.g. different name combos for personalised listings) |
| 7 | **Color chart** — all available colors with names |
| 8 | **Sizing guide** — with measurements |
| 9+ | Video if possible — ~2× conversion rate, only ~28% of sellers use one |

⚠️ Keep slots 7 and 8 consistent across all listings — makes bulk updating easy.

Save finished listing photos to `03-mockups/`.

### Gotchas
- For batch automation: Figma (free) or Photoshop scripts can apply one design to all mockup variants in one pass
- Re-research mockup styles for each new niche — what converts for engagement shirts differs from what converts for nurse humor shirts

---

## Phase 4 · Listing

**Goal:** Finalize all listing copy — title, tags, description, price, and color decisions — before running the creation script.

> **Do Phase 4 before Phase 5.** The Printify creation script bakes in your finalized title and description. Complete listing copy here first, then create the products in Phase 5.

### 4.1–4.3 Title, Tags, and Description

These three outputs are produced together from one locked prompt.

**Prerequisites — must all exist before running:**
- `01-research/competitors.json` (Phase 1.2 complete)
- `01-research/keywords.md` with Trend column filled in (Phase 1.4 complete)
- `01-research/market-insights.md` with Niche Verdict (Stop Check passed)
- `02-design/brief.md` with Lock block filled in (Phase 2.0 complete)

**Run:**
Paste `scripts/prompts/write-listing-copy-prompt.md` to Claude with:
> "Follow this prompt exactly. Niche: [niche-name]."

The prompt instructs Claude to read all four prerequisite files, then produce three output files with built-in self-checks (character counts, keyword placement, structure validation). No vague instructions — the prompt is fully specified.

**Outputs:**
- `04-listing/titles.md` — 3 options with character counts; recommended pick highlighted
- `04-listing/tags.md` — 13 tags ordered by search volume with source column
- `04-listing/descriptions.md` — full structured description

**Rules (enforced by the prompt):**
- Title: 140 chars max; top keyword in first 30 chars; comma-separated stacking
- Tags: 20 chars max each; tag 1 = highest-volume keyword; multi-word phrases only
- Description: opens with emotional hook; uses top 3 keywords naturally; no "unique" or "quality"

### 4.4 Pricing

```bash
python3 scripts/fetch-pp-costs.py --blueprint <id> --pp <provider_id>
```

Formula: **Printify cost × 5 = list price | list ÷ 2 = sell price** (permanent 50% off, always on)

This gives the same 51% net margin as cost×2.5, but the sale badge never disappears — Etsy promotes sale listings continuously in search.

Copy the size/cost table from the script output into `04-listing/pricing.md`.

**Output:** `04-listing/pricing.md`

### 4.5 Generate listing-strategy.html
Tell the AI:
> "Generate listing-strategy.html consolidating the finalized title, tags, description, pricing, and color decisions"

The AI generates a self-contained 6-tab HTML document saved to `04-listing/listing-strategy.html`:

| Tab | Content |
|---|---|
| Strategy | Approach recommendation, key decisions, rationale |
| Titles | All title options with character counts; final pick highlighted |
| Tags | All 13 tags ordered by search volume |
| Price | Cost / list / sale per size tier; margin % per variant |
| Colors | Color list with ink-group assignments (white-ink for dark shirts vs black-ink for light shirts) |
| Personalization | Personalization field instructions (if applicable) |

Review all 6 tabs. When everything looks right, proceed to 4.6.

**Output:** `04-listing/listing-strategy.html`

### 4.6 Review listing-preview.html and approve
Tell the AI:
> "Generate listing-preview.html with the final Etsy listing preview and Printify setup details"

The AI generates a 3-tab HTML document saved to `04-listing/listing-preview.html`:
- **Tab 1 / Tab 2 (one per design):** Etsy listing view — title, description, tags, price, color list, personalization instructions exactly as they'll appear on Etsy
- **Tab 3 (Printify Setup):** API payload summary — design files, placement values, color groups, variant count per group

Review this document carefully. Confirm every field is correct. **This is the last checkpoint before any API calls are made.** Once approved, run the creation script in Phase 5.

**Output:** `04-listing/listing-preview.html`

### Gotchas
- Etsy uses title AND tags together for indexing — repeat your top keywords in both
- First 3 tags carry the most weight — never waste them on low-volume phrases
- **Shipping decision:** Two valid approaches — pick one before publishing:
  - *Built-in free shipping* — include shipping cost in item price, offer free shipping on all orders
  - *Separate shipping + $35 threshold* — charge $5.99 first item / $1.99 additional, enable Etsy's Free Shipping Guarantee at $35+ to get the free shipping badge in search and incentivise multi-item orders

---

## Phase 5 · Printify Setup

**Goal:** Products on Printify as drafts — created by script with the correct variant structure, placement, and pricing.

### 5.1 Create a niche script

Each niche gets its own creation script at `projects/[niche]/scripts/create-[niche]-listings.py`. The script:
- Imports `printify_core` from `shared/` (the shared Printify API library)
- Defines a `LISTINGS` array with one entry per design: title, description, dark_file, light_file, placement
- Handles `--listing N` (create one design at a time) and `--finalize <product_id>` (sync placement)

Tell the AI:
> "Create the Printify creation script for [niche], using the finalized listing copy from Phase 4"

The AI generates the script with the title and description from listing-preview.html baked in.

### 5.2 Create Design 1

```bash
python projects/[niche]/scripts/create-[niche]-listings.py --listing 1
```

This script:
1. Fetches variant groups from the Printify catalog
2. Uploads `design1-white.png` (white ink → dark shirts) and `design1-black.png` (black ink → light shirts)
3. Creates the product draft with an initial 2-group print_areas structure
4. Immediately rebuilds print_areas with the correct per-color structure: 1 default (all non-light colors) + 1 per light color (8 size variants each)
5. Sets pricing at cost × 5

**Output:** Product created as DRAFT in Printify. Terminal prints the product ID and exact next-step commands.

### 5.3 Verify placement in Printify editor

1. Open Printify → find the newly created draft
2. Click into the editor for a dark shirt variant — confirm the design is centred and not clipped
3. Click into a light shirt variant (e.g. White) — confirm it shows the black-ink design, not invisible white-on-white
4. If placement needs adjustment: drag in the visual editor, then **Save**

### 5.4 Sync placement to all print_areas

```bash
python projects/[niche]/scripts/create-[niche]-listings.py --finalize <product_id>
```

The script fetches the product, detects which print_area the user changed in the visual editor (the outlier — least common placement across all print_areas via `collections.Counter`), and pushes that placement to all print_areas. Every color variant now uses the verified placement.

### 5.5 Repeat for each remaining design

```bash
python projects/[niche]/scripts/create-[niche]-listings.py --listing 2
# verify in Printify editor, then:
python projects/[niche]/scripts/create-[niche]-listings.py --finalize <product_2_id>
```

Each design must be verified and finalized independently — designs may have different proportions or y-position.

### Known-good placement values

| Blank | x | y | scale | Verified |
|---|---|---|---|---|
| Gildan 5000 | 0.5 | 0.547735567085003 | 0.8777092933600811 | 2026-05-31 |

Add new blanks here as you verify them.

### Gotchas
- The per-color print_area structure (1 default + 1 per light color) is required for the Printify editor and auto-generated Etsy mockups to show the correct ink color — a simple 2-group split renders invisible white ink on light shirts in the editor
- Always include `decoration_method: "dtg"` in every placeholder — Printify silently drops images if this field is missing (no error returned)
- Use the product's own variant list when building print_areas — Printify adds ~7 discontinued variants after creation that don't appear in the catalog endpoint
- `--finalize` detects the outlier placement via `collections.Counter` — you only need to adjust placement once in the visual editor on any single variant; `--finalize` propagates it everywhere
- If a product returns 404 immediately after creation, it's a Printify server hiccup — re-run `--listing N`

---

## Phase 6 · Sample

**Goal:** Verify what customers will actually receive.

### 6.1 Order a sample
In Printify: go to your product → Order a sample → Ship to yourself.
Cost is typically $10–$20 including shipping.

### 6.2 Check when it arrives
- Is the print placement centred and not clipped?
- Is the print colour accurate vs the design file?
- Does the sizing match the size chart?
- Is the print quality good after one wash?

If anything is off, adjust the design or placement and re-order before going live.

---

## Phase 7 · Go Live

**Goal:** Active Etsy listing with real traffic potential.

### 7.1 Publish from Printify to Etsy
In Printify: product → Publish → Select Etsy shop → Publish.

This pushes the product, variants, and your entered title/description/tags to Etsy automatically.

### 7.2 Upload mockup photos to Etsy listing
Upload the listing photos you built in Phase 3 from `03-mockups/`.
Check slot numbers match the plan (slot 7 = color chart, slot 8 = sizing guide).

### 7.3 Run permanent launch sale
- Set list price in Printify to **cost × 5** (already done if following Phase 4 pricing)
- In Etsy → Marketing → Sales & Discounts: run a **50% off sale, permanent**
- Schedule sales at least 1 week ahead at all times — Etsy doesn't auto-renew them

### 7.4 Set up Etsy email automations (one-time setup)
In Etsy → Marketing → Sales & Discounts, configure all three automations before your first sale:
1. **Abandoned cart** — ~45–50% off coupon
2. **Favourited item** — ~55% off coupon
3. **Thank you / repeat purchase** — ~55–60% off coupon

Set coupon percentages to match your daily sale discount to prevent stacking. Set once, runs forever.

### 7.5 Track performance monthly
Tell the AI:
> "Update metrics.md with this month's stats from Etsy Shop Stats"

Track: views, visits, conversions, top search terms, revenue.

---

## Phase 8 · Post-launch Diagnostics

**Goal:** Know exactly what to fix based on which number is broken.

Work through stages in order — don't skip ahead.

| Symptom | Cause | Fix |
|---|---|---|
| No views | SEO — listing not indexed or ranking low | Revisit title (first 30 chars human-readable), tags (top 3 = highest volume), description (keywords at top). New listings take 2–3 weeks to appear in competitive searches. |
| Views, no clicks | Mockup — thumbnail not stopping the scroll | Change main listing image. Test a different mockup style. Tighten the thumbnail crop in Etsy listing editor. |
| Clicks, no interactions | Design or price — buyers not engaging | Check design passes the principles checklist. Confirm color chart + sizing guide are in consistent image slots. Check your price vs. competitors. |
| Interactions, no sales | Trust — buyers hesitating at checkout | Check for negative reviews. Add a video. Confirm all popular size/color variants are enabled. Verify the sale is currently running (countdown timer creates urgency). |

---

## Phase 9 · Scaling Winners

**Goal:** Multiply what the market proves is working — never guess at scale.

### 9.1 The 5-variation multiplier
When any listing makes its first sale, immediately create 5 more variations before doing anything else:
- Different mockup styles as the main image (lifestyle, flat lay, close-up, different background color)
- Different colorways as the featured thumbnail
- Publish each as a **separate listing**, not a variant

6 total listings targeting the same validated concept → Etsy's algorithm promotes the whole shop when one listing converts.

### 9.2 Cross-niche translation
Duplicate a proven design template and swap only the niche element:
- Nurse humor design → duplicate → swap to "teacher" or "accountant"
- Holiday saying → apply to the next holiday
- A slogan format that works → apply to a new sub-niche

### 9.3 50/50 rule for new designs
Half of new designs = concept-level iterations of proven winners (different angle, different slogan, same proven structure).
Half = fresh research into new niches. Research never fully stops.

### 9.4 Listing volume targets
- Part-time: 5–10 quality listings/week is sustainable and compounds over time
- Full-time: ~20 listings/day is the top-performer benchmark
- ~1,000 quality listings following this framework → expect $1,000–$2,000/month profit (rough benchmark, not a guarantee)
- Batch tasks by type on separate days: research day, design day, upload day — more efficient than doing all steps daily

### 9.5 P&L check (weekly)
Track weekly: revenue, Printify costs, Etsy fees, ad spend, subscriptions.
- COGS (Printify) should be ~40–42% of revenue
- Software subscriptions should be ≤3% of revenue — audit and cut anything unused monthly

---

## Repeating for a New Niche

Everything in `/shared/` carries over:
- `printify_core.py` — the Printify API library; import it in every new niche creation script
- `supplier-notes.md` — placement values for blanks you've already verified
- `etsy-seo-rules.md` — Etsy title/tag rules
- `knowledge/strategies-reference.md` — POD strategies and course insights

For a new niche:
1. Create a new folder under `/projects/new-niche-name/`
2. Start at Phase 1 Research
3. At Phase 5, create a new niche script at `projects/[new-niche]/scripts/create-[new-niche]-listings.py` that imports `printify_core`
4. Reference `supplier-notes.md` for placement if using the same blank (Gildan 5000 values already verified)

---

## Tools Reference

| Tool | When to use | How to invoke |
|---|---|---|
| Playwright | Scraping Etsy competitor listings and eRank data | AI uses it automatically |
| Firecrawl | Faster bulk scraping of competitor pages | AI uses it automatically |
| Printify API | Reading/updating products, placement, variants | AI calls it automatically |
| eRank | Real Etsy search volume data | You log in; AI extracts data |
| `research-competitors.py` | Scrape best-seller Etsy listings into scrapes/ | `python3 scripts/research-competitors.py --niche X --query "Y"` |
| `generate-competitor-report.py` | Build three-tab HTML report from competitors.json + market-insights.md + shop-watchlist.json + patterns-config.json | `python3 scripts/generate-competitor-report.py --niche X` |
| `calculate_placement.py` | Calculate x/y/scale from design image dimensions + print area | `python3 scripts/calculate_placement.py --product_id X` or `--manual W H` |
| `printify_core.py` | Shared Printify API library — all niche creation scripts import this | `import printify_core as pc` (imported from `shared/`) |
| `create-project.py` | Create folder structure + stub files for a new niche | `python3 scripts/create-project.py --niche X` |
| `extract-competitors.py` | Build competitors.json from scrapes/ — deterministic, self-checking | `python3 scripts/extract-competitors.py --niche X` |
| `generate-niche-verdict.py` | Compute verdict math from competitors.json + keywords.md; output pre-filled draft | `python3 scripts/generate-niche-verdict.py --niche X` |
| `prompts/write-market-insights-prompt.md` | Locked prompt for market-insights.md — required sections, source tagging rules, self-check | Paste to Claude: "Follow this prompt exactly. Niche: X." |
| `prompts/write-listing-copy-prompt.md` | Locked prompt for titles + tags + description — reads 4 input files, enforces character limits | Paste to Claude: "Follow this prompt exactly. Niche: X." |
| `extract-competitors-prompt.md` | Schema reference + synthesis rules for market-insights.md (read-only reference) | Do not use for extraction — use the Python script |
