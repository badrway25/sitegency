# Open Issues

## Systemic Issues (affect multiple templates)

### SYS-001 — Dark template text readability
- **Severity:** High
- **Category:** Visual quality
- **Status:** Partially mitigated
- **Templates affected:** All dark-themed templates (~15-20 estimated)
- **Description:** JS runtime dark detection added, but relies on computed background color check after CSS load. Some edge cases may not trigger.
- **Files involved:** customizer/services.py (_inject_premium_interactivity)
- **Notes:** Python-side detection checks inline styles and <style> tags only. Linked CSS dark backgrounds are caught by JS runtime detection. Not all dark templates have been visually verified.

### SYS-002 — Filler text in English in non-EN locales
- **Severity:** Medium
- **Category:** Translation
- **Status:** Partially mitigated
- **Templates affected:** Most templates (original template filler text)
- **Description:** Content pool replaces H1/H2/standalone paragraphs but intentionally skips card titles (H3/H4) and card-level paragraphs to preserve grid layout. This leaves English filler text in cards across non-EN locales.
- **Files involved:** customizer/services.py (_replace_content_with_pool), customizer/content_pool.py
- **Notes:** Trade-off: replacing card text causes height misalignment. Current approach prioritizes layout stability over translation completeness in card bodies.

### SYS-003 — Templates with <3 navbar links
- **Severity:** Medium
- **Category:** Navbar
- **Status:** Identified, partially mitigated
- **Templates affected:** 6 templates (app-landing-tapwise, medical-pulsemed, medical-clinova, finance-wealthnova, fashion-erase-pro, app-landing-appy-pro)
- **Description:** Some templates have minimal or no traditional navbar by design (app landing pages). Others may have structural issues.
- **Files involved:** customizer/services.py (CSS navbar force-show rules)
- **Notes:** App landing pages intentionally minimal. Medical/fashion templates need individual investigation.

### SYS-004 — SVG logo not inserted on 5 templates
- **Severity:** Low
- **Category:** Branding
- **Status:** Identified
- **Templates affected:** 5/192 (97% have logos)
- **Description:** Brand element selectors don't match these templates' HTML structure.
- **Files involved:** customizer/services.py (_inject_brand_identity)
- **Notes:** Need per-template investigation of logo area HTML structure.

### SYS-005 — Hero max-height may clip content on some templates
- **Severity:** Medium
- **Category:** Layout
- **Status:** Partially mitigated
- **Templates affected:** Templates with `max-height: 75vh` applied to hero selectors
- **Description:** Added max-height to prevent oversized heroes, but may clip important hero content on some templates.
- **Files involved:** customizer/services.py (_inject_differentiation_layer CSS)
- **Notes:** Need visual verification across template families.

### SYS-006 — Brand replacement corrupts words via substring matching
- **Severity:** High
- **Category:** Branding
- **Status:** FIXED (Batch 3)
- **Templates affected:** agency-fluxwork (confirmed), potentially others
- **Description:** `_inject_brand_identity` Stage 4 used `.replace()` and regex without `\b` word boundaries. Old brand substrings matched inside Italian/French words (e.g. "Lavori" → "LFluxworkri").
- **Fix:** Replaced all text replacement with pre-compiled `\b`-bounded regex patterns. Both text node and attribute replacement now use word-boundary matching.
- **Files changed:** customizer/services.py (lines ~3534-3583)

### SYS-007 — Content pool replaces counter H2/H3 values with text
- **Severity:** High
- **Category:** Counters/NaN
- **Status:** FIXED (Batch 3)
- **Templates affected:** All 8 Agency templates (confirmed), likely 30+ others
- **Description:** `_replace_content_with_pool` H2 and H3-H6 loops had no counter-context check. H1 loop checked `LOGO_CLASS_KEYWORDS` for counter keywords, but H2/H3/H4/H5/H6 loops did not. Counter numbers got replaced with pool text, causing jQuery counter plugins to animate NaN.
- **Fix:** Added `_is_counter_context()` helper that checks: (1) element's own classes for counter keywords, (2) whether text is numeric, (3) ancestor classes up to 4 levels. Applied to both H2 and H3-H6 loops.
- **Files changed:** customizer/services.py (lines ~675-720)

### SYS-008 — ftco-animate/wow elements permanently hidden in preview
- **Severity:** High
- **Category:** Layout / Visibility
- **Status:** FIXED (Batch 4)
- **Templates affected:** agency-fluxwork (confirmed), estimated 20-30+ Colorlib templates
- **Description:** Many templates use `.ftco-animate` (jQuery Waypoints) or `.wow` (WOW.js) which set `opacity:0; visibility:hidden` and rely on scroll-trigger JS to reveal. In iframe preview, Waypoints/WOW never fires, leaving entire sections invisible.
- **Fix:** Added CSS override in `_inject_differentiation_layer`: `.ftco-animate, .animate-box, [data-animate-effect], .wow { opacity: 1 !important; visibility: visible !important; }`
- **Files changed:** customizer/services.py (_inject_differentiation_layer CSS)
- **Impact:** This is a MAJOR systemic fix — potentially 20-30+ templates that were showing blank/invisible sections are now fully rendered.

