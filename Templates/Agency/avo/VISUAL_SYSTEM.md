# Nøva Creative — Visual System

Reference document for the Agency/avo template visual identity (Nøva Creative brand).

## Color Palette

| Token | Hex | CSS Variable | Usage |
|-------|-----|-------------|-------|
| Primary dark | `#1a1a2e` | `--av-primary` | Headings, hero bg overlay, footer bg tint |
| Accent | `#e94560` | `--av-accent` | CTA buttons, hover states, active nav, icons, links |
| Accent dark | `#c73a52` | `--av-accent-dark` | Button hover |
| Accent light | `#f5c6d0` | `--av-accent-light` | Secondary hover |
| Neutral warm | `#f8f7f4` | `--av-neutral-warm` | Section backgrounds (bg-light) |
| Neutral mid | `#eaeaea` | `--av-neutral-mid` | Borders, separators |
| Text dark | `#2d2d3a` | `--av-text-dark` | Headings, card titles |
| Text body | `#6e6e80` | `--av-text-body` | Paragraphs |
| Text muted | `#9e9eae` | `--av-text-muted` | Meta info, secondary text |
| White | `#ffffff` | `--av-white` | Hero text, button text |
| Footer bg | `#16162a` | `--av-footer-bg` | Footer background |
| Footer bar | `#111122` | `--av-footer-bar` | Footer bottom bar |

### Color Rules
- Accent `#e94560` is the primary action color (NOT the original `#d1002c`)
- Primary dark `#1a1a2e` for headings and dark sections
- Never use the original template red `#d1002c`
- All accent uses go through CSS custom properties

## Typography

| Role | Font | Weight | Size |
|------|------|--------|------|
| Hero title | Sora | 800 | 40px (responsive: 28px mobile) |
| Section title (h2) | Sora | 700 | inherit |
| Page title (bread) | Sora | 700 | inherit |
| Card title (h3) | Sora | — | 18-20px |
| Team name | Sora | 900 | 18px uppercase |
| Footer heading | Sora | 600 | 18px |
| Subheading | Inter | 600 | 13px, 0.15em tracking, uppercase |
| Body text | Inter | 400-500 | 14-16px |
| Nav links | Inter | inherited | inherited |
| Button text | Inter | 600 | 13px, 0.08em tracking, uppercase |
| Brand name | Sora | 700 | 22px (responsive: 16px mobile) |

### Typography Rules
- **Sora**: headings only (h1-h3, brand, team names, footer headings)
- **Inter**: everything else (body, nav, buttons, subheadings, meta)
- Both loaded via `@import` in `avo-shared.css`
- Original font Nunito Sans remains as fallback

## Button System

### Primary (`.btn.btn-primary`)
- Background: `#e94560`, border: same
- Text: white, 13px, 600 weight, uppercase, 0.08em tracking
- Border-radius: 6px
- Hover: `#c73a52`, translateY(-1px), box-shadow `0 6px 20px rgba(233,69,96,0.3)`
- Override: 7x repeated class selector to beat PreviewEngine

### Custom Button (`.custom-btn`)
- Text link style with bottom border
- Color: accent, 13px, 600 weight, uppercase
- 7x selector override applied

### Submit Button
- Same as primary, applied via `input[type="submit"].btn.btn-primary` 7x selector

## Section Patterns

### Home Hero (Owl Carousel slider)
- Full-width background images (external Pexels URLs)
- Overlay: `linear-gradient(135deg, rgba(26,26,46,0.75) 0%, rgba(233,69,96,0.2) 100%)`
- Counter badge (top-right): accent red bar, white number
- Sora 800 title, Inter body text
- Primary CTA button + video play button (accent circle with pulse animation)

### Inner Page Hero (`.hero-wrap-2`)
- Background image with gradient overlay
- Breadcrumbs with accent chevron icons
- Sora 700 page title (no uppercase forced)
- Height: 600px

### Services Icons Grid
- 5-column grid on desktop
- Square icons: 70px, border-radius 16px, accent background
- Flaticon custom font icons in white

### Portfolio (alternating layout)
- Alternating left/right image + text blocks
- Background-image divs (50/50 split)
- Accent subheading, Sora project title, Inter description
- Team member avatar + role below

### Team Section
- 4-column grid (8 members, 2 rows)
- Background-image portraits (400x500)
- Social icons overlay on hover (accent color)
- Sora name (uppercase), accent role text

### Testimonials (Owl Carousel)
- Quote icon in accent
- Sora name, muted position
- Circular avatar (80px)
- Active dot: accent color

### CTA Band
- Full-width background image with rounded corners (12px)
- Accent subheading, white heading
- Primary button

### Blog Cards
- 4-column grid, background-image thumbnails (270px height)
- Sora title, muted meta, Inter description

### Footer
- Dark background `#16162a`
- 5-column: brand + services + azienda + link utili + contatti
- Social icons with border, accent on hover
- Degree shape dividers at top

## CSS Architecture

```
All pages → css/style.css (Bootstrap 4.5 + template custom styles)
         → css/avo-shared.css (Nøva Creative premium overrides)
         → css/animate.css, owl.carousel, magnific-popup, flaticon
```

### File Responsibilities
- `style.css` — Original Bootstrap 4.5 + all template layout/component styles (10190 lines, monolithic)
- `avo-shared.css` — Premium override layer: palette, typography, brand classes, button 7x overrides, section styling, responsive

### Safe CSS Class Prefix
- `av-` prefix for all custom brand elements
- **Safe**: `av-brand`, `av-brand-accent`
- **Avoid**: `logo`, `navbar-brand` (alone), `site-title`, `brand-name`, `brand`, `subtitle`, `tagline`

## PreviewEngine Workarounds

| Issue | Workaround | Applied in |
|-------|-----------|------------|
| Image replacement | Direct Pexels `https://` URLs | All HTML files |
| Link color override | 7x repeated class selectors | avo-shared.css |
| Button pill shape | 7x repeated button selectors | avo-shared.css |
| Nav text replacement | None — known engine behavior | Accepted |
| Brand name clobbering | `av-` prefix classes | HTML + avo-shared.css |
| Counter NaN | Monitor — skip list if needed | Not yet needed |

## Responsive Breakpoints

| Width | Changes |
|-------|---------|
| 991px | Mobile: brand 18px, hero title 28px |
| 767px | Smallest: brand 16px, hero title 22px, stacked columns |

## JS Dependencies

- jQuery 3.x + jQuery Migrate 3.0.1
- Bootstrap 4.5 (JS bundle via popper.min.js + bootstrap.min.js)
- Owl Carousel (hero slider, testimonials)
- Magnific Popup (video lightbox)
- jQuery Waypoints + animateNumber (hero counters)
- jQuery Stellar (parallax on inner heroes)
- Scrollax (scroll effects)
- Google Maps API (contact page — requires API key)
