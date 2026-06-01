# Projects

Each niche you launch lives in its own subfolder here:

```
projects/
  your-niche-name/
    01-research/
      competitors.json      ← scraped competitor data (source of truth)
      keywords.md           ← keyword volumes from eRank
      market-insights.md    ← patterns, gaps, what to copy/avoid
      scrapes/              ← raw Firecrawl output (auto-written by research script)
    02-design/
      brief.md              ← design spec
      print-files/          ← DTG print PNGs uploaded to Printify
    03-mockups/             ← Etsy listing photos
    04-listing/
      titles.md
      descriptions.md
      tags.md
      pricing.md
      listing-snapshot.md
    05-live/
      listings.md           ← published Etsy URLs
    06-performance/
      metrics.md            ← monthly views/sales log
```

To start a new project, tell Claude Code:
> "Create the folder structure for a new project called [your-niche-name]"

This folder is gitignored — your personal niche projects stay on your machine.
