# Medilux Visual System

Reference document for the Medilux medical template visual identity.
Use this as a pattern when building other premium templates.

## Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| Navy | `#111d2e` | Primary: headings, hero bg, buttons, CTA bars, footer bg accent |
| Navy light | `#1e3048` | Hover state for navy buttons |
| Navy deep | `#1a2740` | Brand monogram border |
| Gold | `#b09560` | Accent: subtitles, active nav underline, location titles, `LUX` brand text |
| Warm neutral | `#f9f8f5` | Section backgrounds (before/after, price cards) |
| Text body | `#6b7280` | Paragraph text, intro text |
| Text muted | `#828282` | Secondary body text |
| Text heading | `#404040` | Original heading color (overridden to navy for Playfair headings) |
| White | `#ffffff` | Hero text, button text, footer titles |
| Footer bg | `#26292d` | Footer background |
| Footer bar | `#181a1d` | Footer bottom bar |
| Selection | `rgba(17,29,46,0.75)` | Text selection highlight (navy) |

### Color Rules
- **Never use** teal (`#57ccc3`), coral (`#ffa07f`), or pink — these are old template colors
- Gold is always accent, never primary
- Navy is the dominant brand color
- Neutrals use warm tones (`#f9f8f5`) not cold grays

## Typography

| Role | Font | Weight | Size | Tracking |
|------|------|--------|------|----------|
| Hero title (inner pages) | Playfair Display | 700 | 50px | -0.01em |
| Hero title (home) | Playfair Display | 700 | 52px | -0.01em |
| Section title (h2) | Playfair Display | — | 48px | — |
| Section subtitle | Montserrat | 600 | 11px | 0.2em |
| Service/price card title | Playfair Display | 600 | 20-22px | — |
| Nav links | Montserrat | 600 | 11.5px | 0.12em |
| Body text (p) | Montserrat | 500 | 14px | — |
| Brand name | Playfair Display | 700 | 21px | 0.12em |
| Brand label | Montserrat | 500 | 9px | 0.22em |

### Typography Rules
- Playfair Display: **headings only** (h1-h3, card titles, testimonial quotes)
- Montserrat: **everything else** (body, nav, subtitles, buttons)
- Section subtitles: gold, uppercase, tracked, 11px
- Section titles: navy, Playfair, no uppercase
- `@import` for Playfair is in each inner page CSS + HTML `<link>` preconnect

## Button System

### Primary (`.button_1`, `.ba_button`)
- Background: navy `#111d2e`, border: same
- Text: white, 12px, 600 weight, uppercase, 0.1em tracking
- Height: 50px, border-radius: 5px
- Hover: lighter navy `#1e3048`, slight lift (`translateY(-1px)`), subtle shadow

### Secondary (`.button_2`)
- Background: transparent, border: 2px solid navy
- Text: navy, same typography as primary
- Hover: fill navy, text white

### Newsletter button
- Same 5px radius, 12px uppercase
- Positioned absolute inside form container

### CTA Phone
- White background, navy text, 5px radius

### PreviewEngine Override Technique
The engine injects `a:not(.btn):not(.button):not(.nav-link)...` with specificity `0,6,1`.
Use **7x repeated class selectors** to reach `0,7,1`:
```css
.button_1.button_1.button_1.button_1.button_1.button_1.button_1 a {
    color: #ffffff !important;
}
```
For `<button>` elements, the engine injects `border-radius: 999px !important`.
Use the same technique with `button.classname.classname...` (7x).

## Section Patterns

### Inner Page Hero (solid navy)
- Solid navy `#111d2e` background, no parallax, no overlay image
- Playfair title in white, gold accent line via `::before` (48px wide, 2px tall)
- Subtitle text in `rgba(255,255,255,0.55)`
- Padding: 88px top (for fixed header), 96px+72px content area
- All `.parallax_background`, `.background_image`, `.home_overlay` → `display: none`

