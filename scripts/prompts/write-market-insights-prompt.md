# Market Insights Prompt
# Produces: 01-research/market-insights.md
# Run AFTER: competitors.json is complete and self-check passes
# Do NOT run until: extract-competitors.py reports 0 warnings

---

Read the following files before writing anything:
- `01-research/competitors.json` — full dataset; sort by `estimated_monthly_sales` descending before analysis
- `01-research/keywords.md` — trend direction for Niche Verdict demand adjustment (if file exists)

---

## Required sections (in this order)

1. Niche Verdict
2. Price Range for Shirts
3. Most Common Personalization Types
4. Garment Blanks Mentioned
5. Print Methods
6. Color Strategy
7. Demand Signals Summary
8. Listings to Watch (favorites_per_review > 5.0)
9. Legacy Listings (reviews_per_month < 2)
10. Recommended Mockup Style
11. Niche Trend Keywords (stub table — fill in after Phase 1.4 eRank)
12. Appendix — Data Quality Notes

Note: Do NOT write a "Top Design Patterns" prose section. Design patterns are visualised automatically from patterns-config.json and injected into the HTML report. Writing prose here creates duplication.

---

## Source labeling — MANDATORY

Every sentence that makes a factual or analytical claim MUST end with a backtick-wrapped source tag.
The HTML renderer converts backtick-wrapped tags to color-coded dots. Without backticks, labels are invisible.

| Tag | Write it as | Meaning |
|---|---|---|
| our data | `` `[our data]` `` | Directly observed in competitors.json or keywords.md |
| inferred | `` `[inferred]` `` | Logical conclusion drawn FROM our data — not directly observed |
| market knowledge | `` `[market knowledge]` `` | General POD/Etsy knowledge from AI training data — not verified for this niche |

### Critical rule — no self-calculated counts

**NEVER recalculate a number from competitors.json yourself.** AI arithmetic on raw JSON is unreliable and has caused hallucinated claims tagged `[our data]` in past audits.

- Run `generate-niche-verdict.py --niche <niche>` first. It outputs pre-computed blocks for: Niche Verdict, Personalization Types, Price Table, Print Methods, Blank Distribution, FPR Stats, RPM Percentiles, Top 10 Reference.
- Paste each pre-computed block verbatim into the matching section. Do not change any number in a pre-computed block.
- `[FILL IN]` placeholder sentences are the only lines you write yourself. These are interpretation only — they must be tagged `[inferred]` or `[market knowledge]`, **never `[our data]`**.

If a section has no pre-computed block and requires a count, write `[FILL IN — run generate-niche-verdict.py to get this number]` and do not guess.

---

### Rules

1. **Every sentence gets a tag** — not just section headers or paragraph endings. Each individual claim on its own line or in its own sentence must be tagged.

2. **Backticks are required** — write `` `[our data]` `` not `[our data]`. Without backticks the tag renders as plain text and the color dot does not appear.

3. **Never use hybrid tags** — do not write `[our data + inferred]` or `[our data / inferred]`. These are ambiguous. Instead, split the claim into two sentences: one tagged `[our data]` for the factual part, and one tagged `[inferred]` for the conclusion.

   Wrong:
   > "30/51 listings reference Comfort Colors, which suggests strong buyer preference for the garment-dyed aesthetic. `[our data + market knowledge]`"

   Correct:
   > "30/51 listings reference Comfort Colors. `[our data]` Comfort Colors garment-dyed blanks are broadly favored in POD apparel niches for their vintage aesthetic — this niche confirms that pattern. `[market knowledge]`"

4. **Bullet list items need tags** — if each bullet makes a distinct claim, each bullet gets its own tag.

5. **Table cells need tags** — the Notes column of every table must include a tag on each non-trivial claim. Pure counts (e.g. "32") do not need tags; interpretation (e.g. "dominant method") does.

6. **Do not tag section headings** — H2 and H3 headings are navigational, not claims.

### What counts as each tag

Use `[our data]` when the claim is:
- A count, percentage, or measurement calculated from competitors.json or keywords.md
- A specific listing ID, EMS, RPM, price, review count, favorites count, or blank name from the data
- A ranking or ordering derived from the data

Use `[inferred]` when the claim is:
- A conclusion or implication drawn from data patterns (e.g. "this suggests...", "likely because...", "indicates...")
- A competitive judgment drawn from the numbers (e.g. "barrier to entry is high because...")
- A prediction about buyer behavior based on what the data shows

Use `[market knowledge]` when the claim is:
- General Etsy or POD knowledge not derivable from this dataset (e.g. how in-carts display works, DTG vs embroidery seller behavior, typical mockup conventions)
- A recommendation based on POD norms rather than what the scraped data shows
- Any statement that would be true regardless of what competitors.json contains

---

## Confidence column (for opportunity/gap tables)

Any table listing sub-niche opportunities or listings to watch must include a Confidence column:
- ✅ High — backed by `[our data]`
- ⚠️ Medium — `[inferred]` or partially backed
- ❌ Low — primarily `[market knowledge]`, demand unverified

---

## Section 7 — Demand Signals Summary (interpretation only — tables are auto-computed)

This section must follow the exact structure below. Compute all counts from `competitors.json`.

The three tables in this section (Etsy Demand Labels, In-Carts Heat, Demand by Pattern Segment) are **auto-computed and injected by `generate-competitor-report.py`** — do NOT write them manually.

Your job is to write only the four `[FILL IN]` interpretation lines that the script leaves as placeholders:

1. **Verdict** (after the `## 6.` heading) — one sentence on overall demand strength. `[our data]`
2. **Badge commentary** (after the Etsy Demand Labels table) — 1–2 sentences on what the zero rows mean for this niche. `[inferred]`
3. **Carts commentary** (after the In-Carts Heat table) — already pre-filled with the % at cap; only replace if you have something more useful to say.
4. **Pattern commentary** (after the Demand by Pattern Segment table) — 2–3 sentences on signal-to-competition ratio for new entrants. `[inferred]`

Run `generate-competitor-report.py --niche <niche>` first to populate the tables, then open market-insights.md and fill in only the `[FILL IN]` lines.

---

## Self-check before saving

1. Open market-insights.md and search for `[our data]` without a backtick before it — fix any found
2. Search for `[inferred]` without a backtick before it — fix any found
3. Search for `[market knowledge]` without a backtick before it — fix any found
4. Confirm no sentence in sections 1–12 is untagged (headers and listing ID lines are exempt)
5. Confirm no hybrid tags exist (`[our data + inferred]`, `[our data / inferred]`, etc.)
6. Confirm the Niche Verdict section is at the top and every field is filled (no `[FILL IN]` remaining)
7. **For every sentence tagged `[our data]`: confirm it came verbatim from a generate-niche-verdict.py output block — not a number you calculated yourself.** Any self-calculated count must be `[inferred]`, not `[our data]`.

Only save the file after all 6 checks pass. Flag any failure explicitly before saving.

---

## After saving

Run:
```bash
python3 scripts/generate-competitor-report.py --niche your-niche-name
```

Open the HTML, click "Show labels" in the legend, and visually verify that colored dots appear on every claim throughout the Market Insights tab. If a section has no dots, a tag is missing or missing backticks.
