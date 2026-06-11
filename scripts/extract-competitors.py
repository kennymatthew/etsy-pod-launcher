#!/usr/bin/env python3
"""
extract-competitors.py

Reads etsy-listing-*.md scrape files and builds competitors.json.
Fully deterministic — no API calls, no external dependencies.

All fields are parsed from the scrape text using regex and rules:
- Structured fields: reviews, rating, price, dates, demand signals, image URL, etc.
- Rule-based fields: is_shirt, product_type, colors, print_method, personalization,
  blank, key_phrases — extracted from scrape text patterns
- Subjective fields: design_style, mockup_style, notes — left null
  (fill these in via Claude conversation after running if needed)

Modes:
  default       Parse all scrape files; skip entries whose rule-based fields
                are already populated (identified by key_phrases being non-empty)
  --repair-only Only re-parse structured + calculated fields; preserve all
                existing rule-based and subjective fields untouched (fastest)
  --force       Re-parse ALL fields for every entry (ignores existing data)

Usage:
  python3 scripts/extract-competitors.py --niche dog-mom
  python3 scripts/extract-competitors.py --niche dog-mom --repair-only
  python3 scripts/extract-competitors.py --niche dog-mom --force
"""

import argparse, json, re, datetime, os, sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

CAPTCHA_SIGNALS = [
    'verify you', 'are you human', 'robot check', 'access denied',
    'captcha', 'unusual traffic', "this page isn't", 'security check',
    'please enable cookies', 'cf-browser-verification',
]

def _is_captcha(content):
    low = content[:3000].lower()
    return any(sig in low for sig in CAPTCHA_SIGNALS)


MONTHS_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

SHIRT_KEYWORDS = [
    't-shirt', 'tshirt', 'tee shirt', ' tee', 'sweatshirt',
    'hoodie', 'tank top', 'crewneck', 'crew neck', 'long sleeve',
    'pullover', 'raglan', 'comfort colors shirt', 'gildan shirt',
    ' shirt', 'shirt,', 'shirt.',   # catches "Pet Shirt", "Dog Shirt", etc.
]

PRODUCT_TYPE_MAP = [
    (['sweatshirt', 'crewneck', 'crew neck', 'pullover'],         'sweatshirt'),
    (['hoodie'],                                                    'hoodie'),
    (['tank top', 'tank-top'],                                      'tank top'),
    (['long sleeve', 'longsleeve'],                                 'long sleeve'),
    (['t-shirt', 'tshirt', 'tee shirt', ' tee ', ' tee,',
      'shirt', 'unisex shirt', 'comfort colors'],                   't-shirt'),
    (['mug', 'coffee cup', 'ceramic cup'],                          'mug'),
    (['tumbler', 'water bottle', 'stanley'],                        'tumbler'),
    (['hat', 'cap', 'baseball cap', 'trucker hat', 'beanie'],       'hat'),
    (['tote bag', 'canvas bag'],                                    'tote bag'),
    (['phone case'],                                                 'phone case'),
    (['cutting board'],                                             'cutting board'),
    (['ornament'],                                                  'ornament'),
    (['keychain', 'key chain'],                                     'keychain'),
    (['pillow', 'cushion'],                                         'pillow'),
    (['sign', 'plaque'],                                            'sign'),
    (['frame', 'print', 'poster', 'canvas'],                       'wall art'),
    (['socks', 'sock'],                                             'socks'),
    (['blanket'],                                                   'blanket'),
    (['apron'],                                                     'apron'),
    (['pajama', 'pyjama', 'lounge pants'],                         'pajamas'),
    (['bracelet', 'necklace', 'jewelry', 'jewellery'],             'jewelry'),
]

# UI strings that appear in Etsy dropdown markup and must never be treated as colors
COLOR_JUNK = {
    "Select an option",
    "Please select an option",
    "KlarnaCheck purchase power",
    "Add to cart",
    "Loading",
    "Quantity",
    "Add personalization",
    "Retry upload",
    "Upload files",
    "Default",
    "DIGITAL FILE ONLY",
    "Embroidery File Only",
    "New Digitization",
    "Revision Add On",
}

# Matches standalone size abbreviations and spelled-out sizes
_COLOR_SIZE_RE = re.compile(
    r'^(XS|S|M|L|XL|2XL|XXL|3XL|XXXL|'
    r'Small|Medium|Large|X-?Large|XX?-?Large)$',
    re.IGNORECASE,
)

# Matches strings that START with a product-type keyword (used to catch
# "Adult Small", "Unisex T-Shirt - S", "Premium T-Shirt L", etc.)
_COLOR_PRODUCT_START_RE = re.compile(
    r'^(Adult|Youth|Women|Unisex|Premium|T-?Shirt|Sweatshirt|Hoodie|'
    r'Tank|Tanktops?|V-?Neck|SweatshirtComfort)\b',
    re.IGNORECASE,
)


