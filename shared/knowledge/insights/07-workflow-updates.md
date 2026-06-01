# WORKFLOW.md Update Recommendations
Source: Derived from insight files 01–05 (Alek) and 02c, 03c, 05c (We Scale)

These are specific, sourced additions to WORKFLOW.md — section by section. No invented content.

---

## Add to Phase 1 (Research)

- **Add sub-niche slogan validation as step 1.5.** After market-insights.md is generated (1.3), add a step: search the specific slogan or phrase your design will use on Etsy. Confirm that multiple shops each with 3,000+ reviews are all selling that same saying styled differently. Document the finding in market-insights.md. If no shops with that volume use the phrase, either drill deeper to find a phrase with proven demand, or flag it as untested. This is described as "the real sauce" of Alek's entire course — the intersection of low competition, proven demand, and copyright safety signal.
  Source: 02-design-system.md

- **Add cross-niche design direction to the research output.** In the market insights analysis step (1.3), instruct the AI to also identify what the target niche audience also cares about beyond the primary niche (e.g., "nurses + coffee," "golfers + humor about bad shots"). Document these as "[Niche] x [complementary interest]" pairs in market-insights.md — they become design direction prompts in Phase 2.
  Source: 02c-design-v2-wescale.md

- **Add seasonal calendar check as step 1.6.** Before finalizing the niche, check what seasonal or holiday events are coming up in the next 4–8 weeks. Indexing takes 2–3 weeks and fulfillment adds another week, so listings must be live at least 4 weeks before the target date. If a seasonal angle applies to the niche, flag it now so the design and upload timeline accounts for it.
  Source: 04-marketing.md (Alek)

---

## Add to Phase 2 (Design)

- **Add two-version export requirement as a named deliverable in step 2.2.** The design must be exported as two separate PNG files: (1) black design for white and ivory shirts only, (2) a slightly off-white version (not pure white — using approximately #FBB1B or similar to trigger double ink layer) for all other colorways including all dark shirts. Applying the wrong version to dark shirts produces muddy prints. Label the exports clearly (e.g., `/02-design/assets/design-name-black.png` and `design-name-white.png`).
  Source: 02-design-system.md (Alek)

- **Add design principle checklist to the design brief.** The brief (2.1) should confirm the design passes these checks before production begins: (1) readable from 10 feet away, (2) 1–3 colors maximum, (3) negative space used — shirt fabric is part of the design, not filled with ink, (4) no color gradients, (5) no block-of-ink areas, (6) one clear message. Both courses independently list these as the difference between designs that sell and designs that do not.
  Source: 02-design-system.md (Alek), 02c-design-v2-wescale.md (We Scale)

---

## Add to Phase 3 (Printify Setup)

- **Add product template note to step 3.1.** The first product created manually is the master template for all future listings. Finalize all variants, pricing, shipping profile, and the "show all variants as available for purchase" toggle on this one product before creating any others. Every subsequent product should be created via Printify's "Duplicate" button, then only the design file is swapped and settings are spot-checked. This compresses repeat product creation to approximately 1 minute per product.
  Source: 01-niche-research.md (Alek), 03c-product-launch-v2-wescale.md (We Scale)

- **Add Printify best-selling variants data to step 3.5 (color selection).** When selecting which 12 colors to keep, reference the Printify Insights Dashboard best-selling variants table filtered by product model (e.g., Comfort Colors 1717) alongside the competitor data from market-insights.md. Pick the top 6 colors by actual Printify sales volume, then add 6 more from competitor reference or personal preference. This uses direct sales data rather than relying solely on colors mentioned in scraped competitor text.
  Source: 01-niche-research.md (Alek)

- **Add the design-per-color variant assignment step.** After variants are set, assign the correct design version to the correct color group: black design PNG to white and ivory variants only; off-white design PNG to all remaining (darker) color variants. This requires editing each color group in Printify's canvas editor. Not doing this produces visible print quality issues on dark shirts.
  Source: 02-design-system.md (Alek), 03c-product-launch-v2-wescale.md (We Scale)

---

## Add to Phase 4 (Listing)

- **Add 30-character rule to step 4.1 (title).** The first ~30 characters of the Etsy title are what shows in search result truncation — Etsy places emphasis on this portion. The first 30 characters should be a plain-English human-readable product description (e.g., "Tis the Season Sweatshirt"). The remaining characters are keyword phrases for SEO, pulled and shuffled from top-selling competitors. Note the tension: this may conflict with putting the highest-volume keyword first. Decide per listing which takes priority in the opening characters.
  Source: 03-listing-seo.md (Alek)

- **Add upsell links section to description template (step 4.3).** After the specs/care section, add links to other listings selling the same design on different product types (e.g., same graphic on a sweatshirt, hoodie, or tank top). Also add a closing line directing buyers back up to the photos section at the top of the page — this prevents them from scrolling to Etsy's competing listings panel at the bottom, which appears below the description.
  Source: 03-listing-seo.md (Alek)

- **Add sale pricing decision as a named step in 4.4 (pricing).** The current formula (Printify cost × 5 = list price, ÷ 2 = sell price) implements the permanent 50% off strategy correctly. Make this decision explicit with a note: this list price must be set before publishing, not after. If a temporary sale structure is preferred instead (e.g., 20% off for 60 days), the list price would be cost × 2.5 ÷ 0.8. The two structures look different to buyers long-term. Commit to one before the first listing goes live.
  Source: 01-niche-research.md (Alek), 06-gap-analysis.md

- **Resolve the shipping contradiction as a flagged decision in 4.4 Gotchas.** The current Gotcha says "free shipping (built into price) ranks better in Etsy search." Alek's course takes the opposite position: charge shipping separately ($5.99 first item, $1.99 additional), enable the Etsy Free Shipping Guarantee at the $35 order threshold for the search ranking benefit, and use this to incentivize multi-item orders. Both approaches have tradeoffs. Add a decision note documenting both and force a deliberate choice before publishing.
  Source: 01-niche-research.md (Alek), 06-gap-analysis.md

---

## Add to Phase 6 (Go Live / Post-launch)

- **Specify info card requirements and fixed slot positions in step 6.2.** Two info cards are required for every apparel listing — not optional: (1) a color chart showing all offered color variants with names, and (2) a sizing guide with measurements. Place them in consistent numbered image slots across all listings (e.g., slot 7 = color chart, slot 8 = sizing guide). Consistent slot placement means bulk-updating these later takes seconds across the entire catalog instead of per-listing editing.
  Source: 03-listing-seo.md (Alek)

- **Add listing video as a recommended step after 6.2.** Etsy's own data (at time of Alek's recording) shows listings with videos convert at 2× the rate of listings without, and only ~28% of listings use videos. Minimum viable option: a reusable mockup slideshow or stock sizing guide video applied across all listings in a batch. If time is short, a single reusable video applied to all listings is better than skipping video entirely. Build this once alongside the first batch.
  Source: 03-listing-seo.md (Alek)

