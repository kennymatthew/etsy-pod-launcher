# Modules 5+6 — Mockups & Listing Optimization
Source: Alek (@alekSheffy), lines 1411–1974

---

## Mockup Strategy

### What a mockup is
"A mockup is the actual image that displays your product design" — a blank product image with your design placed on it to look like a real photograph. **Evergreen**

### Core principle
"The mock up image is just as important as the design you make." "If you don't get the mockup right, your product is never going to sell. And I mean that — it'll absolutely never sell if you use bad mockups." **Evergreen**

### How to find high-converting mockups (research process)
1. Run a search on Etsy for the product you're selling (include niche keywords for more specific results)
2. Use Listing View's Outlier Score badge to identify which listings are selling far above average — "the outlier score tells you how well a listing is performing relative to all of the other listings within the same shop"
3. Note the mockups those high-outlier listings use, then search Etsy for that exact mockup (e.g. "comfort colors moss mockup") and buy it
4. Also use Listing View's database search: search broadly (e.g. "comfort colors mockup"), switch to visual browse mode, sort by total sales or monthly sales **Check** (Listing View features may evolve)

### Mockup criteria (4 rules)
1. **Proven to sell** — "Don't pick mockups based on what you personally like. Use data and research to find mockups that are already proven to convert."
2. **Match Etsy's handmade vibe** — "You'll never find best selling listings using something like a PlaceIt mockup." Explicitly warns against PlaceIt: "absolutely no best selling listings on Etsy use mockups from PlaceIt." **Check** (may still hold but worth verifying)
3. **Bright, centered and not cluttered** — "Generally it's going to be just the product and a human or a couple accessory items around the product itself."
4. **Match the vibe** — "Your design and mockup combination has to create a compelling listing that converts shoppers into buyers."

### How many mockups to make per design
"I always recommend making a lot of mockups for each design so that you can pick the best one for the main listing image." The goal is to batch all designs × all mockups at once, then pick the best combination per design. **Evergreen**

### Automation methods (3 options)
| Method | Cost | Notes |
|---|---|---|
| Figma | Free | Fastest overall; uses component/variant system; opacity trick: set design layer to 90–95% to blend texture |
| Photoshop + script | ~$20/month (Adobe) | More control; can warp designs to product (e.g. mugs); blend-if tool for texture; mask tool to hide design behind hair etc.; script auto-generates all design × mockup combos |
| Dynamic Mockups | Paid subscription | Still requires PSD setup; less recommended than Figma or Photoshop |

### Figma automation — key steps
- Drag design into Figma → click "create component" (turns outline purple)
- Rename the layer "designs go here"
- Hold Option + drag to make a variant/copy of the component
- Drag mockup image into Figma behind the variant frame
- Size the purple frame to match the product's print area (so new designs always fit)
- Group (Command+G) mockup + frame together
- To update all mockups at once: swap the design inside the main "designs go here" component — all variants update instantly
- Pro tip: set the design variant's opacity to 90–95% to let mockup texture show through slightly **Evergreen**

### Photoshop script setup — key steps
- Drag mockup + design into Photoshop; create a Smart Object with a solid color fill; scale to print area; save as PSD in the "mockups" folder
- Optional: use "Blend If" panel (hold Option, split handles) to blend design into shirt texture; add masks to hide design behind elements like hair
- Three folders required: `/mockups/` (PSDs), `/designs/` (design files), `/exports/` (output)
- Install script: File → Scripts → run the mockup script; point to folders; hit Start
- "It took eight minutes to complete the job" for a full batch
- ⚠️ Script file is part of course downloadable materials — not publicly available

### Recommendation
"I typically recommend going with the Figma approach at first and then scaling into using Photoshop later on. Once you have an established system and proven mockups, and maybe you're making some sales to cover that extra $20 subscription each month." **Evergreen**

---

## High-Converting Title Formula

### Two purposes of the title
1. Tell the **customer** what the product is (first ~30 characters — visible on search results page)
2. Tell **Etsy** who the product is for (remaining characters = keyword-rich tail)

### The 30-character rule
"Etsy puts a ton of emphasis on that portion of the title. This is typically going to be the first 30 characters. That's because it's what's visible from the first page of search results." **Check** (Etsy UI may change how characters are truncated)

