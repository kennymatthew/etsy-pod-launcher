# Competitor Extraction Prompt
# ⚠️ DO NOT USE FOR EXTRACTION — use `python3 scripts/extract-competitors.py --niche X` instead.
# This file is a reference only: schema definitions and market-insights.md synthesis rules.
# Reason: AI prompt extraction causes context-window degradation over large batches (50+ files),
# leading to silent data corruption (duplicate image URLs, bleed between entries).
# The Python script is deterministic and runs a self-check after every run.

---

Read all `etsy-listing-*.md` files listed in `scrapes/manifest.json` and produce a
`competitors.json` array. Each entry must follow the schema below exactly.

**Before extracting:** check if `scrapes/listing-dates.json` exists. If it does, read it — it maps
listing IDs to `original_creation_date` (YYYY-MM-DD from Etsy API). Use this date as the listing
age anchor for `reviews_per_month` calculations. If the file doesn't exist or a listing ID isn't
in it, fall back to `oldest_visible_review_date` from the scrape.

## Schema

```json
{
  "id":                   "string — Etsy listing ID",
  "url":                  "string — full listing URL",
  "title":                "string — exact title from the listing page, unmodified",
  "price":                "string — starting price as shown, e.g. '$13.64+'",
  "reviews":              "integer — total review count (see RATING RULE below)",
  "rating":               "float  — numeric average (see RATING RULE below)",
  "sales":                "integer or null — shop-level sales count if present, else null",
  "product_type":         "string — what the item physically is, e.g. 't-shirt', 'mug', 'hat'",
  "is_shirt":             "boolean — true only for shirts, sweatshirts, hoodies, tank tops",
  "blank":                "string or null — brand + model if stated (e.g. 'Gildan 5000')",
  "print_method":         "string — see PRINT METHOD RULE below",
  "print_method_confirmed": "boolean — see PRINT METHOD RULE below",
  "personalization":      "boolean",
  "personalization_type": "string or null — what the buyer customizes",
  "design_style":         "string — describe the visual design concept",
  "mockup_style":         "string — one of: lifestyle-in-use | flat-lay | ghost-mannequin | close-up-detail | multi-color-grid | studio-plain | unknown. Classify by viewing the image_url — see MOCKUP STYLE RULE below.",
  "key_phrases":          "array of strings — 3-5 exact keyword phrases from the title",
  "colors":               "array of strings — see COLOR RULE below",
  "shop_name":            "string",
  "notes":                "string — notable selling points: badges, Star Seller, ships from, etc.",
  "image_url":            "string or null — first product image URL (see IMAGE RULE below)",
  "is_bestseller":        "boolean — true if the text 'Bestseller' appears as a badge near the listing title or price. false if not present.",
  "in_carts":             "integer or null — see IN_CARTS RULE below. Set to null if no cart signal found.",
  "demand_signals":       "array of strings — see DEMAND SIGNAL RULE below",
  "favorites_count":      "integer — extract from '[X favorites]' link near the top of the listing. Set to 0 if not found.",
  "most_recent_review_date": "string YYYY-MM-DD — date of the first (most recent) review after '## Reviews for this item'. Format 'Jun 2, 2026' → '2026-06-02'. Set to null if no reviews.",
  "oldest_visible_review_date": "string YYYY-MM-DD — date of the last (oldest) review visible in the reviews section. Set to null if no reviews.",
  "reviews_per_month":    "float — calculated. If reviews is 0, set to 0. months_active = full months from creation anchor to today (minimum 1), where creation anchor = listing-dates.json value for this ID if available, else oldest_visible_review_date. reviews_per_month = reviews ÷ months_active, rounded to 1 decimal.",
  "estimated_monthly_sales": "integer — calculated. reviews_per_month × 7, rounded to nearest whole number. This is a directional estimate only — do not treat as exact. Set to 0 if reviews_per_month is 0.",
  "favorites_per_review": "float — calculated. favorites_count ÷ reviews, rounded to 1 decimal. Set to null if reviews is 0. Signal: above 5.0 = high interest / possible conversion problem; 1.0–5.0 = healthy active listing; below 1.0 = legacy listing with declining interest."
}
```