### SYS-009 — Typewriter JS artifacts in content-replaced headings
- **Severity:** Medium
- **Category:** Visual quality
- **Status:** FIXED (Batch 4)
- **Templates affected:** agency-ironquill (confirmed), any template using Typed.js
- **Description:** `_replace_content_with_pool` replaces H1 text but leaves inline `<span class="typed-words">` with English typed strings. Result: "Creato per professionisti...differenzaBusiness|"
- **Fix:** CSS `display: none !important` on `.typed-words, .typed-cursor, .typed-cursor--blink`
- **Files changed:** customizer/services.py (_inject_differentiation_layer CSS)

### SYS-010 — Hero elements without background image (blocks-cover pattern)
- **Severity:** Medium
- **Category:** Images
- **Status:** FIXED (Batch 4)
- **Templates affected:** agency-ironquill (confirmed), other templates using .site-blocks-cover / [class*="blocks-cover"]
- **Fix:** (1) Added `[class*="blocks-cover"]::before/::after` to mesh gradient/grain selectors. (2) Added PASS 6 in `_replace_hero_images` to inject background-image on hero elements that have no image at all.
- **Files changed:** customizer/services.py (_inject_differentiation_layer CSS + _replace_hero_images)

### SYS-011 — Placeholder nav labels (Menu One, Sub Menu, etc.)
- **Severity:** Low
- **Category:** Navigation
- **Status:** FIXED (Batch 4)
- **Templates affected:** agency-vantage (confirmed), any template with demo dropdown labels
- **Fix:** Added PLACEHOLDER_LABELS set to `_strip_blocked_nav_links` — strips "Menu One/Two/Three", "Sub Menu One/Two/Three", "Deep Drop Down" etc.
- **Files changed:** customizer/services.py (_strip_blocked_nav_links)

### SYS-012 — Dollar pricing on non-EN locales
- **Severity:** Low
- **Category:** Translation
- **Status:** FIXED (Batch 4)
- **Templates affected:** agency-vantage (confirmed), any template with inline $XX pricing
- **Fix:** Added `$` → `€` regex replacement in `_translate_content` for IT/FR locales + CSS hiding of `.product strong` price elements
- **Files changed:** customizer/services.py (_translate_content + _inject_differentiation_layer CSS)

## Template-Specific Issues (Agency family — Batch 3)

### TMPL-001 — agency-ironquill: typewriter JS concatenation
- **Severity:** Medium
- **Category:** Visual quality
- **Status:** FIXED (Batch 4) — typed-words/cursor hidden via CSS
- **Description:** Template has a typewriter JS effect that cycles text. In rendered preview, produces "differenzaB|" or "differenzaStar|" concatenation artifact. The cursor character "|" and partial next word get appended.
- **Notes:** This is a JS timing artifact. The typewriter script cycles through an array of words; the injected pool text and original text get concatenated in the DOM. Would need typewriter-specific handling in the pipeline.

### TMPL-002 — agency-ironquill: no hero image, excessive whitespace
- **Severity:** Medium
- **Category:** Layout
- **Status:** FIXED (Batch 4) — Unsplash bg injected via PASS 6, padding 112→64px
- **Description:** Template has a plain beige split-background hero with no image. Multiple sections have excessive vertical spacing, making the page look sparse and unprofessional.
- **Notes:** Original template design is minimal; the premium CSS layer's hero image replacement may not have matching selectors for this template's hero structure.

### TMPL-003 — agency-fluxwork: invisible sections mid-page
- **Severity:** HIGH → FIXED
- **Category:** Layout
- **Status:** FIXED (Batch 4) — ftco-animate override shows all 36 hidden elements
- **Description:** Full-page screenshot shows hero at top, then massive empty gray/white space, then a small grayscale image near bottom. Multiple sections appear invisible or collapsed.
- **Notes:** May be caused by CSS conflicts between template's original styles and injected premium layer. Needs per-section DOM inspection.

### TMPL-004 — agency-vantage: hero text overlap
- **Severity:** Low
- **Category:** Visual quality
- **Status:** FIXED (Batch 4) — .text-wrap margin-top:0, position:relative
- **Description:** Hero area has overlapping text layers — heading "Esperienze premium, offerte con cura" overlaps with subtitle text "Qualità, precisione e fiducia in ogni dettaglio."
- **Notes:** Carousel/slider positioning conflict.

### TMPL-005 — agency-vantage: placeholder nav labels
- **Severity:** Low
- **Category:** Translation
- **Status:** FIXED (Batch 3)
- **Description:** Nav showed "Dropdown" and "Inner Page" — generic template placeholder labels. Added translations to translation_map.py.

### TMPL-006 — agency-emberlane: English service category names in dropdown
- **Severity:** Low
- **Category:** Translation
- **Status:** Identified
- **Description:** Dropdown shows "HR Consulting", "Leadership Training", "IT Management", "Corporate Management", "Corporate Program" — these are original template content not in the translation dictionary.
- **Notes:** These are domain-specific terms; some may be acceptable anglicisms in IT/FR.
