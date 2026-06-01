# Step-by-Step Workflow — Etsy POD with AI

Detailed instructions for each phase. Read README.md first for the overview.

---

## Sub-agent Strategy (context management)

Sub-agents run as separate processes with their own context window. Use them when input is large but output is small — they do the heavy reading without filling up the main conversation.

| Task | How to run | Signal |
|---|---|---|
| Scrape competitors + build competitors.json | **Sub-agent** | Reads 5 large markdown files |
| eRank keyword extraction via Playwright | **Sub-agent** | Large DOM snapshots |
| Analysing all listing files before recommending | **Sub-agent** | Reading 5+ files at once |
| Single Printify API GET or PUT | Inline | Small payload, fast |
| Updating one markdown file | Inline | Data already in context |
| Variant filtering + API updates | Inline | Single script, small result |

**Rule of thumb:** If the task will read more than ~500 lines of content, use a sub-agent.

How to trigger: tell Claude *"use a sub-agent to..."* or *"spawn an Explore/general-purpose agent to..."*

---

## Phase 1 · Research

**Goal:** Know exactly what's selling before you design anything.

### 1.1 Create project folder structure
Tell the AI:
> "Create the folder structure for a new project called [niche-name]"

It will create `/projects/[niche-name]/01-research/` through `06-performance/`.

### 1.2 Scrape top 5 competitor listings

Run the research script:
```bash
python3 scripts/research-competitors.py --niche your-niche-name --query "your etsy search term"
```

This uses Firecrawl to:
1. Search Google for the top Etsy listings matching your query
2. Scrape each listing page in parallel (3 at a time)
3. Save clean markdown files to `projects/[niche]/01-research/scrapes/`
4. Write a manifest file at `projects/[niche]/01-research/scrapes/manifest.json`

Then tell Claude:
> "Read projects/[niche]/01-research/scrapes/manifest.json and create competitors.json"

Claude reads the scraped pages and extracts:
- Price range
- Title keywords
- Colors mentioned in descriptions
- Rating and Star Seller status
- Description structure and hooks
- Ships from location

**Output:** `.firecrawl/etsy-listing-*.md` (raw) + `01-research/competitors.json` (structured)

**Note:** Color and size *dropdown* values aren't scraped (Etsy loads those via JS). Colors are extracted from the description text instead — usually just as accurate.

### 1.3 Extract market insights
Tell the AI:
> "Analyse competitors.json and write market-insights.md — what colors, sizes, and prices are most common? What gaps exist?"

**Output:** `01-research/market-insights.md`

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

**Free plan limit:** 5 searches per day — plan which keywords matter most before you start.

**Output:** Data added to `01-research/keywords.md`

### Gotchas
- eRank free tier shows search volume for the main keyword but locks competition data with "xxx" — that's fine, volume is what matters most
- Always check both the exact phrase ("save the date shirt") AND broader terms ("save the date") — the broader term often gets 10× more searches

---

## Phase 2 · Design

**Goal:** A print-ready design file based on research.

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
1. **Black design** (`design-name-black.png`) → for white and ivory shirts only
2. **Off-white design** (`design-name-offwhite.png`) → for all other colorways (including dark shirts)

Using pure white ink on dark shirts produces muddy or invisible prints. The off-white version triggers a double ink layer on DTG printers. Assign the correct version to each color group in Printify's canvas editor.

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
1. Search Etsy for your product + niche (e.g. "save the date shirt")
2. Open eRank → Listing View — this overlays an outlier score on each listing (how many times better it sells vs. other listings in the same shop)
3. Look for listings with high outlier scores (e.g. 7×, 30×, 110×) — note what mockup style those listings use
4. Also check your competitors.json — what mockup styles are those top sellers using?

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

## Phase 4 · Printify Setup

**Goal:** Products on Printify with correct placement and the right variant set.

### 4.1 Create one product manually in Printify
1. Log into Printify → Create product
2. Select your blank (e.g., Gildan 5000)
3. Upload your design PNG
4. Set placement in the visual editor until the preview looks correct
5. Save the product

**Do NOT create all your products yet — just one first.**

### 4.2 Read and save placement values
Tell the AI:
> "Read the placement for product [name] via the Printify API and save the x/y/scale values"

The AI calls:
```
GET /v1/shops/{shop_id}/products/{id}.json
```
And extracts `print_areas[].placeholders[].images[]` → x, y, scale.

Values get saved to `shared/supplier-notes.md` for reuse.

