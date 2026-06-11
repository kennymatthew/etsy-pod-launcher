# Listing Copy Prompt
# Produces: 04-listing/titles.md, 04-listing/tags.md, 04-listing/descriptions.md
# Run AFTER: Phase 1 (competitors.json + keywords.md complete) and Phase 2.0 (blank locked)
# Do NOT run until the Niche Verdict says Enter or Enter with sub-niche pivot.

---

Read the following files before writing anything:
- `01-research/competitors.json` — extract top 5 listings by `reviews` (EMS/RPM fields are always null); note their exact titles and key_phrases
- `01-research/keywords.md` — use the keywords with highest search volume as primary targets; note any with Trend: Rising as priority
- `01-research/market-insights.md` — read the Niche Verdict, Price Range, and Personalization Types sections
- `02-design/brief.md` — read the Lock block (blank, blueprint, print provider, list price) and the design direction

Then produce the three output files below. Save each one exactly as specified.

---

## Output 1 — `04-listing/titles.md`

Write **3 title options**. Each must:
- Be exactly 140 characters (count precisely — use the format `[NNN chars]` after each title)
- Start with the highest search-volume keyword from keywords.md in the first 30 characters
- Use comma-separated keyword stacking (copy the pattern from top competitors in competitors.json)
- Be human-readable — not a keyword soup
- Include the personalization type if this is a personalized listing (e.g. "Custom Name", "Personalized")

Format:
```
## Title Options

### Option A [NNN chars]
[title text]

### Option B [NNN chars]
[title text]

### Option C [NNN chars]
[title text]

## Recommended: Option [X]
Reason: [one sentence — why this title leads with the right keyword and best matches competitor patterns]
```

---

## Output 2 — `04-listing/tags.md`

Write exactly **13 tags**. Each tag must:
- Be 20 characters or fewer (count precisely — flag any that exceed 20)
- Be a multi-word phrase, not a single word
- Not duplicate any word unnecessarily — cover different search angles
- Be ordered by estimated search volume descending (use keywords.md as the guide; fill gaps with phrases from top competitor key_phrases)

Format:
```
## Tags (13)

| # | Tag | Chars | Source |
|---|---|---|---|
| 1 | [tag] | [N] | keywords.md / competitor key_phrases / inferred |
| 2 | ... | | |
...
| 13 | ... | | |

## Tag strategy notes
[2-3 sentences: which angles are covered, which competitor patterns are mirrored, any gaps]
```

---

## Output 3 — `04-listing/descriptions.md`

Write **one full Etsy description** following this exact structure. Do not reorder sections.

```
[Emotional hook — 1-2 lines. What this item means to the buyer, not what it is.]

✨ [PRODUCT NAME] Features:
• [Feature 1]
• [Feature 2]
• [Feature 3]
• [Feature 4]

📦 How to Order:
1. [Step 1 — e.g. choose size and color]
2. [Step 2 — e.g. for personalized: enter name in the box at checkout]
3. [Step 3 — e.g. add to cart and check out]

📏 Sizing:
[Brief guidance — link to size chart slot 8 in listing photos; note if unisex sizing runs large]

👕 Product Details:
• Material: [blank name + fabric content — from brief.md Lock block]
• Print method: [DTG / embroidery / sublimation — from brief.md]
• Print location: [front chest / back / etc.]
• Produced and ships from: [print provider country from fetch-pp-costs.py output]
• Production time: 2–5 business days

🎁 Perfect For:
• [Occasion 1]
• [Occasion 2]
• [Occasion 3]

🚚 Shipping & Production:
• Production: 2–5 business days
• Standard shipping: 3–7 business days (US)
• Express options available at checkout

🧺 Care Instructions:
• Machine wash cold, inside out
• Tumble dry low
• Do not iron on print

Questions? Message us — we respond within 24 hours.
```

Rules:
- Use the top 3 keywords from keywords.md naturally in the first 100 words (do not force them)
- Keep sentences short — mobile buyers skim
- Do not use the word "unique" or "quality" — they are banned Etsy SEO filler
- Personalization instructions must exactly match what the buyer needs to do at checkout (check market-insights.md Personalization Types for the correct flow)

---

## Self-check before saving

1. Count every title character — no title may exceed 140
2. Count every tag character — no tag may exceed 20
3. Verify tag 1 matches the highest-volume keyword in keywords.md
4. Confirm the description opens with emotion, not product features
5. Confirm "unique" and "quality" do not appear in the description
6. Confirm the product details section matches the blank and print method in brief.md

Only save files after all 6 checks pass. Flag any failure explicitly before saving.
