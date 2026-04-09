# Premium Audit Master Plan

## Project Objective
Transform the Sitegency marketplace and its 192 template previews into a genuinely ultra-premium, multilingual, RTL-correct, visually coherent product.

## Definition of Done
A template or shared page is "done" ONLY when ALL of:
- Visually inspected in a real browser with full scroll
- Navbar verified (desktop + mobile, all links present and functional)
- All 4 locales verified visually (IT/FR/EN/AR)
- RTL verified for Arabic
- Brand replacement verified (no old brand traces)
- Logo replaced with generated SVG
- Images verified as premium, coherent, correctly proportioned
- No blocking JS console errors
- No untranslated buttons/labels/CTAs
- Design judged as genuinely premium (not "merely functional")
- Audit status file updated with evidence

## Evidence Rules
- "verified" = inspected in rendered browser, screenshot or DOM check performed
- "partially verified" = some aspects checked, others remain
- "structurally improved" = code changed, not visually confirmed
- "not verified" = no inspection performed
- Every claim must cite files changed, selectors affected, or checks performed
- Global completion claims (100%, done, fixed) are FORBIDDEN without per-item evidence

## Verification Categories
1. Structure (sections, layout, scroll)
2. Navbar (desktop, mobile, links, dropdowns)
3. Visual quality (balance, spacing, typography, cards, buttons)
4. Images (quality, proportions, coherence)
5. Branding (old brand removed, new applied)
6. Languages (IT, FR, EN, AR — each separately)
7. Arabic/RTL (direction, alignment, forms, cards)
8. Preview/Customizer (language sync, direction sync)
9. JS/Runtime (console errors, interactions)
10. Premium judgment (elegant, commercial-grade, above default)

## Phase Plan

### Phase 1 — Shared architecture and systemic stability
- [ ] Audit language handling (i18n middleware, get_language, locale prefix)
- [ ] Audit lang/dir handling in templates and previews
- [ ] Audit language switcher reliability
- [ ] Audit preview/customizer language sync
- [ ] Audit RTL foundations (_inject_rtl method)
- [ ] Identify systemic blockers affecting multiple templates
- [ ] Fix top blockers

### Phase 2 — Shared premium foundation
- [ ] Audit global design tokens (CSS custom properties)
- [ ] Audit global layout rhythm (section spacing, padding)
- [ ] Audit global navbar quality
- [ ] Audit card/button/form system
- [ ] Audit typography hierarchy
- [ ] Audit premium surfaces (shadows, borders, motion)
- [ ] Audit shared RTL-safe CSS
- [ ] Fix top issues

### Phase 3 — Core shared pages (marketplace shell)
- [ ] Homepage (layout, hero, features, translations, RTL)
- [ ] Categories listing
- [ ] FAQ page
- [ ] Contact page
- [ ] Template listing
- [ ] Template detail page

### Phase 4 — Template family work (192 templates)
Process by category family. Track each template individually in template_audit_status.json.

### Phase 5 — Hard exceptions and final QA
- Broken navbar edge cases
- Broken preview edge cases
- Broken RTL edge cases
- Image quality outliers
- Visual quality outliers

---

## Premium Design System (v1 — extracted from Agency family, Batches 3-6)

This system defines the visual standard applied to ALL 192 template previews. It is injected via `_inject_differentiation_layer()` in `customizer/services.py`.

### DS-1: Token System (CSS Custom Properties)

```
--sg-hue       Per-template deterministic primary hue (12 options)
--sg-hue2      Golden-ratio offset (+137°) for complementary harmony
--sg-hue3      Triadic offset (+60°)
--sg-accent    hsla(hue, 72%, 55%, 1)   — primary accent
--sg-accent2   hsla(hue2, 60%, 55%, 1)  — secondary accent
--sg-accent-dark   darker variant for hover/active
--sg-accent-light  lighter variant for backgrounds
--sg-accent-glow   glow variant for shadows
--sg-grad-accent   linear-gradient(135deg, accent, accent2)
--sg-shadow-sm/md/lg/xl  4-tier shadow system
```

Every template gets a UNIQUE but harmonious dual-hue color scheme. No random template colors should leak through.

### DS-2: Typography

| Element | Font | Size | Weight | Notes |
|---------|------|------|--------|-------|
| body | Plus Jakarta Sans | 1rem | 400 | line-height: 1.7 |
| h1 | Playfair Display | clamp(1.8rem, 4vw, 3.2rem) | 800 | Serif for drama |
| h2 | Playfair Display | clamp(1.5rem, 3vw, 2.4rem) | 700 | Accent color, accent bar |
| h3 | Plus Jakarta Sans | clamp(1.15rem, 2vw, 1.5rem) | 700 | Sans for readability |
| h4-h6 | Plus Jakarta Sans | inherited | 600 | Utility headings |
| p | Plus Jakarta Sans | inherited | 400 | line-height: 1.75 |
| nav links | Plus Jakarta Sans | 15px | 500 | NOT Playfair |