### Home Page Hero (split layout)
- Two-column: warm neutral left (52%) + full-bleed image right
- Badge line with gold left-rule (24px line + `0.22em` tracked uppercase)
- Playfair title 52px, body text in `#6b7280`
- Primary CTA + secondary link with arrow icon

### Service Cards
- Icon in navy circle (61px, centered)
- Playfair title 20px, navy
- Body text in `#828282`
- 6 per section (3x2 grid via `col-xl-4 col-md-6`)

### Price Cards
- Gold left border (3px solid `#b09560`)
- Warm neutral background (`#f9f8f5`)
- Navy price badge floated top-right (absolute, `border-radius: 4px`)
- Playfair title, Montserrat description

### Testimonials (about page)
- Dark navy background (`#111d2e`)
- Gold subtitle, white heading
- Playfair italic quotes in `rgba(255,255,255,0.7)`
- Gold owl-carousel dots

### Navbar (ml-hdr)
- Utility bar: navy bg, small text, social icons
- Main nav: white bg, Playfair monogram logo, Montserrat nav links
- Phone block with label + number
- Navy CTA button with arrow
- Scrolled: topbar hides, nav compresses to 72px

### Footer
- Dark bg (`#26292d`), gold accents on location titles
- 4-column: about + contacts + locations + hours
- Bottom bar: `#181a1d`

## CSS Architecture

```
index.html   → main_styles.css + responsive.css
about.html   → main_styles.css + responsive.css + about.css   + medilux-shared.css + about_responsive.css
services.html→ main_styles.css + responsive.css + services.css + medilux-shared.css + services_responsive.css
blog.html    → main_styles.css + responsive.css + blog.css     + medilux-shared.css + blog_responsive.css
contact.html → main_styles.css + responsive.css + contact.css  + medilux-shared.css + contact_responsive.css
```

### File Responsibilities
- `main_styles.css` — Home page layout, navbar/topbar (`ml-*`), brand identity, home hero split, footer
- `{page}.css` — Full standalone page styles (base resets + page-specific sections)
- `medilux-shared.css` — **Shared overrides** for all inner pages: hero, header hide, buttons, newsletter, PreviewEngine 7x overrides
- `{page}_responsive.css` — Responsive breakpoints per page
- `responsive.css` — Home page responsive breakpoints

### Safe CSS Class Prefixes
- `ml-` prefix for custom brand elements (avoids PreviewEngine targeting)
- **Avoid**: `logo`, `navbar-brand`, `site-title`, `brand-name`, `brand`, `subtitle`, `tagline`
- **Safe**: `ml-brand`, `ml-brand-mark`, `ml-brand-name`, `ml-clinic-label`, `ml-hdr`, `ml-topbar`, `ml-cta`

## PreviewEngine Workarounds

| Issue | Workaround | Applied in |
|-------|-----------|------------|
| Image replacement | Use direct external URLs (pexels.com/unsplash) — engine skips `https://` | Hero images |
| Link color override | 7x repeated class selectors (specificity 0,7,1) | medilux-shared.css |
| Button pill shape | 7x repeated `button.class.class...` selectors | medilux-shared.css |
| Nav text replacement | None — engine replaces active page nav text | Known issue, no fix |
| Raw HTML in hero | `font-size: 0; color: #111d2e` on `.home`, restore on `.home_container` | Inner page CSS |
| Brand name clobbering | Use `ml-` prefix class names, avoid engine-targeted selectors | HTML templates |
| Mobile menu dedup | Use `<div role="navigation">` instead of `<nav>` for mobile menu | HTML templates |

## Responsive Breakpoints

| Width | Changes |
|-------|---------|
| 1280px | Hide phone block, compact brand spacing |
| 1199px | Compact CTA, hide arrow, reduce hero title |
| 991px | **Mobile**: hide nav/CTA/phone, show hamburger, stack columns |
| 767px | Smaller hero title (34-38px), stack footer bar |
| 575px | Smallest: 30px title, compact brand, smaller buttons |