**Why this matters:** Printify's default `scale=1.0` fills the full print template including edge bleed — designs get clipped. The safe scale for Gildan 5000 is ~0.878.

### 4.3 Create remaining products
Tell the AI:
> "Create products for [design 2], [design 3] using the same blank"

The AI creates them via the Printify API using your design files.

### 4.4 Copy verified placement to all products
Tell the AI:
> "Copy the placement from [product 1] to all other products"

The AI calls `PUT /v1/shops/{shop_id}/products/{id}.json` for each product with the verified x/y/scale values.

### 4.5 Reduce variants to ≤100 for Etsy
Etsy's limit is 100 variants per listing. Gildan 5000 has 32 colors × 8 sizes = 255 by default.

Tell the AI:
> "Based on the competitor research, which colors should we keep? Update all products to only enable those variants."

The AI:
1. Checks market-insights.md for which colors competitors actually offer
2. Selects the top 12 colors × 8 sizes = 96 variants (under the 100 cap)
3. Disables the rest via the Printify API

**Output:** All products updated to 96 variants.

### Known-good placement values

| Blank | x | y | scale | Verified |
|---|---|---|---|---|
| Gildan 5000 | 0.5 | 0.547735567085003 | 0.8777092933600811 | 2026-05-31 |

Add new blanks here as you verify them.

### Gotchas
- The Printify PUT API requires `variant_ids` array in `print_areas` — if you get error code 8150, that's why
- Always verify placement on the FIRST product visually before bulk-copying to the rest

---

## Phase 5 · Listing

**Goal:** A complete, keyword-optimised Etsy listing ready to publish.

### 5.1 Title
Tell the AI:
> "Write title options for this listing based on the eRank keyword data"

Rules:
- 140 character max
- **First ~30 characters** = human-readable product name (what buyers see truncated in search results)
- **Most-searched keyword must be first** (eRank tells you which one) — balance this with readability in the first 30 chars
- Comma-separated keyword stacking (what all top sellers do)
- Use all 140 characters

**Output:** `04-listing/titles.md`

### 5.2 Tags (13 max, 20 characters each)
Tell the AI:
> "Write the 13 Etsy tags based on the keyword research, ordered by search volume"

Rules:
- Tag 1 = highest search volume keyword
- Use multi-word phrases, not single words
- Don't repeat words unnecessarily across tags — cover different search angles

**Output:** `04-listing/tags.md`

### 5.3 Description
Tell the AI:
> "Write a full Etsy description using the keyword-anchored template"

Structure used by all top sellers:
1. Emotional hook (1-2 lines)
2. Feature bullet points
3. How to order (numbered steps — reduces buyer questions)
4. Sizing guidance (reduces returns)
5. Product specs (material, print method)
6. "Perfect for" list
7. Shipping & production time
8. Care instructions

**Output:** `04-listing/descriptions.md`

### 5.4 Pricing
Tell the AI:
> "Pull the Printify base costs from the API and calculate prices at 60% margin"

Formula: **Printify cost × 5 = list price | list ÷ 2 = sell price** (permanent 50% off, always on)

This gives the same 51% net margin as cost×2.5, but the sale badge never disappears — Etsy promotes sale listings continuously in search.

**Output:** `04-listing/pricing.md`

### Gotchas
- Etsy uses title AND tags together for indexing — repeat your top keywords in both
- First 3 tags carry the most weight — never waste them on low-volume phrases
- **Shipping decision:** Two valid approaches — pick one before publishing:
  - *Built-in free shipping* — include shipping cost in item price, offer free shipping on all orders
  - *Separate shipping + $35 threshold* — charge $5.99 first item / $1.99 additional, enable Etsy's Free Shipping Guarantee at $35+ to get the free shipping badge in search and incentivise multi-item orders

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
- `supplier-notes.md` — placement values for blanks you've already verified
- `etsy-seo-rules.md` — Etsy title/tag rules

For a new niche, just:
1. Create a new folder under `/projects/new-niche-name/`
2. Start at Phase 1 Research
3. Reference shared files for placement (if using the same blank)

---

## Tools Reference

| Tool | When to use | How to invoke |
|---|---|---|
| Playwright | Scraping Etsy competitor listings and eRank data | AI uses it automatically |
| Firecrawl | Faster bulk scraping of competitor pages | AI uses it automatically |
| Printify API | Reading/updating products, placement, variants | AI calls it automatically |
| eRank | Real Etsy search volume data | You log in; AI extracts data |