### DS-3: Navbar System

| Property | Value | Enforcement |
|----------|-------|-------------|
| Height | max-height: 80px | All templates |
| Position | sticky, top: 0 | All templates |
| Background | rgba(255,255,255,0.88) | Glassmorphism |
| Blur | backdrop-filter: blur(16px) saturate(180%) | All templates |
| Shadow | 0 1px 24px rgba(0,0,0,0.06) | Subtle depth |
| Link font | Plus Jakarta Sans, 15px, 500 | Overrides Playfair |
| Overflow | hidden | Prevents tall nav leak |

**Known exceptions:** Some templates use absolute positioning (emberlane) or unique sidebar nav (parallax). These still function correctly.

### DS-4: Hero System

| Property | Value | Notes |
|----------|-------|-------|
| Overlay | Mesh gradient (::before) with 3 radial gradients | Animated drift, 15s cycle |
| Grain | SVG noise texture (::after) | mix-blend-mode: overlay, 0.7 opacity |
| Min-height | auto | Prevent whitespace inflation |
| Max-height | 75vh | Prevent oversized heroes |
| Content z-index | 3 | Above overlay (z:1) and grain (z:2) |
| Images | PASS 6 injects bg-image on empty heroes | Fallback for templates with no hero image |

Hero selectors: `.hero-wrap, .hero-section, section.hero, #hero, .banner-area, .slider-area, .home-slider, .banner, .jumbotron, .main-banner, .page-header, [class*="blocks-cover"]`

### DS-5: Card System

| Property | Value | Notes |
|----------|-------|-------|
| Border-radius | 16px (feature), 14px (blog), 12px (portfolio) | Tiered by context |
| Box-shadow | 0 4px 24px rgba(0,0,0,0.06) | Resting state |
| Hover shadow | 0 16px 48px rgba(0,0,0,0.10) | Elevated state |
| Hover transform | translateY(-6px) | Lift effect |
| Background | rgba(255,255,255,0.85) or #fff | Semi-transparent or solid |
| Transition | 0.35s cubic-bezier(0.22,1,0.36,1) | Smooth easing |

Card selectors: `[class*="feature-"], [class*="service-box"], .media-body, .blog-entry, .post-entry, .blog-card, .card, .pricing-box, .testimonial-item`

### DS-6: Button/CTA System

| Type | Properties | Notes |
|------|-----------|-------|
| Primary (.btn) | Gradient bg, 50px radius, 14px/600, uppercase | Pill shape |
| Text-link CTA | Gradient bg, 50px radius, 14px 32px padding | Transforms bare links |
| Hover | translateY(-2px), increased shadow glow | Lift + glow |
| Shadow | 0 4px 15px hsla(hue, 70%, 50%, 0.35) | Accent-colored shadow |

CTA selectors: `a[class*="more-"], a.read-more, a[class*="btn-link"], .btn`

### DS-7: Image System

| Property | Value | Notes |
|----------|-------|-------|
| Border-radius | 10px | ALL content images |
| Hover transform | scale(1.03) | Subtle zoom |
| Hover shadow | 0 12px 40px rgba(0,0,0,0.12) | Depth on hover |
| Transition | 0.4s cubic-bezier(0.22,1,0.36,1) | Smooth |

**Exempt:** nav/header images, icons, logos, SVGs, 1x1 tracking pixels.
Selectors: `section img, .container img, [class*="col-"] img, .row img`

### DS-8: Footer System

| Property | Value |
|----------|-------|
| Background | linear-gradient(180deg, rgb(17,24,39), rgb(7,10,18)) |
| Text color | rgba(255,255,255,0.75) |
| Heading color | #fff |
| Link color | hsla(hue, 70%, 70%, 1) — accent-tinted |
| Social icons | rgba(255,255,255,0.08) bg, 1px white/10% border |
| Padding | 64px top, 40px bottom |
| Border-top | 1px solid rgba(255,255,255,0.06) |

Selectors: `.site-footer, .ftco-footer, footer.footer, footer[class*="footer"], .footer-area`

### DS-9: Section Rhythm

| Property | Value | Notes |
|----------|-------|-------|
| Padding | 64px top/bottom | Replaces excessive 100-112px |
| Alternating bg | Subtle gradient on :nth-child(even) | Visual rhythm |
| H2 accent bar | 48px x 3px gradient bar via ::before | Above every section heading |
| H2 color | hsla(hue, 72%, 45%, 1) | Consistent accent |

### DS-10: Visibility Overrides