def _clean_color_candidate(raw: str):
    """
    Given a raw candidate string from the scrape, return the cleaned colour name
    or None if the candidate should be discarded.

    Handles:
    - Multi-line dropdown labels embedded as \\n\\n (take last segment)
    - Known UI junk strings
    - Size-only entries (S, M, Adult Small, Unisex T-Shirt - L, etc.)
    - "Color - Size" and "Color/Size" variant strings → returns unique colour
    """
    # Strip multi-line dropdown prefix (e.g. "Colors\n\nSelect an option\n\nWhite")
    if '\n\n' in raw:
        parts = [p.strip() for p in raw.split('\n\n') if p.strip()]
        raw = parts[-1] if parts else raw
    s = raw.strip()

    if not s or s in COLOR_JUNK:
        return None

    # Pure size abbreviation
    if _COLOR_SIZE_RE.match(s):
        return None

    # Starts with a product-type keyword and last token is a size
    if _COLOR_PRODUCT_START_RE.match(s):
        last = s.split()[-1] if s.split() else ''
        if _COLOR_SIZE_RE.match(last):
            return None
        # e.g. "Adult Unisex - S"
        if ' - ' in s and _COLOR_SIZE_RE.match(s.rsplit(' - ', 1)[-1].strip()):
            return None

    # "Color - Size" pattern → extract colour; "ProductType - Color" → extract colour
    if ' - ' in s:
        a, _, b = s.rpartition(' - ')
        b = b.strip()
        if _COLOR_SIZE_RE.match(b):
            # B is a size: A is either a colour or "Brand - Color" — recurse to unwrap
            if _COLOR_PRODUCT_START_RE.search(a):
                return None
            if ' - ' in a:
                return _clean_color_candidate(a)
            return a.strip()
        else:
            # B is likely a colour name (e.g. "Comfort Colors Shirt - White")
            return b

    # "Color/Size" pattern → extract colour
    if '/' in s:
        a, _, b = s.rpartition('/')
        b = b.strip()
        if _COLOR_SIZE_RE.match(b):
            return None if _COLOR_PRODUCT_START_RE.search(a) else a.strip()

    return s


PRODUCT_TYPE_VARIANTS = [
    ('t-shirt',      re.compile(r'\b(t-?shirt|tee|unisex shirt|comfort colors shirt|gildan shirt)\b', re.I)),
    ('sweatshirt',   re.compile(r'\b(sweatshirt|crewneck|crew.?neck|pullover)\b', re.I)),
    ('hoodie',       re.compile(r'\bhoodie\b', re.I)),
    ('tank top',     re.compile(r'\btank.?top\b|\btank\b', re.I)),
    ('v-neck',       re.compile(r'\bv-?neck\b', re.I)),
    ('long sleeve',  re.compile(r'\blong.?sleeve\b', re.I)),
    ('youth',        re.compile(r'\byouth\b', re.I)),
]

ANCHOR_PATTERNS = [
    ('digital_file',    re.compile(r'\bdigital\b|\bsvg\b|\bpng\b|\bpdf\b|\bprintable\b|\bdigital file\b|\bfile only\b', re.I)),
    ('sticker',         re.compile(r'\bsticker\b', re.I)),
    ('magnet',          re.compile(r'\bmagnet\b', re.I)),
    ('keychain',        re.compile(r'\bkeychain\b|\bkey chain\b|\bzipper pull\b', re.I)),
    ('ornament',        re.compile(r'\bornament\b', re.I)),
    ('pin',             re.compile(r'\bpin\b|\bbutton\b|\benamel pin\b', re.I)),
    ('patch',           re.compile(r'\bpatch\b|\biron.on\b', re.I)),
    ('card',            re.compile(r'\bpostcard\b|\bgreeting card\b', re.I)),
    ('bookmark',        re.compile(r'\bbookmark\b', re.I)),
    ('coaster',         re.compile(r'\bcoaster\b', re.I)),
    ('bandana',         re.compile(r'\bbandana\b', re.I)),
    ('embroidery_file', re.compile(r'\bembroidery file\b|\bdigitization\b', re.I)),
    ('youth',           re.compile(r'\byouth\b|\bkids?\b|\btoddler\b|\bbaby\b|\binfant\b|\bonesie\b', re.I)),
    ('small_item',      re.compile(r'\bsample\b|\bswatch\b|\btemporary tattoo\b|\btemp tattoo\b', re.I)),
]