- **Add Etsy email automation setup as a one-time step before or alongside 6.3 (launch sale).** Configure all three Etsy automations in Etsy Marketing → Sales & Discounts before the first sale occurs: (1) abandoned cart offer (~45–50% off), (2) favorited item offer (~55% off), (3) thank you / repeat purchase offer (~55–60% off). Set coupon percentages to match the daily sale discount to prevent stacking. These run permanently with no ongoing maintenance.
  Source: 05-scaling.md (Alek)

- **Add daily sale scheduling as an operational task in 6.3.** Etsy does not allow automating the daily 50% off sale — it must be manually created each time. The workaround is to schedule sales one to four weeks in advance in Etsy → Marketing → Sales & Discounts → "Run a Sale" (set start and end date to the same date). Schedule at least one week ahead at all times. Failure to maintain the daily sale breaks the permanent-sale strategy.
  Source: 05-scaling.md (Alek)

---

## New section to add: Post-launch Diagnostics

Add this as a new subsection within Phase 6 (or as a standalone Phase 7 Troubleshooting section).

---

### Diagnostic Funnel — If You're Not Getting Sales

Work through these stages in order. Do not skip ahead — each stage builds on the previous.

```
VIEWS → VISITS → INTERACTIONS → CONVERSIONS
```

**Stage 1 — No Views**
Your listings are not appearing in Etsy search results.
- Cause: SEO setup was skipped or done incorrectly.
- Fix: Go back to Phase 4. Review title (first 30 characters human-readable, keyword tail follows), tags (2–3 tags with highest recommendation score applied to all listings, remaining slots filled from top competitor tags), and description (keywords at top). Verify the listing has been indexed — new listings take 2–3 weeks to appear in competitive searches.

**Stage 2 — Views but No Visits (no clicks from search)**
Buyers see your listing in search but do not click through.
- Cause: Almost always an image problem — main mockup, thumbnail crop, or design clarity.
- Fix: Change the main listing image. Test a different mockup. Tighten the thumbnail crop in the Etsy listing editor (Listings → open listing → edit images → Transform → square crop → zoom in). Check that the design is clearly readable at thumbnail size.