---

## Field-by-field extraction rules

### RATING RULE (most common error source)
Etsy listing scrapes contain TWO different rating signals. Use the correct one:

| What you see in scrape | What it means | Use it? |
|---|---|---|
| `[5 out of 5 stars]` or `5 out of 5 stars` | The star-widget display — rounds to nearest whole star | ❌ DO NOT USE |
| `4.8 Item average` or `4.9` near the text "Item average" | Recency-weighted numeric average | ✅ USE THIS |
| `(1.6k reviews)` or `1,600 reviews` | Total review count | Use for `reviews` field |

If the numeric average is not present, look for the pattern `[X.X out of 5]` near a review count,
which Etsy shows as the actual rating in some scrape formats. Never use the star icon count.

### COLOR RULE (completeness)
Extract every color listed in the Colors dropdown section. In Etsy scrapes this looks like:

```
Natural ($13.64 - $36.39)
Light Pink ($13.64 - $36.39)
Red ($13.64 - $36.39)
```

**Count the colors you find and include all of them.** Do not summarize ("various colors") or
truncate. If the scrape is truncated and you cannot see all color options, write `null` rather
than a partial list.

### PRINT METHOD RULE (accuracy vs inference)
Only mark a method as confirmed if it is **explicitly named** in the scrape text.

| Evidence | `print_method` value | `print_method_confirmed` |
|---|---|---|
| Listing says "DTG", "Direct to Garment", or "screen printed" | `"DTG"` / `"screen print"` | `true` |
| Listing says "embroidered", "stitched" | `"embroidery"` | `true` |
| Listing says "sublimation", "all-over print" | `"sublimation"` | `true` |
| Gildan 5000 / Bella Canvas + photo upload — DTG implied but not stated | `"DTG"` | `false` |
| No print method evidence at all | `"unknown"` | `false` |

When `print_method_confirmed` is `false`, add a note in `notes` explaining the inference
(e.g., "DTG inferred from Gildan 5000 blank + photo personalization").

### BESTSELLER RULE
Look for the text `Bestseller` appearing as a badge near the listing title or price block (usually within the first 50 lines of the scrape). It may appear as:
- `Bestseller`
- `[Bestseller]`
- `**Bestseller**`

Set `is_bestseller: true` if found, `is_bestseller: false` if not. Never set null.

### IN_CARTS RULE
Look near the top of the listing (usually within the first 100 lines) for text matching:
- `In 20+ carts` → set `in_carts: 20`
- `In 17 carts` → set `in_carts: 17`
- `In 5 carts` → set `in_carts: 5`

Pattern: `In (\d+)\+? carts?` — extract the number as an integer. The `20+` format means at least 20 — store as `20`. Set `in_carts: null` if no cart signal is found.

### DEMAND SIGNAL RULE
Look for Etsy urgency/scarcity signals near the top of the listing (usually within the first 100 lines). The text format varies by locale and A/B test — capture it raw, do not normalise.

Common patterns (not exhaustive — capture anything matching):
- `In 20+ carts` / `In 20+ baskets`
- `In high demand`
- `Only 3 left and in 5 carts`
- `Low in stock, only 3 left`

Extract using: `re.findall(r'(In \d+\+? (?:carts?|baskets?)|In high demand|Only \d+ left[^.]*|Low in stock[^.]*)', text, re.IGNORECASE)`

Set `demand_signals: []` (empty array) if no signal is found. Never set `null`.

---

### IMAGE RULE
Look for the **first product image** in the listing scrape. It appears near the top of the file
in an `![alt text](URL)` markdown image tag. Use the `il_794xN` size variant when available —
it is the highest-resolution version Firecrawl captures. Example pattern:

```
![alt text](https://i.etsystatic.com/SHOPID/r/il/HASH/IMAGEID/il_794xN.IMAGEID_CODE.jpg)
```

If no image URL is found, set `image_url: null`.

