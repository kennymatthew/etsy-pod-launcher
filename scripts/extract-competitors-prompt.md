# Competitor Extraction Prompt
# Usage: paste this into Claude when building competitors.json from scraped listing files.

---

Read all `etsy-listing-*.md` files listed in `scrapes/manifest.json` and produce a
`competitors.json` array. Each entry must follow the schema below exactly.

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
  "key_phrases":          "array of strings — 3-5 exact keyword phrases from the title",
  "colors":               "array of strings — see COLOR RULE below",
  "shop_name":            "string",
  "notes":                "string — notable selling points: badges, Star Seller, ships from, etc.",
  "image_url":            "string or null — first product image URL (see IMAGE RULE below)",
  "demand_signals":       "array of strings — see DEMAND SIGNAL RULE below"
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

### is_shirt RULE
`true` for: t-shirt, tee, sweatshirt, hoodie, tank top, long sleeve, crewneck apparel.
`false` for: hats, mugs, glasses, frames, signs, bracelets, cutting boards, socks, pants, etc.

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

---

## Output format

Return only the JSON array — no markdown wrapper, no explanation before or after.
Save to `projects/<niche>/01-research/competitors.json`.