**Stage 3 — Visits but No Interactions (no favorites, no add-to-cart)**
Buyers visit the listing page but do not engage.
- Cause: One of three issues — design quality is low, info cards (color chart, sizing guide) are missing or poor quality, or the price is too high relative to competitors.
- Fix: Check that the color chart and sizing guide are in fixed image slots. Review the design against the principles checklist (readable, simple, negative space, 1–3 colors). Run the Listing View calculator to verify your price delivers margin without being uncompetitive.

**Stage 4 — Interactions but No Conversions (favorites/carts but no purchases)**
Buyers engage with the listing but do not complete the purchase.
- Cause: This stage is uncommon — once interactions exist, sales usually follow. When it occurs, check trust signals.
- Fix: Do you have any bad reviews that are visible? Does the listing have a video? Does the shop overall look complete and trustworthy? Review which color and size variants you are offering — missing popular variants can block purchase. Consider whether the daily sale is currently running (a sale creates urgency via countdown timers).

Source: 05-scaling.md (Alek)

---

## New section to add: Scaling Winners

Add this as a new Phase 7 (Scaling) after Phase 6.

---

### Phase 7 — Scaling Winners

**Goal:** Multiply what the market tells you is working, without guessing.

#### 7.1 The 5-variation multiplier
When any listing makes its first sale, immediately create 5 more variations of that same design before doing anything else:
- Use different mockup styles as the main listing image (lifestyle, flat lay, close-up, different color background)
- Use different colorways as the featured thumbnail
- Publish each as a separate listing, not a variant of the existing one

This gives 6 total listings targeting the same validated niche concept, each with a unique visual entry point in search. Etsy's algorithm treats a shop conversion as a signal to promote that shop's other listings — variations immediately benefit from this.

"Any product that has sold is a winning product. Don't waste time guessing what's going to work when the market tells you something. Listen and then scale immediately."
Source: 05-scaling.md (Alek)

#### 7.2 Cross-niche translation
Once a design template converts in one niche, duplicate the design template and swap the niche-specific element:
- Nurse profession design → duplicate → swap to "accounting" or "teaching"
- A holiday saying template → apply to a different holiday
- A humor format ("I'd rather be [activity]") → swap the activity to a different niche

This compounds proven design formats into catalog volume across niches without rebuilding from scratch.
Source: 05-scaling.md (Alek)

#### 7.3 Iterate at the concept level (not execution)
When a design wins, do not make minor execution tweaks (change a font, adjust a color, remove a graphic element) — these address the same micro-audience. Instead, iterate at the concept level: different joke with the same format, different emotional angle, different slogan with the same visual structure. Concept-level iterations open new audience segments while carrying forward the proven appeal signals.

50/50 rule: half of new designs should be concept-level iterations of proven winners; half should come from fresh research. Research never fully stops.
Source: 05c-scaling-v2-wescale.md (We Scale)

#### 7.4 Daily sale scheduling maintenance
Maintain at least one week of scheduled daily 50% off sales at all times. Set each sale with start and end date on the same day (expires at midnight). Schedule them out weekly or monthly in advance in Etsy → Marketing → Sales & Discounts. Without the daily sale running, the listing no longer shows the sale badge and countdown timer to buyers — this breaks the standard Etsy POD conversion pattern.
Source: 05-scaling.md (Alek)

#### 7.5 Listing volume targets
- **Daily target:** 20 new listings per day, 5 days per week (manageable quality + volume balance)
- **Consistency beats intensity:** 5–10 quality listings per week compounds significantly over time for part-time sellers
- **1,000-listing milestone:** At ~1,000 quality listings following the research and SEO framework, expect $1,000–$2,000/month profit as a rough benchmark (not a guarantee)
- **Part-time approach:** Batch tasks by day (design-only day, upload-only day, research-only day) rather than doing all steps daily. Time blocking is the constraint — optimization is the lever.

Source: 05-scaling.md (Alek), 02c-design-v2-wescale.md (We Scale)

#### 7.6 P&L tracking (weekly minimum)
Run a profit and loss statement weekly: revenue minus cost of goods (Printify), Etsy fees, ad spend (if running), and software subscriptions. Track cost of goods as a percentage of revenue. Track software subscriptions as a percentage of revenue — anything above 3% is a red flag. "What gets measured gets grown." Overhead creep is silent and compounds — audit every subscription monthly.
Source: 05c-scaling-v2-wescale.md (We Scale)