Example given: "Tis the Season sweatshirt" as the human-friendly front, followed by additional keywords.
Another example: "Comfort Colors 1717 size chart" — "you can't get more clear than that."

### Formula
```
[Human-readable product description — ~30 chars] + [Additional keyword phrases for SEO]
```

### How to build titles (process)
1. Pull up several top-selling listings in your niche in Listing View
2. Copy the keywords they use in their titles
3. Paste into Pre-List, which "shuffles these keywords around and create completely unique titles for all of the products that we're uploading"
4. "Create new combinations of these keywords to create completely original and new titles" — do not copy any one listing verbatim **Evergreen**

### Key rule
"Etsy is constantly mentioning that they want the titles to be as human friendly as possible." First 30 characters = human. Remainder = SEO. **Check** (Etsy's stated guidance may evolve)

---

## Tag Strategy

### Why tags matter now
"Etsy has publicly stated that tags are going to become more important than the titles in your listings in coming months." Tags limited to **20 characters** each. **Check** (Etsy's algorithm weighting changes over time)

### Process for picking tags
1. Open several top-selling listings in your niche
2. In Listing View, expand the stats tray (or open the full details page) — it shows all tags with a **recommendation score** (green bar = low competition, high search volume)
3. Copy tags with the highest recommendation scores — these have "high volume but low competition and also factors in a few other things like conversion rates and average prices"
4. Also copy tags from multiple best-selling listings to fill remaining slots
5. Use **adjacent keywords** (synonyms and related terms) — e.g. for a wedding shirt: "engagement," "bridal shower," "fiancé," "bride to be"; for hiking: "camping," "adventure," "nature," "sports," "travel"

### Adjacent keyword rule
"You want to broaden the search that your product will show up for. You don't want to go way too broad, to the point where you lose the actual meaning for the product."

### Competition rule
"Just because a tag has a lot of competition does not mean that you have to avoid it entirely. Etsy is always pushing new listings, even on the first page of search results for super broad, highly competitive keywords." Example: "Christmas shirt" — 3 million listings, yet Etsy was pushing 28 new listings on page 1 created within the last 60 days. **Evergreen** (principle; specific numbers may change)

### Tag slot strategy (live demo)
- First: apply the 3 low-competition keywords found across multiple best-sellers to all listings
- Then: fill remaining 9 slots by copying full tag sets from individual top-performing listings, rotating the source listing so there's variety across your batch
- ⚠️ He mentions having 13 total tag slots implied (3 low-comp + 9 filled from best-sellers = 12; Etsy allows 13) — the exact count should be verified against current Etsy limits

---

## Description Structure

### Core philosophy
"Use a template titled description so that I can reuse it on all of my listings all at once. This is because if we ever need to change any details about our description, I want to be able to change it once and have it updated across all of our listings."

### Template outline (in order)
1. **Keywords section** — "Including a few keywords at the very top of your description. This is going to help that product rank in search a little bit better over time." Can reuse the title or paste the tags here. **Check** (Etsy's weighting of description keywords may change)
2. **Production and shipping times** — how long to expect for delivery
3. **How to order instructions** — especially relevant for personalized/custom listings
4. **Specifications** — how the product fits, materials, care instructions
5. **Upsell links** — links to other products (e.g. same design on sweatshirt, hoodie, tank top): "leave a link in the product description to those other custom listings"

### Pro tip — get customers back to the top
"I like to mention that any necessary details are given in the photos section of the listing. This gives customers back up to the top of the page where they're looking at your product mockups, where they'll be able to buy." The goal: prevent them from scrolling to the bottom where Etsy shows competing listings. **Evergreen**

### What changes per listing
"The only thing that we need to change for each product is the keyword section at the very top of our description." Everything else is identical across all listings. **Evergreen**

---

## Listing Photos & Videos

### Info cards — required types
- **One info card per variation** — e.g. a color chart showing all color options + names, and a sizing guide with measurements. "You're going to get a ton of customer questions if you don't have good info cards for the variant options."
- Keep info cards in the **same image slots** across all listings — "If they're always saved in slots two and three, for example, we can always use a bulk editor to update the second and third image slots across all of our listings."
- His example setup: 6 mockup images in slots 1–6; color chart in slot 7; sizing guide in slot 8 **Evergreen** (principle; slot numbers are his specific example)

### Additional optional info cards
- Processing/shipping times
- Font options or ordering instructions (for custom listings)
- Social proof / customer reviews

### Where to get info cards
- Buy on Etsy (he maintains a live table of recommended shops in course materials)
- Build in Kittl from scratch
- ⚠️ Specific shop links are in course downloadable materials — not extractable from transcript

### Video
- "On average, listings with videos convert twice as often as listings without videos" (Etsy's own stat)
- "Only around 28% of listings use videos" — opportunity to stand out **Check** (stat is from Etsy at time of recording)

### Video options (in order of recommendation)
1. **Mockup slideshow** — cycle through the same design on multiple mockups, end with shop logo. "Takes a while to make."
2. **AI-animated mockup** — use Google Gemini (free), upload mockup, prompt it to animate slightly (e.g. "make a slow motion video of this person adjusting their sweater"). "Definitely has a little bit of AI vibes to it." **Check** (Gemini capabilities may have changed)
3. **Reusable video across all listings** — stock footage of shirts being printed/created + your logo, or a live sizing guide video showing fit and measurements. "Probably a little bit less effective, but definitely more time effective."

### Time priority rule
"If you're limited on time, I would definitely go with something like a video sizing chart that you can reuse across all of your listings, or spend your time creating more listings instead of spending a bunch of time creating unique videos for every single listing. Your time is better spent creating more additional listings for your shop than it is tweaking the little details about each specific listing." **Evergreen**

---

## Bulk Editing Tips

### Tools for bulk editing
- **Pre-List** — import listings, bulk overwrite title/description/tags using template + shuffle; use find-and-replace to fix formatting (e.g. remove asterisks for bold, replace dashes with bullet characters)
- **Listing View Bulk Editor** — connect shop, select all new listings, edit each section (title, description, tags, photos, variations, shipping, sections) across all listings at once **Check** (tool features may change)

### Description workflow in Listing View
1. Paste template into overwrite mode → updates all listings
2. Find-and-replace `*` with nothing (remove bold formatting — "we're not allowed to use bold characters in the description")
3. Find-and-replace `- ` with bullet character `•`

### Photo management workflow
1. Drag mockup images directly onto individual listing photo trays (do NOT use the apply-to-all option for mockups, since each listing has a unique design)
2. Use delete mode to remove Printify's auto-generated mockups from slots 7–12 (or whichever slots)
3. Add info cards in bulk using overwrite for specific slots (e.g. slot 7 = color chart, slot 8 = sizing guide) — applies across all listings instantly
4. Manually swap the first/featured mockup slot per listing so each listing leads with its best image

### Shop sections
- Etsy allows up to **12 shop sections** — he uses 9, based on high-level niches from his Niche Ideas document
- Create sections before bulk uploading: Shop Manager → Listings → "Organize your listings" → add sections
- Assign listings to a section in bulk via the Listing View bulk editor **Evergreen**

### Publishing flow (full sequence)
1. In Printify: select all products → Publish → "keep individual product details" → Confirm
2. Wait briefly for mockup images to transfer to Etsy
3. In Listing View (or Pre-List): import listings → bulk edit descriptions, tags, photos, sections → hit Publish Listings

---

## Key Takeaways

- **Never use PlaceIt mockups** — no top-selling Etsy POD listing uses them; buy proven mockups directly from Etsy sellers and verify their outlier scores before purchasing.
- **Batch all mockups at once** using Figma (free, fastest) or Photoshop + script (~$20/mo, more realistic blending); start with Figma and graduate to Photoshop once you're making sales.
- **Title formula**: first ~30 characters = plain-English product description for humans; remainder = keyword phrases pulled and shuffled from top-selling competitors via Pre-List.
- **Tags**: prioritize the 2–3 tags with the highest Listing View recommendation score (low competition + high volume) across all listings; fill remaining slots by rotating tags from multiple top-selling listings; don't avoid high-competition tags — Etsy still surfaces new listings there.
- **Descriptions and info cards are templates** — write once, apply to all listings; always keep info cards in the same numbered image slots so bulk-updating them later takes seconds, not hours.