### FAVORITES RULE
Look for a markdown link matching the pattern `[X favorites](https://www.etsy.com/listing/.../favoriters...)` near the top of the listing (usually within the first 200 lines). Extract the number X as an integer. Set to 0 if not found.

### REVIEW DATE RULE
After the `## Reviews for this item` section, review entries appear in this order: star rating line, reviewer name link, **date line** (e.g. `Jun 2, 2026`), then the review text.

- `most_recent_review_date` = the **first** date line found after the reviews header (most recent review)
- `oldest_visible_review_date` = the **last** date line found in the reviews section (oldest visible review)

Convert dates to YYYY-MM-DD format: `Jun 2, 2026` → `2026-06-02`. Set both to null if no reviews section exists.

### is_shirt RULE
`true` for: t-shirt, tee, sweatshirt, hoodie, tank top, long sleeve, crewneck apparel.
`false` for: hats, mugs, glasses, frames, signs, bracelets, cutting boards, socks, pants, etc.

### MOCKUP STYLE RULE
Classify by **visually viewing the image** at the listing's `image_url`. Follow these two steps for each listing:

1. Call **WebFetch** on the `image_url` — this downloads the image and saves it to a local temp file path shown in the result.
2. Call **Read** on that saved file path — this renders the image so you can see it.

Then classify what you see:

| Value | What you see in the image |
|---|---|
| `lifestyle-in-use` | A real person wearing the item in a natural or outdoor setting |
| `flat-lay` | Item laid flat on a surface, photographed from above |
| `ghost-mannequin` | Item on an invisible mannequin — structured shape, no visible person |
| `close-up-detail` | Tight crop on the print area showing font/graphic detail |
| `multi-color-grid` | Multiple color variants shown side by side in a grid |
| `studio-plain` | Item on a plain or white background, no person, no props |
| `unknown` | Image could not be fetched, or does not clearly match any category |

If `image_url` is null, or if WebFetch returns a 404, set to `unknown`.

---

## After extraction — self-check

Before returning the JSON, verify:

1. **Rating check**: does any shirt listing have `rating: 5.0` AND more than 50 reviews?
   That's suspicious — Etsy's recency-weighted averages almost never land exactly on 5.0
   for high-volume listings. Re-read the scrape for that listing.

2. **Color check**: for any listing with a `Colors` dropdown, count the colors in the JSON.
   If you extracted fewer than 5 and the listing is a multi-color apparel item, re-read.

3. **print_method_confirmed check**: count how many entries have `print_method_confirmed: true`.
   If every shirt has `true`, double-check — it's likely that at least some are inferred.

4. **Shirt count**: report at the end how many listings have `is_shirt: true`.
   If < 10% are shirts and the query was shirt-specific, flag it.

5. **Velocity check**: report how many listings have `reviews_per_month` above 20 (high velocity)
   and how many are below 2 (likely legacy). If more than half of all scraped listings are below 2
   reviews/month, flag it — the niche may be declining or oversaturated.

6. **Cross-listing data leakage** (copy-paste between entries — most common AI extraction error):
   - Are any two entries with different `shop_name` values sharing the same `image_url`? → re-read both scrape files and correct.
   - Are any two entries with different `id` values sharing the same `title`? → likely a copy-paste, re-read.
   - For every entry: does the `id` appear inside the `url` string (e.g. `/listing/1724644210/`)? If not, the fields were likely mixed between entries — re-read.

7. **Arithmetic consistency** (recompute; do not trust your own prior calculation):
   - For every entry: verify `estimated_monthly_sales == round(reviews_per_month × 7)`. Flag any mismatch.
   - For every entry with reviews > 0: verify `favorites_per_review == round(favorites_count / reviews, 1)`. Flag any mismatch.
   - For every entry: verify `reviews_per_month <= reviews` (months_active is always ≥ 1, so reviews_per_month can never exceed reviews). Flag any violation.