BLANK_PATTERNS = [
    (r'Gildan\s*5000',        'Gildan 5000'),
    (r'Gildan\s*64000',       'Gildan 64000'),
    (r'Gildan\s*18500',       'Gildan 18500'),
    (r'Bella\s*\+?\s*Canvas\s*3001', 'Bella+Canvas 3001'),
    (r'Bella\s*Canvas',       'Bella Canvas'),
    (r'Comfort\s*Colors\s*1717', 'Comfort Colors 1717'),
    (r'Comfort\s*Colors',     'Comfort Colors'),
    (r'Next\s*Level',         'Next Level'),
    (r'AS\s*Colour',          'AS Colour'),
    (r'Independent\s*Trading','Independent Trading'),
    (r'Hanes',                'Hanes'),
    (r'Port\s*&?\s*Company',  'Port & Company'),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

_NOISE_PATTERNS = [
    r'^##\s+More from this shop',
    r'^##\s+Buy together',
    r'^##\s+Meet your seller',
    r'^##\s+Did you know',
    r'^##\s+Privacy',
    r'^##\s+Shop policies',
]

def _noise_boundary(content):
    """Return the index of the first cross-sell / noise section, or len(content)."""
    boundary = len(content)
    for pattern in _NOISE_PATTERNS:
        m = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
        if m and m.start() < boundary:
            boundary = m.start()
    return boundary


def load_env():
    env = dict(os.environ)
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()
    return env


def parse_k_number(s):
    """Parse '1.6k' → 1600, '5,800' → 5800, '19' → 19. Returns 0 on parse failure."""
    try:
        s = str(s).strip().lower().replace(',', '')
        if s.endswith('k'):
            return int(float(s[:-1]) * 1000)
        return int(float(s))
    except (ValueError, AttributeError):
        return 0


def parse_date_str(s):
    """Parse 'Jun 2, 2026', '02 Jun, 2026', 'June 2nd, 2026' → '2026-06-02'. Returns None on failure."""
    s = s.strip()
    s = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', s)
    m = re.match(r'(\w{3})\s+(\d{1,2}),?\s+(\d{4})', s)
    if m:
        month, day, year = m.groups()
        mo = MONTHS_MAP.get(month.lower())
        if mo:
            return f"{year}-{mo:02d}-{int(day):02d}"
    m = re.match(r'(\d{1,2})\s+(\w{3}),?\s+(\d{4})', s)
    if m:
        day, month, year = m.groups()
        mo = MONTHS_MAP.get(month.lower())
        if mo:
            return f"{year}-{mo:02d}-{int(day):02d}"
    return None


# ── Structured field parser ───────────────────────────────────────────────────

def parse_structured(content, listing_id, creation_date=None):
    result = {
        'id':  listing_id,
        'url': f'https://www.etsy.com/listing/{listing_id}/',
    }

    # Title
    m = re.search(r'^# (.+)$', content, re.MULTILINE)
    result['title'] = m.group(1).strip() if m else None

    # Price
    m = re.search(r'Price:\s*([^\n]+)', content)
    result['price'] = m.group(1).strip() if m else None

    # Shop name
    m = re.search(r'\[([^\]]+)\]\(https://www\.etsy\.com/shop/([^?/\)]+)', content)
    result['shop_name'] = m.group(1).strip() if m else None

    # Shop total sales count (shown in listing's shop info — lifetime shop figure, not listing-level)
    m = re.search(r'([\d,]+(?:\.\d+)?k?)\s+sales', content, re.IGNORECASE)
    result['shop_sales'] = parse_k_number(m.group(1)) if m else None

    # Shop age — "X years on Etsy", "X.X years on Etsy", or "X months on Etsy"
    m_yr = re.search(r'([\d]+(?:\.\d+)?)\s+years?\s+on\s+Etsy', content, re.IGNORECASE)
    m_mo = re.search(r'([\d]+)\s+months?\s+on\s+Etsy', content, re.IGNORECASE)
    if m_yr:
        result['shop_years_on_etsy'] = float(m_yr.group(1))
    elif m_mo:
        result['shop_years_on_etsy'] = round(int(m_mo.group(1)) / 12, 2)
    else:
        result['shop_years_on_etsy'] = None

    # All product listing images — only from before cross-sell noise sections
    img_section = content[:_noise_boundary(content)]
    all_img_urls = list(dict.fromkeys(
        re.findall(r'https://i\.etsystatic\.com/[^\s\)]+il_794xN[^\s\)]+\.jpg', img_section)
    ))
    result['image_urls'] = all_img_urls
    result['image_url']  = all_img_urls[0] if all_img_urls else None

    # Badge — Bestseller, Etsy's Pick, Rare find (mutually exclusive; first match wins)
    # Etsy shows exactly one badge per listing (mutually exclusive, single UI slot).
    # Priority order matches Etsy's own display hierarchy.
    if re.search(r'(?m)^Bestseller\s*$', content, re.IGNORECASE):
        result['badge'] = 'Bestseller'
    elif re.search(r"Etsy['’]?s?\s*Pick", content, re.IGNORECASE):
        result['badge'] = "Etsy's Pick"
    elif re.search(r'\bPopular\s+Now\b', content, re.IGNORECASE):
        result['badge'] = 'Popular Now'
    elif re.search(r'\bRare\s+find\b', content, re.IGNORECASE):
        result['badge'] = 'Rare find'
    else:
        result['badge'] = None
    result['is_bestseller'] = result['badge'] == 'Bestseller'

    # In-carts — capture all Etsy cart-count variants and normalise to an integer.
    # "In 1 person's cart" / "In X people's carts" / "In X+ carts" / "Over 20 people have this in their cart"
    m = re.search(
        r'(?:In (\d+)\+?\s+(?:people\'?s?\s+)?(?:carts?|baskets?)'
        r'|In (\d+)\s+person\'?s?\s+cart'
        r'|Over\s+(\d+)\s+people\s+have\s+this\s+in\s+their\s+cart)',
        content, re.IGNORECASE
    )
    if m:
        result['in_carts'] = int(m.group(1) or m.group(2) or m.group(3))
    else:
        result['in_carts'] = None

    # Demand signals — full matrix of Etsy's automated urgency/social-proof sentences.
    # Dynamic velocity signals (bought in last 24h etc.) are included: they are noise
    # for any single scrape but useful for spotting hot listings when scraped frequently.
    result['demand_signals'] = re.findall(
        r'('
        # In-carts variants
        r'In \d+\+?\s+(?:people\'?s?\s+)?(?:carts?|baskets?)'
        r'|In \d+\s+person\'?s?\s+cart'
        r'|Over \d+ people have this in their cart'
        # Sales-velocity variants
        r'|In demand\.?\s+\d+ people bought this in the last \d+ hours?'
        r'|Popular!?\s+\d+ people bought this in the last \d+ hours?'
        r'|\d+ people have bought this in the last \d+ days?'
        r'|\d+ sales? in the last \d+ hours?'
        r'|In high demand'
        # Scarcity variants
        r'|Only \d+ left(?:\s+and\s+in\s+\d+\+?\s+carts?)?[^.\n]*'
        r'|Low in stock[^.\n]*'
        r'|Almost gone'
        r'|Low stock'
        r')',
        content, re.IGNORECASE
    )

    # Star Seller
    result['star_seller'] = bool(re.search(r'\bStar Seller\b', content))

    # Free shipping
    result['free_shipping'] = bool(re.search(r'(?m)^-\s*Free shipping\s*$', content, re.IGNORECASE))

    # Ships from
    m = re.search(r'Ships from:\s*\*{0,2}([^*\n]+?)\*{0,2}\s*$', content, re.MULTILINE)
    result['ships_from'] = m.group(1).strip() if m else None

    # Returns
    if re.search(r'Returns\s*&?\s*exchanges?\s+not\s+accepted', content, re.IGNORECASE):
        result['returns_accepted'] = False
    elif re.search(r'Returns\s*&?\s*exchanges?\s+accepted', content, re.IGNORECASE):
        result['returns_accepted'] = True
    else:
        result['returns_accepted'] = None

    # Has sale
    result['has_sale'] = bool(re.search(r'Sale ends in|Sale Price\s*\$', content, re.IGNORECASE))

    # Sale percent (e.g. "30% off")
    m = re.search(r'(\d+)%\s+off', content, re.IGNORECASE)
    result['sale_percent'] = int(m.group(1)) if m else None

    # Sale type
    if re.search(r'limited time sale', content, re.IGNORECASE):
        result['sale_type'] = 'limited_time'
    elif result['has_sale']:
        result['sale_type'] = 'sale'
    else:
        result['sale_type'] = None

    # Full item description
    m = re.search(r'## Item details\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
    result['description'] = m.group(1).strip() if m else None

    # Favorites
    m = re.search(r'\[([\d,]+(?:\.\d+)?k?)\s+favorites?\]', content, re.IGNORECASE)
    result['favorites_count'] = parse_k_number(m.group(1)) if m else 0

    # Reviews section
    rev_idx = content.find('## Reviews for this item')
    if rev_idx >= 0:
        rev_section = content[rev_idx:]

        m = re.search(r'(\d+\.\d+)\s*\n+\s*Item average', rev_section)
        result['rating'] = float(m.group(1)) if m else None

        m = re.search(r'\(([\d,]+(?:\.\d+)?k?)\s+reviews?\)', rev_section, re.IGNORECASE)
        result['reviews'] = parse_k_number(m.group(1)) if m else 0

        date_pat = r'\b(\d{1,2}\s+\w{3},?\s+\d{4}|\w{3}\s+\d{1,2},?\s+\d{4})\b'
        raw_dates = re.findall(date_pat, rev_section)
        dates = [parse_date_str(d) for d in raw_dates]
        dates = sorted([d for d in dates if d and d > '2000-01-01'], reverse=True)
        result['most_recent_review_date'] = dates[0] if dates else None
    else:
        result['rating']                  = None
        result['reviews']                 = 0
        result['most_recent_review_date'] = None

    fav = result['favorites_count']
    reviews = result['reviews']
    result['favorites_per_review'] = round(fav / reviews, 1) if reviews > 0 else None

    # Pricing fields (parse from full raw content)
    pricing = parse_pricing(content)
    result.update(pricing)

    return result


# ── Rule-based field parser ───────────────────────────────────────────────────

def parse_rule_based(content, title):
    """
    Extract fields that look fuzzy but are actually deterministic from scrape text.
    No AI needed — rules derived from Etsy scrape patterns.
    """
    result = {}
    title_lower = (title or '').lower()

    # Truncate at the first cross-sell / noise section
    clean_content = content[:_noise_boundary(content)]

    # Also strip image markdown lines (alt text can describe unrelated products)
    clean_content = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', clean_content)

    # ── is_shirt ──
    result['is_shirt'] = any(kw in title_lower for kw in SHIRT_KEYWORDS)

    # ── product_type ──
    result['product_type'] = None
    for keywords, ptype in PRODUCT_TYPE_MAP:
        if any(kw in title_lower for kw in keywords):
            result['product_type'] = ptype
            break

    # ── blank ──
    result['blank'] = None
    for pattern, name in BLANK_PATTERNS:
        if re.search(pattern, clean_content, re.IGNORECASE):
            result['blank'] = name
            break

    # ── print_method + print_method_confirmed ──
    # Tier 1: title contains the keyword → confirmed=True (seller named it explicitly)
    # Tier 2: clean_content contains keyword but title doesn't → confirmed=False (inferred from description)

    if re.search(r'\bdtg\b|direct.to.garment', title_lower):
        result['print_method'] = 'dtg'
        result['print_method_confirmed'] = True
    elif re.search(r'\bscreen.?print', title_lower):
        result['print_method'] = 'screen print'
        result['print_method_confirmed'] = True
    elif re.search(r'\bembroidered?\b', title_lower):
        result['print_method'] = 'embroidery'
        result['print_method_confirmed'] = True
    elif re.search(r'\bsublimation\b|\ball.over.print\b', title_lower):
        result['print_method'] = 'sublimation'
        result['print_method_confirmed'] = True
    elif re.search(r'\blaser.engrav', title_lower):
        result['print_method'] = 'laser engraving'
        result['print_method_confirmed'] = True
    # Tier 2: keyword found in cleaned content (description/highlights/reviews) but not title
    elif re.search(r'\bdtg\b|direct.to.garment', clean_content, re.IGNORECASE):
        result['print_method'] = 'dtg'
        result['print_method_confirmed'] = True  # "DTG" in description is still explicit
    elif re.search(r'\bscreen.?print', clean_content, re.IGNORECASE):
        result['print_method'] = 'screen print'
        result['print_method_confirmed'] = True  # same — very specific term
    elif re.search(r'\bembroidered?\b', clean_content, re.IGNORECASE):
        result['print_method'] = 'embroidery'
        result['print_method_confirmed'] = False  # in description only — inferred
    elif re.search(r'\bsublimation\b|\ball.over.print\b', clean_content, re.IGNORECASE):
        result['print_method'] = 'sublimation'
        result['print_method_confirmed'] = False
    elif re.search(r'\blaser.engrav', clean_content, re.IGNORECASE):
        result['print_method'] = 'laser engraving'
        result['print_method_confirmed'] = False
    # Tier 3: infer from blank
    elif result['blank'] in ('Gildan 5000', 'Bella+Canvas 3001', 'Bella Canvas',
                              'Comfort Colors 1717', 'Comfort Colors', 'Next Level'):
        result['print_method'] = 'dtg'
        result['print_method_confirmed'] = False
    else:
        result['print_method'] = 'unknown'
        result['print_method_confirmed'] = False

    # ── personalization ──
    result['personalization'] = bool(re.search(
        r'personali|custom(?:ized?|ise|ization)|add your|enter (your|a |the )|'
        r'your (?:name|pet|photo|text|dog|cat)|upload (?:your )?photo',
        clean_content, re.IGNORECASE
    ))

    # ── personalization_type ──
    result['personalization_type'] = None
    if result['personalization']:
        types = []
        if re.search(r'photo|image|picture|portrait', clean_content, re.IGNORECASE):
            types.append('photo')
        if re.search(r'\bname\b', clean_content, re.IGNORECASE):
            types.append('name')
        if re.search(r'\bdate\b|\banniversary\b|\bbirthday\b', clean_content, re.IGNORECASE):
            types.append('date')
        if re.search(r'\btext\b|\bmessage\b|\bquote\b', clean_content, re.IGNORECASE):
            types.append('text')
        if re.search(r'\bpet\b|\bdog\b|\bcat\b', clean_content, re.IGNORECASE):
            types.append('pet name/breed')
        result['personalization_type'] = ', '.join(types) if types else 'custom text'

    # ── colors ──
    # Etsy color dropdowns appear as lines: "Color Name ($X.XX - $Y.YY)" or "Color Name"
    # Look for the color section block between "Color" label and the next section.
    # _clean_color_candidate filters UI junk, size-only entries, and deduplicates
    # color+size variant strings (e.g. "Black - S", "Orchid/Medium").
    colors = []
    seen_colors: set[str] = set()

    def _add_color(raw: str) -> None:
        c = _clean_color_candidate(raw)
        if c and 2 <= len(c) <= 40 and c not in seen_colors:
            seen_colors.add(c)
            colors.append(c)

    color_section = re.search(
        r'(?:^|\n)(?:Color|Colour)[:\s]*\n(.*?)(?=\n##|\n\*\*|\nSize|\nStyle|\Z)',
        clean_content, re.DOTALL | re.IGNORECASE
    )
    if color_section:
        for line in color_section.group(1).splitlines():
            line = line.strip()
            # Lines like "Natural ($13.64 - $36.39)" or just "Black"
            m = re.match(r'^([A-Z][a-zA-Z\s/\-]+?)(?:\s*\([^)]*\))?\s*$', line)
            if m:
                _add_color(m.group(1).strip())
    # Fallback: look for color dropdown pattern directly
    if not colors:
        for m in re.finditer(
            r'^([A-Z][a-zA-Z\s/\-]{1,35})\s+\(\s*\$[\d.]+',
            clean_content, re.MULTILINE
        ):
            _add_color(m.group(1).strip())

    result['colors'] = colors if colors else None

    # ── product_types + multi_product_listing ──
    # Scan short variant/option lines (< 60 chars) for product-type keywords.
    # Variant dropdown lines are always short; descriptions and reviews are longer,
    # so this length filter avoids false positives from prose mentions.
    variant_text = '\n'.join(
        line for line in clean_content.splitlines()
        if len(line.strip()) < 60
    )

    found_types = []
    for ptype, pat in PRODUCT_TYPE_VARIANTS:
        if pat.search(variant_text):
            found_types.append(ptype)

    result['product_types'] = sorted(found_types) if found_types else (
        [result['product_type']] if result.get('product_type') else []
    )
    result['multi_product_listing'] = len(found_types) > 1

    # ── key_phrases ── split on Etsy title separators; fall back to filler words
    if title:
        # Primary split: commas, pipes, em-dashes, " + ", " - " (spaced only, avoids "t-shirt")
        parts = [p.strip() for p in re.split(r'[,|–—]|\s+\+\s+|\s+-\s+', title) if p.strip()]
        # Fallback for comma-free titles: split on common connector words
        if len(parts) < 2:
            parts = [p.strip() for p in re.split(
                r'\s+(?:for|and|with|by|from|gift)\s+', title, flags=re.I
            ) if p.strip()]
        result['key_phrases'] = [p[:60] for p in parts[:5]]
    else:
        result['key_phrases'] = []

    # Subjective fields — left for Claude conversation if needed
    result['design_style'] = None
    result['mockup_style'] = 'unknown'
    result['notes']        = None

    return result


# ── Pricing field parser ──────────────────────────────────────────────────────

def parse_pricing(content):
    """
    Parse variant pricing from raw scrape content.

    Returns a dict with keys:
      price_max, price_real_min, anchor_type, anchor_price, price_spread, blank_tiers

    All values may be None if the data is not found.
    """
    raw_content = content[:_noise_boundary(content)]

    # Regex: match variant lines like "Label ($9.00)" or "Label ($9.00 - $29.25)"
    VARIANT_RE = re.compile(
        r'^(.+?)\s+\(\$(\d+\.?\d*)(?:\s*-\s*\$(\d+\.?\d*))?\)\s*$',
        re.MULTILINE
    )

    # Regex for blank_tiers: "Blank - Size ($price)" — only single-price lines
    BLANK_SIZE_RE = re.compile(
        r'^([\w\s\+]+?)\s+-\s+((?:XS|S|M|L|XL|2XL|XXL|3XL|XXXL|4XL|5XL|6XL))\s+\(\$(\d+\.?\d*)\)\s*$',
        re.MULTILINE | re.IGNORECASE
    )

    # Collect all variant lines: (label, low_price, high_price_or_None)
    variants = []
    for m in VARIANT_RE.finditer(raw_content):
        label  = m.group(1).strip()
        low    = float(m.group(2))
        high   = float(m.group(3)) if m.group(3) else None
        variants.append((label, low, high))

    if not variants:
        return {
            'price_max':        None,
            'price_real_min':   None,
            'anchor_type':      None,
            'anchor_price':     None,
            'price_spread':     None,
            'blank_tiers':      None,
            'quantity_pricing': False,
        }

    # Collect ALL prices for price_max (use high if present, else low)
    all_prices = []
    for label, low, high in variants:
        all_prices.append(high if high is not None else low)
        all_prices.append(low)

    price_max = max(all_prices)

    # Anchor detection per variant (label → anchor_type or None)
    def detect_anchor_type(label):
        for atype, pat in ANCHOR_PATTERNS:
            if pat.search(label):
                return atype
        return None

    # Separate anchors from non-anchors using Tier 1 named patterns first
    anchor_candidates = []   # (anchor_type, price)
    non_anchor_prices = []

    for label, low, high in variants:
        atype = detect_anchor_type(label)
        # Use the effective price for this variant: low (the price it contributes to min)
        effective_price = low
        if atype:
            anchor_candidates.append((atype, effective_price))
        else:
            non_anchor_prices.append(effective_price)

    # Detect quantity pricing: variant labels that are bare numbers or "Pack of X" / "Set of X" / "Qty X"
    qty_pattern = re.compile(r'^(\d+|Pack of \d+|Set of \d+|Qty\.?\s*\d+)$', re.I)
    qty_matches = [label for label, lo, hi in variants if qty_pattern.match(label.strip())]
    quantity_pricing = len(qty_matches) >= 2

    # Tier 2: size anchor detection
    # Look for variants like "ProductType - Size ($price)" or "ProductType Size ($price)"
    SIZE_ORDER = ['XS', 'S', 'M', 'L', 'XL', '2XL', 'XXL', '3XL', '4XL', '5XL']
    ADULT_SIZES = {'S', 'M', 'L', 'XL', '2XL', 'XXL', '3XL', '4XL', '5XL'}

    size_variant_re = re.compile(
        r'^(.+?)\s*[-\s]\s*(XS|S|M|L|XL|2XL|XXL|3XL|4XL|5XL|6XL)\s*$', re.I
    )

    # Group variant prices by product_label -> {size: min_price}
    size_price_map = {}  # {normalized_label: {size: price}}
    for label, lo, hi in variants:
        mv = size_variant_re.match(label.strip())
        if mv:
            base = mv.group(1).strip().lower()
            size = mv.group(2).upper()
            if size in ADULT_SIZES:
                if base not in size_price_map:
                    size_price_map[base] = {}
                existing = size_price_map[base].get(size, float('inf'))
                size_price_map[base][size] = min(existing, lo)

    # Check if S is significantly cheaper than M (or L as fallback)
    size_anchor_type  = None
    size_anchor_price = None
    for base, sizes in size_price_map.items():
        s_price = sizes.get('S')
        m_price = sizes.get('M') or sizes.get('L')  # fallback to L if no M
        if s_price and m_price and m_price > 0:
            discount = (m_price - s_price) / m_price
            if discount >= 0.50:
                size_anchor_type  = 'size_anchor_high'
                size_anchor_price = s_price
                break
            elif discount >= 0.20:
                size_anchor_type  = 'size_anchor_low'
                size_anchor_price = s_price
                # don't break — keep looking for a worse one

    # Determine the dominant anchor (priority: named > size_anchor_high > size_anchor_low)
    anchor_type  = None
    anchor_price = None
    if anchor_candidates:
        # Named anchor: sort by price ascending, pick the cheapest one
        anchor_candidates.sort(key=lambda x: x[1])
        anchor_type, anchor_price = anchor_candidates[0]
    elif size_anchor_type:
        anchor_type  = size_anchor_type
        anchor_price = size_anchor_price

    # Non-garment anchor types — digital files, embroidery files, small add-ons.
    # These should never be used as a price_real_min fallback for a shirt listing.
    _NON_GARMENT_ANCHORS = {
        'digital_file', 'embroidery_file', 'sticker', 'magnet', 'keychain',
        'ornament', 'pin', 'patch', 'card', 'bookmark', 'coaster', 'bandana',
        'small_item',
    }

    # price_real_min: minimum price among non-anchor variants
    if non_anchor_prices:
        price_real_min = min(non_anchor_prices)
    elif anchor_candidates:
        # Only fall back to anchor price if the anchor is a garment (size-based), not a
        # non-garment add-on like a digital file — those would give a misleadingly low price.
        garment_anchors = [(t, p) for t, p in anchor_candidates if t not in _NON_GARMENT_ANCHORS]
        if garment_anchors:
            price_real_min = min(p for _, p in garment_anchors)
        else:
            price_real_min = None
    else:
        price_real_min = None

    # price_spread
    if price_max is not None and price_real_min is not None:
        price_spread = round(price_max - price_real_min, 2)
    else:
        price_spread = None

    # blank_tiers construction
    SIZE_GROUP = {
        'XS': 'XS', 'S': 'S-XL', 'M': 'S-XL', 'L': 'S-XL', 'XL': 'S-XL',
        '2XL': '2XL', 'XXL': '2XL',
        '3XL': '3XL', 'XXXL': '3XL',
        '4XL': '4XL',
        '5XL': '5XL',
        '6XL': '6XL',
    }

    # Only accept known blank brand names as the left-hand side of "Blank - Size ($price)"
    # This prevents color names (e.g. "Black - S") from being treated as blanks.
    _BLANK_BRAND_RE = re.compile(
        r'\b(comfort colors?|gildan|bella\s*\+?\s*canvas|next level|hanes|'
        r'port\s*&?\s*company|independent trading|as colou?r|'
        r'district|anvil|alternative|jerzees|fruit of the loom)\b',
        re.I
    )

    blank_tiers_raw = {}  # blank → size_group → [prices]
    for m in BLANK_SIZE_RE.finditer(raw_content):
        blank_name = m.group(1).strip()
        # Skip if the blank name doesn't look like a known garment brand
        if not _BLANK_BRAND_RE.search(blank_name):
            continue
        size_raw   = m.group(2).upper()
        price      = float(m.group(3))
        group      = SIZE_GROUP.get(size_raw, size_raw)
        blank_tiers_raw.setdefault(blank_name, {}).setdefault(group, []).append(price)

    blank_tiers = None
    if blank_tiers_raw:
        blank_tiers = {}
        for blank_name, groups in blank_tiers_raw.items():
            blank_tiers[blank_name] = {
                grp: round(max(prices), 2)   # use max within group (most common = representative price)
                for grp, prices in groups.items()
            }
        # blank_tiers is the most accurate source for real garment prices — override both bounds
        all_blank_prices = [p for sizes in blank_tiers.values() for p in sizes.values()]
        price_real_min = min(all_blank_prices)
        price_max = max(all_blank_prices)

    return {
        'price_max':        round(price_max, 2) if price_max is not None else None,
        'price_real_min':   round(price_real_min, 2) if price_real_min is not None else None,
        'anchor_type':      anchor_type,
        'anchor_price':     round(anchor_price, 2) if anchor_price is not None else None,
        'price_spread':     price_spread,
        'blank_tiers':      blank_tiers,
        'quantity_pricing': quantity_pricing,
    }


# ── Self-check ────────────────────────────────────────────────────────────────

def self_check(entries):
    warnings = []
    total    = len(entries)
    zero_rev = sum(1 for e in entries if e.get('reviews', 0) == 0)
    shirts   = sum(1 for e in entries if e.get('is_shirt'))

    if zero_rev > total * 0.3:
        warnings.append(f"⚠  {zero_rev}/{total} entries have reviews=0 — "
                        f"check if scrape files contain a '## Reviews for this item' section")
    if shirts == 0:
        warnings.append(f"⚠  No shirt listings found (is_shirt=true for 0 entries) — "
                        f"check that SHIRT_KEYWORDS match title patterns in this niche")
    elif shirts < total * 0.1:
        warnings.append(f"⚠  Only {shirts}/{total} listings detected as shirts — "
                        f"verify SHIRT_KEYWORDS cover this niche's title patterns")

    # Duplicate first image check (cross-listing data bleed)
    url_to_shops = {}
    for e in entries:
        urls = e.get('image_urls') or ([e['image_url']] if e.get('image_url') else [])
        url = urls[0] if urls else None
        if url:
            url_to_shops.setdefault(url, []).append(e.get('shop_name', e.get('id', '?')))
    dupes = {url: shops for url, shops in url_to_shops.items() if len(shops) > 1}
    if dupes:
        for url, shops in dupes.items():
            warnings.append(
                f"⚠  Duplicate first image_url shared by {len(shops)} shops "
                f"({', '.join(shops)}): {url[:80]}…"
            )

    # Schema completeness
    for e in entries:
        for field in ('id', 'url', 'title', 'price', 'reviews', 'shop_name'):
            if not e.get(field):
                warnings.append(f"⚠  Entry {e.get('id','?')}: required field '{field}' is null/empty")

    return warnings


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Build competitors.json from scrape files (no API required)')
    parser.add_argument('--niche',        required=True, help='Project slug, e.g. dog-mom')
    parser.add_argument('--repair-only',  action='store_true',
                        help='Only reparse structured/calculated fields; keep existing rule-based fields')
    parser.add_argument('--force',        action='store_true',
                        help='Re-parse ALL fields for every entry (ignores existing data)')
    args = parser.parse_args()

    project_dir = BASE_DIR / 'projects' / args.niche / '01-research'
    scrapes_dir = project_dir / 'scrapes'
    output_path = project_dir / 'competitors.json'
    dates_path  = scrapes_dir / 'listing-dates.json'

    if not scrapes_dir.exists():
        print(f"✗ scrapes directory not found: {scrapes_dir}")
        return 1

    # Load creation dates from Etsy API if available
    creation_dates = {}
    if dates_path.exists():
        try:
            creation_dates = json.loads(dates_path.read_text())
        except Exception:
            pass

    # Load existing competitors.json to allow repair/incremental modes
    existing = {}
    if output_path.exists():
        try:
            for entry in json.loads(output_path.read_text()):
                existing[entry['id']] = entry
        except Exception:
            pass

    scrape_files = sorted(scrapes_dir.glob('etsy-listing-*.md')) + \
                   sorted(scrapes_dir.glob('etsy-shirt-*.md'))

    if not scrape_files:
        print(f"✗ No etsy-listing-*.md files found in {scrapes_dir}")
        return 1

    mode = 'repair-only' if args.repair_only else ('force' if args.force else 'default')
    print(f"\n── Extract Competitors: {args.niche} ──")
    print(f"Mode     : {mode}")
    print(f"Files    : {len(scrape_files)} scrape files")
    print(f"Existing : {len(existing)} entries in competitors.json\n")

    results = []

    for scrape_path in scrape_files:
        m = re.search(r'etsy-(?:listing|shirt)-(\d+)\.md', scrape_path.name)
        if not m:
            continue
        listing_id = m.group(1)

        content = scrape_path.read_text(encoding='utf-8', errors='replace')
        if len(content) < 200:
            print(f"  skip  {listing_id} (file too small)")
            continue
        if _is_captcha(content):
            print(f"  skip  {listing_id} (CAPTCHA detected — re-run research-competitors.py)")
            continue

        creation_date = creation_dates.get(listing_id)
        structured    = parse_structured(content, listing_id, creation_date)
        prev          = existing.get(listing_id, {})

        if args.repair_only:
            # Keep existing rule-based fields; only update structured + calculated
            rule_based = {k: prev.get(k) for k in (
                'product_type', 'is_shirt', 'blank', 'print_method',
                'print_method_confirmed', 'personalization', 'personalization_type',
                'design_style', 'mockup_style', 'key_phrases', 'colors', 'notes',
                'product_types', 'multi_product_listing',
            )}
        elif args.force or not prev.get('key_phrases'):
            # Full parse
            rule_based = parse_rule_based(content, structured.get('title'))
        else:
            # Entry already fully parsed — keep existing rule-based fields
            rule_based = {k: prev.get(k) for k in (
                'product_type', 'is_shirt', 'blank', 'print_method',
                'print_method_confirmed', 'personalization', 'personalization_type',
                'design_style', 'mockup_style', 'key_phrases', 'colors', 'notes',
                'product_types', 'multi_product_listing',
            )}

        entry = {
            'id':                         structured['id'],
            'url':                        structured['url'],
            'title':                      structured['title'],
            'price':                      structured['price'],
            'reviews':                    structured['reviews'],
            'rating':                     structured['rating'],
            'shop_sales':                 structured['shop_sales'],
            'shop_years_on_etsy':         structured['shop_years_on_etsy'],
            'product_type':               rule_based.get('product_type'),
            'is_shirt':                   rule_based.get('is_shirt', False),
            'blank':                      rule_based.get('blank'),
            'print_method':               rule_based.get('print_method', 'unknown'),
            'print_method_confirmed':     rule_based.get('print_method_confirmed', False),
            'personalization':            rule_based.get('personalization', False),
            'personalization_type':       rule_based.get('personalization_type'),
            'design_style':               rule_based.get('design_style'),
            'mockup_style':               rule_based.get('mockup_style', 'unknown'),
            'key_phrases':                rule_based.get('key_phrases', []),
            'colors':                     rule_based.get('colors'),
            'product_types':              rule_based.get('product_types', []),
            'multi_product_listing':      rule_based.get('multi_product_listing', False),
            'shop_name':                  structured['shop_name'],
            'star_seller':                structured['star_seller'],
            'free_shipping':              structured['free_shipping'],
            'ships_from':                 structured['ships_from'],
            'returns_accepted':           structured['returns_accepted'],
            'has_sale':                   structured['has_sale'],
            'notes':                      rule_based.get('notes'),
            'image_url':                  structured['image_url'],
            'image_urls':                 structured['image_urls'],
            'description':                structured['description'],
            'sale_percent':               structured['sale_percent'],
            'sale_type':                  structured['sale_type'],
            'badge':                      structured['badge'],
            'is_bestseller':              structured['is_bestseller'],
            'in_carts':                   structured['in_carts'],
            'demand_signals':             structured['demand_signals'],
            'favorites_count':            structured['favorites_count'],
            'most_recent_review_date':    structured['most_recent_review_date'],
            'favorites_per_review':       structured['favorites_per_review'],
            # Pricing fields (always re-parsed — structured/calculated, not rule-based)
            'price_max':                  structured['price_max'],
            'price_real_min':             structured['price_real_min'],
            'anchor_type':                structured['anchor_type'],
            'anchor_price':               structured['anchor_price'],
            'price_spread':               structured['price_spread'],
            'blank_tiers':                structured['blank_tiers'],
            'quantity_pricing':           structured['quantity_pricing'],
        }

        results.append(entry)
        status = '✓' if structured['reviews'] > 0 else '○'
        anchor_info = (f"  anchor={structured['anchor_type']}@${structured['anchor_price']}"
                       if structured['anchor_type'] else '')
        qty_info = '  qty_pricing=True' if structured.get('quantity_pricing') else ''
        print(f"  {status}  {listing_id}  reviews={structured['reviews']}  "
              f"rating={structured['rating']}  shirt={entry['is_shirt']}  "
              f"colors={len(entry['colors'] or [])}  method={entry['print_method']}"
              f"  price_max={structured['price_max']}{anchor_info}{qty_info}")

    output_path.write_text(json.dumps(results, indent=2))

    total    = len(results)
    with_rev = sum(1 for e in results if e['reviews'] > 0)
    shirts   = sum(1 for e in results if e.get('is_shirt'))
    personal = sum(1 for e in results if e.get('personalization'))

    print(f"\n── Done ──")
    print(f"Entries      : {total}")
    print(f"With reviews : {with_rev}  |  no reviews: {total - with_rev}")
    print(f"Shirts       : {shirts}")
    print(f"Personalized : {personal}")
    print(f"Saved        : {output_path}\n")

    warnings = self_check(results)
    for w in warnings:
        print(w)

    return 0


if __name__ == '__main__':
    exit(main())