| Override | Selectors | Why |
|----------|-----------|-----|
| ftco-animate | `.ftco-animate, .animate-box, [data-animate-effect], .wow` | jQuery Waypoints never fires in iframe |
| Typed.js | `.typed-words, .typed-cursor` | English typewriter text not translatable |
| Placeholder nav | "Menu One", "Sub Menu", "Deep Drop Down" | Template demo content |
| Mobile overflow | `html, body { overflow-x: hidden }` | Prevents horizontal scroll |

### DS-11: Color Leak Prevention

Any original template accent color that doesn't match the premium hue system must be overridden:
- `rgb(255, 99, 99)` → premium accent
- `[style*="color: rgb(255, 99"]` → forced to accent
- `.post-meta` date labels → forced to accent
- Dollar pricing ($) → hidden or converted to euro for IT/FR

### DS-12: RTL (Arabic)

- `dir="rtl"` on `<html>` element
- Noto Kufi Arabic font injected
- Surgical CSS: logical properties only, NO global text-align forcing
- Icon content remapping for directional icons

---

## Premium-Ready Checklist (apply to EVERY template)

A template is premium-ready when ALL of the following are true:

### Mandatory (blocking)
- [ ] All 4 locales render without errors (EN, IT, FR, AR)
- [ ] NaN count = 0
- [ ] No untranslated English in nav/buttons/CTAs for non-EN locales
- [ ] Navbar visible and functional on desktop
- [ ] Hamburger toggle visible on mobile (375px)
- [ ] No horizontal overflow on mobile
- [ ] Footer present and dark-styled
- [ ] SVG logo or brand text present
- [ ] RTL correct for Arabic (dir=rtl, mirrored layout)
- [ ] No garbled brand text (word-boundary replacement working)

### Quality (should-have)
- [ ] Hero section has image or gradient background (not blank)
- [ ] Images have border-radius: 10px
- [ ] Cards/features have shadow and hover elevation
- [ ] H2 headings in accent color with accent bar
- [ ] Section spacing is consistent (not 100px+ padding)
- [ ] No original template accent colors leaking
- [ ] CTAs styled as pill buttons (not bare text links)
- [ ] Overall visual impression: "would pass as a real commercial site"

### Evidence required
- [ ] Desktop screenshot (1280x800) in IT locale
- [ ] Mobile screenshot (375x812) in IT locale
- [ ] FR locale browser-verified
- [ ] AR locale browser-verified (RTL check)

---

## Scaling Rules (for Business family and beyond)

### Before starting a new family
1. Run all templates in the family through `PreviewEngine.render()` — verify 0 errors
2. Take IT desktop screenshots of all templates
3. Identify which systemic fixes already improved them (ftco-animate, typed.js, etc.)

### Per-template process
1. Browser-verify IT locale (full scroll, all sections)
2. Check against Premium-Ready Checklist above
3. Fix any failing items
4. If original template design is too basic → apply aggressive CSS upgrades
5. Verify FR and AR locales
6. Verify mobile viewport
7. Update audit status

### After completing a family
1. Consistency pass across all templates in the family
2. Cross-check against Agency family standards (DS-1 through DS-12)
3. Document any family-specific issues or exceptions
4. Mark family as complete only when ALL templates are premium-ready

### What constitutes a regression
- Any template that previously passed now fails a checklist item
- NaN appearing where it was 0
- Mobile overflow appearing
- Missing footer or navbar
- Garbled brand text
- Untranslated English in previously-translated elements

---

## DS Validation Log (Batch 8 — Business family sample)

### Validated on: business-meridia, business-north-bureau, business-prime-office

### Rules that work reliably across families
DS-1, DS-2, DS-3, DS-5, DS-8, DS-9, DS-10, DS-12 — no adjustment needed when applied to Business templates.

### Rules that required refinement
- **DS-4 (Hero PASS 6)**: Was too conservative — checked child elements for bg-images. Carousel children have bg-images but they aren't visible in the hero viewport. Fix: only check the hero element itself.
- **DS-11 (Color Leaks)**: Only caught red `rgb(255,99,99)`. Business templates leaked green `rgb(49,222,121)`. Fix: added green accent override. **Note:** each template family may have its own accent color to override.

### Known DS limitations
- **DS-7 (Images)**: Only applies to `<img>` tags. Colorlib templates using CSS `background-image` divs (meridia, fluxwork) get 0/0 rounded images. Not fixable with CSS alone — the images render fine but don't get hover effects.
- **DS-11 (Color Leaks)**: Class-based overrides are semi-specific. New accent colors discovered in each family need to be added to the override list.
- **DS-3 (Navbar)**: Some templates resist the 80px max-height (emberlane at 161px, prime-office at 100px). The nav IS functional — this is a cosmetic inconsistency.