8. **Date sanity**:
   - For every entry: `oldest_visible_review_date` must be ≤ `most_recent_review_date`. If oldest is more recent, the dates are swapped — correct them.
   - Flag any review date that is in the future (later than today's date). That is a parsing error.

9. **Cross-field consistency**:
   - `is_shirt: true` but `product_type` is not an apparel word (shirt, tee, sweatshirt, hoodie, tank, long sleeve, crewneck) → field mismatch, re-read.
   - `personalization: false` but `personalization_type` is not null → contradiction, set `personalization_type: null`.
   - `personalization: true` but `personalization_type` is null → missing data, re-read scrape and fill in.
   - `print_method_confirmed: true` but `notes` contains the word "inferred" → contradiction, re-read and correct one of the two fields.

10. **Schema completeness**:
    - The fields `id`, `url`, `title`, `price`, `reviews`, `shop_name` must never be null. Flag any entry where they are.
    - `is_bestseller` must never be null (use `false` if badge not found).
    - `demand_signals` must never be null (use `[]` if none found).
    - Any apparel listing (`is_shirt: true`) with `colors: []` is suspicious — re-read the scrape for color options.

---

## Synthesis instruction for market-insights.md

When writing or updating `market-insights.md` after `competitors.json` is built, follow the locked prompt at `scripts/prompts/write-market-insights-prompt.md`. Key rules summarised here:

- Sort listings by `estimated_monthly_sales` descending. The top 3 are **benchmark listings** — name them explicitly with their estimated monthly sales figure.
- Flag any listing with `favorites_per_review` above 5.0 as **high-interest / possible conversion gap** (buyers save but don't purchase — usually a price or trust issue worth noting).
- Flag any listing with `reviews_per_month` below 2 as a **legacy listing** — do not use as a pricing or keyword benchmark.
- Add a section called **Recommended Mockup Style**: report the most frequent `mockup_style` among the top 5 listings by `estimated_monthly_sales`. If there is a tie, list both. If the majority are `unknown`, note that the data is insufficient and recommend checking eRank Listing View manually. This becomes the default for slot 1 (main listing photo) in Phase 3.

**Source tagging — mandatory for every sentence:**
Every claim must end with a backtick-wrapped source tag. The HTML renderer requires backticks — tags without them render as plain text and the color dots do not appear.

| Write it as | Meaning |
|---|---|
| `` `[our data]` `` | Directly observed in competitors.json or keywords.md |
| `` `[inferred]` `` | Logical conclusion drawn from our data |
| `` `[market knowledge]` `` | General POD/Etsy knowledge from AI training data — not verified for this niche |

Never use hybrid tags (`[our data + inferred]`). Split into two separately tagged sentences instead.

---

## Niche Verdict (write this first, before the JSON)

After building competitors.json, write the Niche Verdict block and add it to the **top of `market-insights.md`** before any other content. Fill in every field — do not leave any blank.

```markdown
## Niche Verdict [REQUIRED]

**Demand signal:** [High / Medium / Low]
Basis: [one sentence — reference estimated_monthly_sales of top 3 listings by that field,
whether Bestseller badges were found (is_bestseller count), and in_carts signals found.
Then apply trend adjustment from keywords.md: Rising → upgrade one level, Declining →
downgrade one level, Seasonal → note peak month, Unknown → leave unadjusted and note the gap.]

**Competition barrier:** [High / Medium / Low]
Basis: [one sentence — what proportion of scraped listings have reviews_per_month above 10?
Majority = High barrier. Minority = Low barrier.]

**15/month check:** [Pass / Fail]
Basis: [do at least 3 of the top 5 listings by estimated_monthly_sales show 15+
estimated monthly sales? Pass = yes. Fail = no. Name the 5 listings and their values.]

**Recommendation:** [Enter / Enter with sub-niche pivot / Do not enter]
Reasoning: [one sentence combining all three signals above]

**If sub-niche pivot recommended:** [specific angle — e.g. a specific occupation, design
format, or product type that has fewer dominant competitors in the scraped data]

**Confidence:** [High = verdict backed entirely by scraped data |
Medium = partly inferred or trend unknown | Low = limited data, proceed cautiously]
```

---

## Output format

Return only the JSON array — no markdown wrapper, no explanation before or after.
Save to `projects/<niche>/01-research/competitors.json`.
