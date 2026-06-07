# Research Gap Tracker

> Living document. Gaps are ordered by workflow stage — fix them in the order you encounter them.
> When a gap is fixed, change status to ✅ Done and note what was done.
> When new source material reveals new gaps, append to the correct stage section.

---

## Quick Index

| Gap | Name | Stage | Files Touched | Status |
|---|---|---|---|---|
| GAP-12 | Add Phase 0 Niche Discovery | Phase 0 | WORKFLOW.md, shared/seasonal-calendar.md | ✅ Done |
| GAP-13 | Alura top-sellers scraper | Phase 0 | scripts/research-top-sellers.py, WORKFLOW.md | ✅ Done |
| GAP-07 | Schema: sales estimate + velocity fields | Phase 1.2 | extract-competitors-prompt.md, generate-competitor-report.py, research-competitors.py | ✅ Done |
| GAP-09 | Schema: mockup_style field | Phase 1.2 | extract-competitors-prompt.md, WORKFLOW.md Phase 3.1 | ✅ Done |
| GAP-01 | Competitor shop watchlist | Phase 1.2 | scripts/research-shops.py, shop-watchlist.json | ✅ Done |
| GAP-05 | Visual inspiration board | Phase 1.2 | inspiration-images/, inspiration-board.md (new) | 🔴 Open |
| GAP-02 | Monthly sales per listing (eRank) | — | ✅ Merged into GAP-07 | ✅ Merged |
| GAP-10 | eRank trend direction | Phase 1.4 | keywords.md, WORKFLOW.md | ✅ Done |
| GAP-08 | Niche Verdict mandatory block | Phase 1.3→2 gate | extract-competitors-prompt.md, WORKFLOW.md | ✅ Done |
| GAP-04 | Sub-niche angle decision | Phase 1.3→2 gate | 02-design/brief.md | 🔴 Open |
| GAP-11 | Phase 6.5 Pre-Publish Audit | Phase 6.5 | WORKFLOW.md | 🔴 Open |
| GAP-14 | Product + Print Provider selection guide | Phase 2 | WORKFLOW.md, shared/pp-selection-guide.md, scripts/fetch-pp-costs.py | ✅ Done |
| GAP-03 | 15/month rule go/no-go gate | — | ✅ Merged into GAP-08 | ✅ Merged |
| GAP-06 | Seasonal launch timing check | — | ✅ Merged into GAP-12 | ✅ Merged |

---

---

## STAGE: Phase 0 — Niche Discovery

> These gaps must be fixed before any Phase 1 work begins on a new niche.
> Phase 0 does not yet exist in WORKFLOW.md — both gaps below add it.

---

### GAP-12 — No Phase 0 (Niche Discovery before research begins)

**What's missing:**
`WORKFLOW.md` starts at Phase 1 (competitor scrape). There is no structured process for finding and validating a niche *before* committing to a full Phase 1 scrape. The current process implies you already know what niche to research. This is a gap for anyone starting from scratch or expanding to a new niche.

**Why it matters:**
Running a full Phase 1 scrape on a dead niche wastes time and Firecrawl credits. A 15-minute Phase 0 check can confirm buyer language exists (autocomplete), demand exists (eRank volume), and the entry window is open (seasonal timing) before any scraping starts.

> **Note:** This gap absorbs GAP-06 (seasonal timing check). The timing check becomes Step 3 of Phase 0. GAP-06 has no separate fix.

**Firecrawl?** No for Phase 0 itself. Firecrawl enters at Phase 1 once the niche is confirmed.

**Methods included (Amazon/DS Quick View method excluded — requires browser extension manual install):**

**Fix — step by step:**
1. Open `WORKFLOW.md`. Add a new **Phase 0 — Niche Discovery** section before Phase 1. Content:

> **Goal:** Confirm a niche has real buyer demand and a viable entry window before running Phase 1.
>
> **Method A — Etsy Autocomplete (buyer language check, free, no account)**
> 1. Open Etsy in an incognito window (do NOT be logged into your seller account — skews results).
> 2. Type a broad identity word (e.g. "nurse", "camping", "retirement").
> 3. Record every autocomplete suggestion — these are real buyer phrases.
> 4. Repeat with the word + each letter: "nurse a", "nurse b", etc. Focus on: a, b, c, f, g, h, s, t.
> 5. Result: a list of candidate niche phrases in confirmed buyer language.
>
> **Method B — Cross-niche substitution (free, no tools)**
> 1. If you have an existing winning design structure (a phrase format, a humor angle), list 10 other identity words that slot into the same format.
> 2. Prefer less-obvious occupations/hobbies (ICU tech, arborist, disc golf) over saturated ones (nurse, teacher).
> 3. For each candidate, run it through Method A to confirm buyers are searching for it.
>
> **Method C — eRank Keyword Ideas (free, uses 1 daily credit)**
> 1. In eRank Keyword Tool, enter the broad niche keyword.
> 2. Scroll to the "Keyword Ideas" section. Sort by competition (low → high).
> 3. Look for phrases with green competition and meaningful volume — these are sub-niche entry points.
> 4. Only spend an eRank credit here when Methods A and B have already produced a strong candidate.
>
> **Timing check (incorporates GAP-06):**
> Before committing to a seasonal niche, confirm today's date is at least 35 days before the event. If not: (a) choose an evergreen niche instead, or (b) start immediately and accept lower ranking on first launch.
> Reference `shared/seasonal-calendar.md` for "start by" dates. (Create this file if it doesn't exist — see step 2 below.)
>
> **Optional Alura check (adds 2 minutes, uses Firecrawl credits):**
> Run: `python3 scripts/research-top-sellers.py --niche your-niche-name`
> Pass the raw markdown to Claude. Ask Claude to extract the listing data as JSON and save to `01-research/top-sellers-clothing.json`.
> Then tell Claude: "Search top-sellers-clothing.json for [your niche keyword]. Report how many listings match and their monthly sales."
> - 3+ matches with monthly_sales above 100 → demand confirmed at top-seller level
> - 0 matches → niche may be new or underserved — proceed to Phase 1 but treat as uncertain
>
> **Output of Phase 0:** One confirmed niche keyword that has appeared in autocomplete AND passed an eRank volume check. Only after this does Phase 1 begin.

2. Create `shared/seasonal-calendar.md` with major POD holidays and 35-day-out "start by" dates:

| Holiday | Date | Start by |
|---|---|---|
| Mother's Day | May 10 | Apr 5 |
| Father's Day | Jun 15 | May 11 |
| Back to School | Sep 1 (approx) | Jul 27 |
| Halloween | Oct 31 | Sep 26 |
| Christmas | Dec 25 | Nov 20 |
| Valentine's Day | Feb 14 | Jan 10 |
| St. Patrick's Day | Mar 17 | Feb 10 |
| Easter | varies | 35 days prior |

**Status:** ✅ Done — Added Phase 0 to WORKFLOW.md (Steps 0.1–0.5: autocomplete script, cross-niche substitution, eRank volume check, timing check, optional Alura check). Created `shared/seasonal-calendar.md` with 12 holidays + "start by" dates + evergreen niche list. Created `scripts/research-autocomplete.py` (Playwright, US context, letter-suffix variants, ranked output). Absorbs GAP-06.

---

### GAP-13 — No Alura top-sellers scraper (confirmed free public data)

**What's missing:**
There is no script to pull Alura's publicly accessible best-selling Clothing listings. Alura publishes a ranked list of top Etsy listings by category — with estimated total sales, monthly sales, and revenue — on pages that require no login and no account.

**Why it matters:**
Before running a full Phase 1 scrape, you can check in 30 seconds whether your niche has any presence among the top sellers. If 3+ listings in the top sellers list match your niche keyword with high monthly sales → demand is confirmed. If 0 appear → either demand is low or the niche is genuinely new and underserved. This is faster than running a Phase 1 scrape on a guess.

**Firecrawl?** Yes — confirmed working.
Live test on 2026-06-04 returned a ranked list of clothing listings with sales data (e.g., #1: "Peaches Records Shirt", 13,179 total sales, 449 monthly sales). Page renders correctly with a 4-second JS wait. No login required.

**Stability caveat:** Alura could restrict or restructure this page at any time. If the scrape returns navigation-only content (no listing rows), the page has changed — fall back to the in-house estimate from GAP-07.

**Fix — step by step:**
1. Create `scripts/research-top-sellers.py`:

```python
#!/usr/bin/env python3
"""
research-top-sellers.py
Scrapes Alura's public best-selling Clothing page and saves ranked listing data.
Usage: python3 scripts/research-top-sellers.py --niche your-niche-name
"""

import os, json, requests, argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
FIRECRAWL_KEY = os.environ.get("FIRECRAWL_API_KEY")

def scrape_alura():
    resp = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"},
        json={
            "url": "https://www.alura.io/best-selling-etsy-items/clothing",
            "formats": ["markdown"],
            "onlyMainContent": True,
            "waitFor": 4000
        },
        timeout=30
    )
    return resp.json().get("data", {}).get("markdown", "")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", required=True)
    args = parser.parse_args()

    out_dir = BASE_DIR / "projects" / args.niche / "01-research"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "top-sellers-clothing-raw.md"
    out_path = out_dir / "top-sellers-clothing.json"

    print("Scraping Alura best-selling Clothing page...")
    markdown = scrape_alura()

    if not markdown or len(markdown) < 500:
        print("✗ Scrape returned minimal content — Alura page may have changed. Check the URL manually.")
        return

    raw_path.write_text(markdown)
    print(f"✓ Raw markdown saved to {raw_path}")
    print(f"  Pass {raw_path} to Claude with this instruction:")
    print()
    print('  "Read this markdown from Alura\'s best-selling Clothing page. Extract each listing row')
    print('   as a JSON object with fields: title (string), etsy_url (string), total_sales (integer),')
    print('   monthly_sales (integer), revenue_estimate (string), rank (integer).')
    print('   Skip the placeholder row (the one with \'Shop name\' and \'123,123\'). Return a JSON array."')
    print()
    print(f"  Save Claude's output to: {out_path}")

if __name__ == "__main__":
    main()
```

2. The WORKFLOW.md Phase 0 entry for the Alura check is covered in GAP-12, step 1 (Optional Alura check block). No separate WORKFLOW.md edit needed here.

3. Add to Phase 1 market-insights.md synthesis (optional cross-reference):

> "If `top-sellers-clothing.json` exists, check whether any of the Alura top sellers appear in our scraped competitors. If a listing appears in both, note it — it is doubly validated (our scrape + Alura's estimate)."

**Status:** ✅ Done — Created `scripts/research-top-sellers.py` using Firecrawl CLI (4s JS wait, sanity-checks for sales figures, exits gracefully if page changes). WORKFLOW.md Phase 0 Step 0.5 covers the Alura check and Claude extraction instructions. Stability caveat documented in both script and WORKFLOW.md.

---

---

## STAGE: Phase 1.2 — Competitor Scraping: Schema Upgrades

> Both gaps below modify `scripts/extract-competitors-prompt.md`. Implement in a single session —
> opening the file twice is wasted effort. Fix GAP-07 first, then GAP-09 in the same file.
> GAP-07 must be done before GAP-08 (the Niche Verdict block references `estimated_monthly_sales`).

---

### GAP-07 — Schema missing in-house sales estimate + review velocity fields

**What's missing:**
The `extract-competitors-prompt.md` schema captures `reviews` (total count) but has no `favorites_count`, no `reviews_per_month`, and no calculated sales estimate. The `generate-competitor-report.py` sorts by raw review count. This means we rank competitors by lagging history, not current momentum.

**Why it matters:**
A listing with 500 reviews could be dead (2 sales/month) or thriving (80 sales/month). We have no way to tell. Review velocity (`reviews_per_month`) distinguishes active listings from legacy ones. The sales estimate (`review_count × 7`) gives a directional demand signal using the same public inputs Alura uses — without paying for Alura.

**Firecrawl?** Yes — already confirmed.
Both `favorites_count` ("1957 favorites" format) and `most_recent_review_date` ("Jun 2, 2026" format) are present in existing scraped markdown files. No additional scraping needed — just update the extraction prompt to capture them.

**Accuracy caveat:** The 1:7 multiplier (1 review = ~7 sales) is a widely-cited estimate for POD apparel. It is accurate within 20–30% for ranking purposes. Do NOT use it to forecast exact revenue. Adjust multiplier if adding non-apparel product types: use 1:4 for handmade, 1:15 for digital.

**Fix — step by step:**
1. Open `scripts/extract-competitors-prompt.md`. In the schema block, add these fields after `demand_signals`:

```json
"favorites_count": "integer — extract from text matching pattern 'X favorites' or 'X people have this in their favorites' on the listing page. Set to 0 if not visible.",
"most_recent_review_date": "string YYYY-MM-DD — extract from the date shown next to the first (most recent) review in the reviews section. Format like 'Jun 2, 2026' → '2026-06-02'. Set to null if no reviews.",
"reviews_per_month": "float — calculated. If most_recent_review_date is null or reviews is 0, set to 0. Otherwise: months_active = full months between most_recent_review_date and today (minimum 1). reviews_per_month = reviews ÷ months_active, rounded to 1 decimal.",
"estimated_monthly_sales": "integer — calculated. reviews_per_month × 7, rounded to nearest whole number. Label clearly as an estimate. Set to 0 if reviews_per_month is 0.",
"favorites_per_review": "float — calculated. favorites_count ÷ reviews, rounded to 1 decimal. Set to null if reviews is 0. Interpretation: above 5.0 = high interest, possible conversion problem. 1.0–5.0 = healthy active listing. Below 1.0 = legacy listing with declining interest."
```

2. In the same file, add to the extraction instruction section:

> "For review dates: look immediately after reviewer names — they appear as 'Mon DD, YYYY' (e.g., 'Jun 2, 2026'). The first date you find in the reviews section is the most recent. Convert to YYYY-MM-DD format."
>
> "For favorites: look for the pattern 'X favorites' near a heart icon at the top of the listing. May also appear as 'X people have this in their favorites'."

3. Add to the self-check block:

> "5. **Velocity check**: report how many listings have reviews_per_month above 20 (high velocity) and how many are below 2 (likely legacy). If more than half the scraped listings are below 2 reviews/month, flag it — the niche may be declining."

4. Open `scripts/generate-competitor-report.py`. In the `build_top_strip` function (around line 141), change the sort key from `reviews` to `estimated_monthly_sales`:
```python
# Change:
key=lambda e: e.get('reviews', 0), reverse=True
# To:
key=lambda e: e.get('estimated_monthly_sales', 0), reverse=True
```

5. In the same file, add `estimated_monthly_sales` to the sort dropdown in the `competitors_tab` HTML block:
```html
<option value="est-sales">Est. Monthly Sales</option>
```
And add the sort case to the `setSort` JS function and the `render()` sort block.

6. Update `scripts/extract-competitors-prompt.md` synthesis instruction for market-insights.md: replace "sort by review count" with "sort by estimated_monthly_sales descending. Call out top 3 listings by estimated_monthly_sales as benchmark listings. Flag any listing with favorites_per_review above 5.0 (high interest, possible conversion gap). Flag any listing with reviews_per_month below 2 as legacy — do not use as a pricing or keyword benchmark."

**Status:** ✅ Done — Added 6 schema fields (favorites_count, most_recent_review_date, oldest_visible_review_date, reviews_per_month, estimated_monthly_sales, favorites_per_review). Added FAVORITES RULE + REVIEW DATE RULE to extraction rules. Added velocity self-check (#5). Added synthesis instruction. Updated generate-competitor-report.py to sort by estimated_monthly_sales (default), added est-sales badge to cards. Added Etsy API creation date fetch (Step 3) to research-competitors.py with oldest_visible_review_date fallback. Updated .env.example + SETUP.md.

---

### GAP-09 — Schema missing mockup_style field

**What's missing:**
The schema in `extract-competitors-prompt.md` has no `mockup_style` field. Phase 3.1 of `WORKFLOW.md` currently instructs the user to manually browse eRank Listing View and visually note mockup styles from high-performing listings. This is disconnected from the data already collected in Phase 1.

**Why it matters:**
The mockup decision in Phase 3 should come from data, not a separate manual browsing session. We already scrape the listing descriptions in Phase 1 — mockup style is classifiable from description text. Adding the field closes the loop automatically.

**Firecrawl?** No for classification — YES for the scrape itself (already done). Etsy CDN image URLs use hashed filenames with no readable descriptors. Classification MUST come from description text only, not image URLs.

**Fix — step by step:**
1. Open `scripts/extract-competitors-prompt.md`. Add this field to the schema after `design_style`:

```json
"mockup_style": "one of: lifestyle-worn | flat-lay | ghost-mannequin | close-up-detail | multi-color-grid | studio-plain | unknown"
```

2. Add this classification instruction to the field-by-field rules section:

> **MOCKUP STYLE RULE**
> Classify from listing description text and title ONLY. Do NOT use image URLs — Etsy CDN filenames are hashed and unreadable.
>
> - `lifestyle-worn` — description mentions "model", "worn by", "lifestyle photo", or person in a natural setting
> - `flat-lay` — description mentions "flat lay", "overhead", or "laid flat"
> - `ghost-mannequin` — description mentions "mannequin" or "invisible mannequin"
> - `close-up-detail` — description mentions "close-up", "detail shot", or "print quality photo"
> - `multi-color-grid` — description mentions "all colors shown", "color options photo", or "color chart photo"
> - `studio-plain` — description mentions "plain background", "white background", or "studio"
> - `unknown` — none of the above signals present

3. Add to the market-insights.md synthesis instruction in the prompt:

> "Add a section called 'Recommended Mockup Style'. Report the most frequent mockup_style among the top 5 listings sorted by estimated_monthly_sales. If there is a tie, list both. This becomes the recommended style for slot 1 (main listing photo) in Phase 3."

4. Open `WORKFLOW.md`. In Phase 3.1, replace the current instruction to manually browse eRank Listing View with:

> "Check the 'Recommended Mockup Style' section in market-insights.md — this is derived from the Phase 1 competitor scrape and is the primary input for slot 1. You may still browse eRank Listing View to confirm, but the scraped data takes precedence."

**Status:** ✅ Done — Added `mockup_style` field to schema after `design_style`. Added MOCKUP STYLE RULE (7-value classification from description text only, not image URLs). Added Recommended Mockup Style synthesis instruction to market-insights.md block. Updated WORKFLOW.md Phase 3.1 to read from market-insights.md first, fall back to eRank Listing View only when majority are `unknown`.

---

---

## STAGE: Phase 1.2 — Competitor Scraping: Data Depth

> These gaps add richer data collection after the core Phase 1.2 scrape is complete.
> Neither changes the schema prompt — they are separate data collection actions.

---

### GAP-01 — No competitor shop watchlist (listing data ≠ shop data)

**What's missing:**
We scraped 62 *listings* but never built a list of 5+ competitor *shops* with shop-level metrics: monthly sales, monthly revenue, total listings, listing-to-sales ratio. The course (Alek) says the shop watchlist is the primary reference for keywords, pricing, and mockup decisions — not individual listings.

**Why it matters:**
A listing with 532 reviews could be a dead shop now making 2 sales/month. Without shop-level data you can't tell which competitors are actually generating income vs. coasting on old reviews.

**Firecrawl?** Partially.
- Firecrawl CAN scrape an Etsy shop page to get: total sales count, number of active listings, shop age, and listing titles.
- Firecrawl CANNOT get monthly sales or monthly revenue — that data lives inside eRank's shop analyzer and is not on the public Etsy page.

**Fix — step by step:**
1. Open `projects/personalized-gift-for-dad/01-research/market-insights.md` — Section 9 (Shirt-Specific Competitive Summary) has 5 listing IDs. Convert each listing ID to its shop URL by finding the shop name from competitors.json.
2. Use Firecrawl to scrape each shop page (format: `https://www.etsy.com/shop/[ShopName]`). Save raw output to `projects/personalized-gift-for-dad/01-research/raw-shops/[shopname].md`.
3. Extract from each scraped shop page: shop name, total sales number, active listing count, shop opened date.
4. Calculate listings-to-sales ratio (total sales ÷ active listings). Higher ratio = better conversion per listing = stronger competitor to study.
5. Create file `projects/personalized-gift-for-dad/01-research/shop-watchlist.json` (NOT `competitors.json` — that file already holds listing-level data) with this structure per shop:
   ```json
   {
     "shop_name": "",
     "etsy_url": "",
     "total_sales": 0,
     "active_listings": 0,
     "shop_opened": "",
     "sales_per_listing_ratio": 0,
     "monthly_sales_estimated": null,
     "source": "firecrawl-scrape"
   }
   ```
6. For monthly sales: log into eRank using Playwright (already confirmed working), run each shop URL through eRank's shop analyzer, and fill in `monthly_sales_estimated`.
7. Flag any shop with monthly sales < 15 — those are not worth studying closely (Alek's threshold).

**Status:** ✅ Done — Created `scripts/research-shops.py`. Scrapes public Etsy shop pages via Firecrawl (no API, no login). Derives shop monthly sales from 3 signals: Method 1 (total_sales ÷ months_active), Method 2 (rate-based review projection × 7 using dynamic 5-month / 20-page window to smooth seasonal spikes), Method 3 (listing rollup from competitors.json). Cross-validates all three, sets confidence High/Medium/Low based on signal divergence (<40% = high, 40–70% = medium, >70% = low), adds trend signal (growing/stable/declining) via M2 ÷ M1 ratio. Results feed into the Shop Intelligence tab in competitor-report.html. eRank not needed — confirmed it uses the same review-based formula. Run: `python3 scripts/research-shops.py --niche <niche>`

---

### GAP-05 — No visual design inspiration board (patterns are text-only)

**What's missing:**
Both courses say to save 10–15 best-seller product images into a visual board before designing. We documented patterns in markdown text — that's useful for analysis but not the same as having actual reference images when building a design.

**Why it matters:**
Text descriptions like "bold DAD lettering with each child's name printed below" are ambiguous. A designer (or AI generating a design brief) needs to see the actual visual execution to understand spacing, weight, color, and composition.

**Firecrawl?** Yes — partially.
Firecrawl can scrape Etsy listing pages and extract image URLs. We can then download those images locally as a reference folder.

**Fix — step by step:**
1. Use Firecrawl scrape on each of the 5 shirt listing URLs from `market-insights.md` Section 9.
2. From each scraped page, extract the main product image URL (look for `og:image` meta tag or the first large `il_794xN` image).
3. Download each image to `projects/personalized-gift-for-dad/01-research/inspiration-images/[listing-ID].jpg`.
4. Create `projects/personalized-gift-for-dad/01-research/inspiration-board.md` — a markdown file that references each image with a one-line note on what to take from it (e.g., "font weight on DAD", "how names are spaced", "which Comfort Colors shade in mockup").
5. Add a link to `inspiration-board.md` at the top of `02-design/brief.md` so it's always referenced alongside the text brief.

**Status:** ✅ Merged into GAP-07 — GAP-07 already adds `reviews_per_month` and `estimated_monthly_sales` (reviews_per_month × 7) to every listing in `competitors.json`. The 15/month threshold check is covered by the Niche Verdict block (GAP-08). No separate eRank session needed.

---

---

## STAGE: Phase 1.4 — eRank Keyword Session

> Both gaps are completed during the same eRank session — do them together to avoid
> wasting daily search credits (free plan = 5 searches/day).

---

### GAP-02 — No confirmed monthly sales data per listing (reviews ≠ sales)

**What's missing:**
`keywords.md` explicitly flags: *"eRank: Login required — not accessible. Volume estimates inferred from result density."* We used review counts as a proxy for demand. Review counts are a lagging indicator — a listing can have 500 reviews and be making 0 sales today.

**Why it matters:**
The whole niche validation rests on whether listings are actively selling. Without monthly sales data, we don't know if "personalized gift for dad" shirts are hot right now or peaked 2 years ago. Alek's rule: only design for niches where listings are hitting 15+ sales/month.

**Firecrawl?** No.
Monthly sales data is not on the public Etsy listing page. It requires eRank's Listing Analyzer (requires login). Firecrawl cannot get this.

**Fix — step by step:**
1. Use Playwright to log into eRank (already confirmed logged in from prior session).
2. Navigate to eRank's Listing Analyzer tool.
3. Paste in each of the 5 shirt listing IDs from `market-insights.md` Section 9: `1701562378`, `1732501325`, `4297033571`, `4482796793`, `4407005111`.
4. For each listing, record: monthly views, monthly sales estimate, monthly revenue estimate, listing age.
5. Add a new section to `projects/personalized-gift-for-dad/01-research/keywords.md` called `## Listing Sales Validation` with a table: Listing ID | Monthly Sales | Monthly Revenue | Clears 15/mo threshold (Y/N).
6. If fewer than 3 of the 5 listings clear 15 sales/month: flag the niche as unvalidated and document the finding. Do not proceed to more designs until this is resolved.
7. If 3+ listings clear the threshold: niche is validated. Update `market-insights.md` Section 7 (Niche Demand Health) to reflect confirmed sales data, not just cart signal proxies.

**Status:** ✅ Done — Added Stop Check section to WORKFLOW.md between Phase 1.4 and Phase 2 (Enter / Enter with sub-niche pivot / Do not enter). Added Niche Verdict block template to extract-competitors-prompt.md output section — Claude fills this in and saves it to top of market-insights.md after building competitors.json. Verdict references estimated_monthly_sales + is_bestseller + in_carts from competitors.json and trend direction from keywords.md (GAP-10).

---

### GAP-10 — No eRank trend direction recorded during keyword research

**What's missing:**
Phase 1.4 of `WORKFLOW.md` captures keyword search volume from eRank but does not capture trend direction (rising / stable / declining / seasonal). A keyword with 140 searches/month that is declining is a worse bet than one with 80/month that is rising.

**Why it matters:**
A declining trend on the primary keyword downgrades the whole niche. A rising trend upgrades it. This takes 10 seconds to note while you are already in eRank and has a direct effect on the Niche Verdict.

**Firecrawl?** No. You are already looking at eRank via Playwright. Just record what you see.

**Important caveat:** eRank's full trend graph (15-month Trend Buzz) is a paid feature. What the free plan shows is a shorter trend indicator below the search volume number — whether this appears on the free plan is unconfirmed. When you next run an eRank keyword search, check: does a trend line or graph appear below the volume number? If yes, use it. If it's locked, check eRank's free "Top 10 Trending Keywords" list as a fallback — if your niche keyword appears there, it's rising.

**Note:** Google Trends is NOT in the current WORKFLOW.md. No removal needed — this gap is purely additive.

**Fix — step by step:**
1. Open `WORKFLOW.md`. In Phase 1.4, after the existing keyword search instructions, add:

> "While in eRank, also note the trend direction for each keyword. Look for a trend line or graph below the search volume number. Record in `keywords.md` using this format:
>
> `Trend: [keyword] → Rising | Stable | Declining | Seasonal (peak: [month]) | Unknown (graph locked on free plan)`
>
> Apply this rule when writing the Niche Verdict:
> - Main keyword trending Declining → downgrade Demand Signal by one level (High → Medium, Medium → Low)
> - Main keyword trending Rising → upgrade Demand Signal by one level
> - Seasonal → note the peak month and flag it in the Niche Verdict basis line"

2. Open `projects/<niche>/01-research/keywords.md` template. Add a `Trend Direction` column to the keyword data table.

**Status:** ✅ Done — Added Step 5 to Phase 1.4 in WORKFLOW.md: while in eRank, record trend direction per keyword (Rising / Stable / Declining / Seasonal / Unknown) in a Trend column in keywords.md. Added adjustment rule: Rising = upgrade Demand Signal one level, Declining = downgrade, Seasonal = note peak month, Unknown = leave unadjusted and flag in Verdict confidence. Free-plan fallback: check eRank's Top 10 Trending Keywords list.

---

---

## STAGE: Phase 1.3 → Phase 2 Gate — Niche Verdict & Positioning

> These two gaps together form the decision checkpoint between research and design.
> Fix GAP-08 first (adds the Verdict block). GAP-04 is the action that follows from the Verdict.
>
> **Two dependencies before the Verdict can be written:**
> 1. GAP-07 must be done — the Verdict block references `estimated_monthly_sales` from competitors.json
> 2. GAP-10 must be done — trend direction from keywords.md feeds into the Demand Signal rating
>
> **WORKFLOW.md sequencing note:** The Verdict gate must be placed AFTER Phase 1.4 (eRank keywords),
> not after Phase 1.3. GAP-08 step 2 reflects this — the stop check goes after eRank, before Phase 2.

---

### GAP-08 — No mandatory Niche Verdict block before Phase 2

**What's missing:**
`WORKFLOW.md` moves directly from Phase 1.3 (write market-insights.md) to Phase 2 (design brief) with no explicit stop gate. There is no required decision — "should we actually enter this niche?" — before design work begins.

**Why it matters:**
Without a required verdict, it's easy to move into design on a niche that doesn't pass basic demand or competition thresholds. The verdict block makes the go/no-go decision explicit and traceable.

> **Note:** This gap absorbs GAP-03 (15/month rule). The 15/month check is now a named field inside the Niche Verdict block, not a separate manual step. GAP-03 has no separate fix.

**Firecrawl?** No. This is a prompt engineering + workflow change only.

**Fix — step by step:**
1. Open `scripts/extract-competitors-prompt.md`. Add this block as the FIRST section of the output template, before any other content:

```markdown
## Niche Verdict [REQUIRED — complete this before writing anything else]

**Demand signal:** [High / Medium / Low]
Basis: [one sentence — reference estimated_monthly_sales of top 3 listings and whether Bestseller badges or "In X carts" signals were found. Then apply trend adjustment from keywords.md: Rising → upgrade one level, Declining → downgrade one level, Seasonal → note peak month]

**Competition barrier:** [High / Medium / Low]
Basis: [one sentence — what proportion of scraped listings have reviews_per_month above 10? If majority do, barrier is High. If few do, barrier is Low.]

**15/month check:** [Pass / Fail]
Basis: [do at least 3 of the top 5 listings by estimated_monthly_sales show 15+ estimated monthly sales? Pass = yes. Fail = no.]

**Recommendation:** [Enter / Enter with sub-niche pivot / Do not enter]
Reasoning: [one sentence]

**If sub-niche pivot recommended:** [specific angle — e.g. a specific occupation, design format, or product type that has fewer dominant competitors in the scraped data]

**Confidence:** [High = verdict backed entirely by our scraped data | Medium = partly inferred | Low = limited data, proceed cautiously]
```

2. Open `WORKFLOW.md`. After Phase 1.4 (eRank keywords) and before Phase 2 (Design), add:

> **Stop check — Niche Verdict:**
> The Verdict is written here — AFTER both market-insights.md (Phase 1.3) and keywords.md trend data (Phase 1.4) are complete. Both sources feed into it.
> Tell Claude: "Write the Niche Verdict for [niche]. Use competitors.json for estimated_monthly_sales and the 15/month check, and keywords.md for trend direction."
> Read the completed Niche Verdict block:
> - Recommendation = "Enter" → proceed to Phase 1.5, then Phase 2.
> - Recommendation = "Enter with sub-niche pivot" → update the project niche direction in brief.md before Phase 2. Do not design for the original broad niche.
> - Recommendation = "Do not enter" → stop. Do not proceed to Phase 2. Start a new project folder for a different niche or the recommended sub-niche.

**Status:** 🔴 Open

---

### GAP-04 — No sub-niche angle selected (brand positioning undefined)

**What's missing:**
The project is targeting "personalized gift for dad" at the broadest level. The Wescale transcript says to pick a specific *angle* before designing — e.g., sentimental/milestone vs. humor/parody vs. millennial gaming dad. Our `market-insights.md` Section 10 (Gaps) identified several angles as *opportunities*, but never committed to one as the shop's positioning.

**Why it matters:**
Without a clear angle, design decisions are arbitrary. The angle determines: which keywords lead, what the thumbnail aesthetic is, what the emotional hook is for the buyer. "Personalized dad shirt" is a keyword, not a positioning.

**Firecrawl?** No.
This is a strategic decision for the user to make. Data to support the decision already exists in our research files.

> **Note:** For future niches, the sub-niche pivot recommendation comes automatically from the Niche Verdict block (GAP-08). This gap is project-specific to the current niche — the options below come from existing research.

**Fix — step by step:**
1. Read `projects/personalized-gift-for-dad/01-research/market-insights.md` Section 10 (Gaps 1–5) — these are already written as distinct angles.
2. Pick exactly ONE angle as the primary launch angle. Options identified:
   - **A. "DAD + kids names" typographic shirt** — lowest friction, highest proven demand (532 reviews), fully automatable. Recommended first launch.
   - **B. Comfort Colors premium lane** — same design as A, premium blank, only 1/61 listings use it, higher price point.
   - **C. Gaming/parody angle** — "DAD LEVEL: UNLOCKED" — millennial dad, no current shirt competition, medium confidence.
3. Write the chosen angle as a one-sentence brief at the top of `projects/personalized-gift-for-dad/02-design/brief.md`: *"This listing targets [X buyer] with [Y emotional hook] using [Z design format]."*
4. All design decisions (fonts, colors, mockup aesthetic) must serve that one sentence. If a design decision doesn't serve it, reject it.

**Status:** 🔴 Open | Decision needed from user

---

---

## STAGE: Phase 2 — Design Brief / Product Selection

> Product and print provider must be locked before mockups (Phase 3) begin.
> The blank determines the mockup template, color palette, and pricing floor.

---

### GAP-14 — No structured product + print provider selection process

**What's missing:**
WORKFLOW.md has no step that walks through *how* to pick a product blank (e.g., Gildan 5000 vs Bella+Canvas 3001 vs Comfort Colors 1717) and which print provider (PP) to use for it. The current process implies you already know what to pick. There is also no step that uses the Printify API to compare real costs across providers for the same product before committing.

**Why it matters:**
The PP choice directly sets the cost floor. Two providers offering the same Gildan 5000 can differ by $2–4 per unit, which shifts margin by 15–20 percentage points. Provider location also affects shipping speed to your target market (US-based PP = faster US delivery = better review scores). Picking the wrong blank or the wrong PP at this stage is expensive to undo after mockups and listing copy are done.

**Firecrawl?** No.
All data needed is available via the Printify API: `GET /v1/catalog/blueprints.json` (all products), `GET /v1/catalog/blueprints/{id}/print_providers.json` (providers for a product), `GET /v1/catalog/blueprints/{id}/print_providers/{pp_id}/variants.json` (costs per color/size). No scraping required. Cross-reference with memory: [[feedback-pricing-check-costs-first]] covers the cost fetch rule.

**Fix — step by step:**
1. Create `shared/pp-selection-guide.md` with these sections:

   **Blank selection criteria**
   | Criterion | Guidance |
   |---|---|
   | Competitor blank | Read competitors.json — what `blank` field is most common among top-3 by estimated_monthly_sales? Start there unless you have a specific reason not to. |
   | Price tier | Gildan 5000 = budget ($8–10 cost), Bella+Canvas 3001 = mid ($12–15), Comfort Colors 1717 = premium ($16–20). Match to your niche's pricing ceiling. |
   | Color range | Check how many colors are in Printify catalog for that blank. More colors = more variant potential but approaches the 100-variant cap faster. |
   | Unisex vs fitted | Most POD shirts are unisex. Only choose fitted if competitor research shows it. |

   **Print provider selection criteria**
   | Criterion | Guidance |
   |---|---|
   | Location | Prefer US-based PP if your target market is US buyers. Check PP location on Printify catalog page. |
   | Quality score | Printify shows a 0–5 quality rating per PP. Prefer 4.5+. |
   | Production time | Check estimated production days shown in Printify catalog. Under 3 business days preferred. |
   | Cost per variant | Must fetch via API — never estimate. Use scripts/fetch-pp-costs.py (see step 3). |
   | Monster Digital note | Confirmed working for Gildan 5000 (from prior session). US-based. Good quality score. Use as default unless cost comparison shows a better option. |

   **Decision order**
   1. Check competitors.json → most common `blank` field → that's your starting candidate.
   2. Confirm it's in Printify catalog and available from at least one US PP with quality 4.5+.
   3. Fetch costs via API. Build margin table. Confirm 60% margin target is achievable (sell price = cost × 2.5).
   4. If margin target fails → try next blank up the price ladder (not down — lower-cost blanks usually have worse quality scores).
   5. Lock blank + PP. Write the choice at the top of `02-design/brief.md` before any design work.

2. Open `WORKFLOW.md`. At the start of Phase 2 (Design Brief), add:

   > **Phase 2.0 — Lock Product + Print Provider (do this before any design work)**
   >
   > 1. Check `competitors.json` → most common `blank` value among top 3 by `estimated_monthly_sales`.
   > 2. Find the blank in Printify catalog. Run: `python3 scripts/fetch-pp-costs.py --blueprint <id>` to compare costs across available print providers.
   > 3. Build a margin table (see `shared/pp-selection-guide.md`). Confirm cost × 2.5 ≥ market price ceiling identified in Phase 1.
   > 4. Pick PP. Record selection at top of `02-design/brief.md`:
   >    ```
   >    Blank: [name]  |  Printify Blueprint ID: [id]  |  Print Provider: [name] (ID: [id])
   >    Cost (S–2XL avg): $[X]  |  List price: $[Y]  |  Target margin: [Z]%
   >    ```
   > 5. Do NOT proceed to Phase 2.1 (design brief text) until this block is filled in.

3. Create `scripts/fetch-pp-costs.py` — a helper that calls the Printify API and prints a comparison table of all print providers for a given blueprint, sorted by average cost:

   ```
   Blueprint 12 (Gildan 5000)
   ─────────────────────────────────────────────────────
   PP ID  Provider Name        Location    Quality  S      M      L      XL     2XL    Avg
   29     Monster Digital      US          4.8      $8.42  $8.42  $8.42  $8.42  $9.98  $8.73
   99     SPOD                 US/EU       4.4      $9.11  $9.11  $9.11  $9.11 $10.50  $9.39
   ...
   ```

   This replaces the manual Printify dashboard cost lookup and makes cost checking a one-command step.

**Status:** ✅ Done — Created `scripts/fetch-pp-costs.py` (fetches Printify API costs for all print providers on a blueprint, prints comparison table sorted by avg cost S–2XL, shows min list price at 60% margin) and `shared/pp-selection-guide.md` (6-step decision guide). Added Phase 2.0 block to WORKFLOW.md. Run: `python3 scripts/fetch-pp-costs.py --blueprint <id>`

---

---

## STAGE: Phase 6.5 — Pre-Publish Audit

> This gap adds a mandatory checklist step between Phase 6 (Sample) and Phase 7 (Go Live).
> It requires no external tools — Claude reads the project folder and checks against it.

---

### GAP-11 — No pre-publish self-audit (Phase 6.5 missing)

**What's missing:**
`WORKFLOW.md` jumps from Phase 6 (Sample) directly to Phase 7 (Go Live) with no structured check against the project files. Phase 8 (Diagnostics) catches SEO and configuration errors — but only after the listing has been live for weeks. All the data needed to catch these errors already exists in the project folder before publish.

**Why it matters:**
Avoidable publish errors (wrong keyword order in title, missing tags, variant count over 100, pricing formula wrong) cost ranking time. A listing that goes live with a bad title is already losing ground. This check takes 2 minutes and prevents it.

**Firecrawl?** No. Claude reads the project folder and checks against it — no scraping needed.

**Fix — step by step:**
1. Open `WORKFLOW.md`. Add a new phase between Phase 6 and Phase 7, labeled **Phase 6.5 — Pre-Publish Audit**.

Content of the new phase:

> Tell Claude: "Run a pre-publish audit on this project."
>
> Claude checks each item and marks Pass or Fail with a one-line reason for any Fail:
>
> | Check | Source |
> |---|---|
> | Title starts with highest-volume keyword from keywords.md | `04-listing/titles.md` + `keywords.md` |
> | Title is 130+ characters (uses most of the 140-char limit) | `04-listing/titles.md` |
> | Top 3 tags match the 3 highest-volume phrases in keywords.md | `04-listing/tags.md` + `keywords.md` |
> | All 13 tag slots are filled | `04-listing/tags.md` |
> | Listing image slot 7 is a color chart | `03-mockups/` file naming |
> | Listing image slot 8 is a sizing guide | `03-mockups/` file naming |
> | Variants are at or under 100 | confirmed via Printify API in Phase 4 |
> | Pricing follows cost × 5 formula (list price), ÷ 2 = sell price | `04-listing/pricing.md` |
> | Niche Verdict recommendation was "Enter" or "Enter with sub-niche pivot" | `01-research/market-insights.md` top block |
>
> Any Fail must be resolved before proceeding to Phase 7. Do not publish with an open Fail.

**Status:** 🔴 Open

---

---

## Merged Gaps (no standalone fix needed)

These gaps are fully covered by another gap's fix steps. Documented here for traceability.

### GAP-03 — 15/month rule go/no-go gate → ✅ Merged into GAP-08

The 15/month check is now the "15/month check: [Pass / Fail]" field inside the Niche Verdict block (GAP-08). Implementing GAP-08 fully resolves this.

### GAP-06 — Seasonal launch timing check → ✅ Merged into GAP-12

The timing check is now Step 3 (Timing check) inside Phase 0 of WORKFLOW.md, added by GAP-12. The `shared/seasonal-calendar.md` file specified in GAP-06 is created as part of GAP-12 step 2. Implementing GAP-12 fully resolves this.

---

---

## How to add a new gap

1. Identify which workflow stage the fix belongs to (Phase 0, Phase 1.2, Phase 1.4, etc.).
2. Add the gap under that stage section, not at the bottom of the file.
3. Add a row to the Quick Index table at the top.
4. Use this template:

```
### GAP-[next number] — [Short name]

**What's missing:**
[One paragraph — what should exist but doesn't]

**Why it matters:**
[One paragraph — what breaks or stays unknown without this]

**Firecrawl?** Yes / Partially / No
[One sentence explaining what Firecrawl can and can't do here]

**Fix — step by step:**
1. ...
2. ...
3. ...

**Status:** 🔴 Open
```
