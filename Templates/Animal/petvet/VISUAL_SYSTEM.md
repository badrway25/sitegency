# VISUAL SYSTEM — ZampaCura (Animal/petvet)

Template pilota #3 per Sitegency. Verticale: veterinaria/animali.

## Brand

| Campo | Valore |
|-------|--------|
| Nome | **ZampaCura** |
| Tagline | Centro Veterinario |
| Locale | Italiano |
| Citta | Torino |
| Indirizzo | Corso Re Umberto 42, 10128 Torino |
| Telefono | +39 011 234 5678 |
| Email | info@zampacura.it |
| CSS prefix | `zc-` |

## Palette

| Token | Hex | Uso |
|-------|-----|-----|
| `--zc-primary` | `#2d6a4f` | Verde salvia — CTA, accenti, icone |
| `--zc-accent` | `#e9c46a` | Warm gold — bottoni secondari, dettagli premium |
| `--zc-dark` | `#1b2a1f` | Verde scurissimo — headings, hero overlay, footer bg |
| `--zc-body` | `#4a5a4e` | Grigio-verde — testo body |
| `--zc-light-bg` | `#f7f5f0` | Bianco caldo — sezioni alternate (bg-light) |
| `--zc-white` | `#ffffff` | Bianco puro |
| `--zc-hero-overlay` | `rgba(27,42,31,0.55)` | Overlay hero scuro |

## Tipografia

| Ruolo | Font | Peso | Sorgente |
|-------|------|------|----------|
| Headings | **Lora** | 600-700 | Google Fonts via @import |
| Body | **DM Sans** | 300-700 | Google Fonts via @import |
| Subheadings | DM Sans | 600, uppercase, letter-spacing 2px | |
| Brand name | Lora | 700, 22px | |
| Brand subtitle | DM Sans | 11px, uppercase, 1.5px spacing | |

## Pagine (8)

| File | Titolo | Sezioni chiave |
|------|--------|----------------|
| `index.html` | Home | Hero fullheight, servizi intro, about, form, team, testimonials, pricing, blog |
| `about.html` | Chi Siamo | Hero, about, counters (30/4500/400/3000), testimonials |
| `services.html` | Servizi | Hero, form, 7 servizi card |
| `groomer.html` | Il Team | Hero, form, 8 veterinari |
| `blog.html` | Blog | Hero, 6 card articoli |
| `blog-single.html` | Articolo | Hero, articolo, sidebar, commenti |
| `pricing.html` | Tariffe | Hero, form, 4 card pricing (EUR) |
| `contact.html` | Contatti | Hero, info cards, form, mappa |

## Framework & Dipendenze

- **Bootstrap 4.5.0** — compilato in `css/style.css`
- **jQuery 3.x** + Migrate 3.0.1
- **Owl Carousel** — testimonials
- **jQuery Waypoints** — scroll-triggered animations
- **jQuery animateNumber** — counters
- **Magnific Popup** — lightbox
- **Bootstrap Datepicker** + **jQuery Timepicker** — form appuntamento
- **Animate.css** — CSS animations
- **Font Awesome 4.7** — icone generali
- **Flaticon** — icone pet-specific (stethoscope, pet, cat, house, veterinary, dog-training, dog)
- **Google Maps API** — pagina contatti (richiede API key)

### Plugin DISABILITATI (prevenzione jank)
- **jQuery Stellar** — parallax commentato in `main.js`, `data-stellar-background-ratio` rimosso da tutti gli HTML
- **Scrollax** — `$.Scrollax()` commentato in `main.js`

## Pattern CSS

File condiviso: **`css/petvet-shared.css`** (~380 righe)

### Specificita (PreviewEngine bypass)
- 7x repeated class selectors per `.btn-primary`, `.btn-secondary`, `.nav-item.cta > a`
- Brand classes safe: `zc-brand`, `zc-brand-accent`, `zc-footer-logo`
- CSS custom properties (`--zc-*`) per palette centralizzata

### Struttura override
```
@import Google Fonts (DM Sans + Lora)
:root variables
Typography (body, headings, subheadings)
Navbar brand (zc-brand, mobile, scrolled)
Links (engine override)
CTA buttons (7x selector)
Primary/secondary buttons (7x selector)
Hero sections (overlay, text)
Services (icon color, hover)
About/counters
Appointment form
Staff/groomers
Testimonials
Pricing cards
Blog cards
Footer (dark theme, logo, links)
Contact section
Utilities (loader, owl dots, pagination, sidebar, selection, bg-light)
```

## Strategia Immagini

**Tutte le immagini critiche usano URL Pexels diretti** (`https://images.pexels.com/...`) per bypassare la sostituzione automatica del PreviewEngine, che skippa URL che iniziano con `http://` o `https://`.

| Zona | URL Pexels | Dimensione |
|------|-----------|------------|
| Hero (tutte le pagine) | 6235233 | 1920px |
| About section | 6235241 | 800px |
| Testimonials bg | 1170986 | 1920px |
| Team (4 in index) | 5452201, 5452293, 6234600, 5452268 | 400px |
| Team (4 extra in groomer) | 5327585, 5215024, 5452205, 5452196 | 400px |
| Pricing cards | 1904105, 1909802, 2253275, 1629781 | 400px |
| Blog cards | 1378849, 2607544, 1805164, 2253275, 1629781, 1904105 | 400px |
| Testimonial avatars | 774909, 220453, 415829 | 100px |
| Contact image | 6235241 | 800px |
| Blog article images | 1805164, 2253275 | 800px |
| Author avatar | 5452201 | 100px |

## Workaround PreviewEngine

| Problema | Impatto | Workaround |
|----------|---------|------------|
| Brand injection su `.navbar-brand` | Alto | Classe `zc-brand` + CSS 7x selectors |
| Pill shape su `.btn-primary`/`.btn-secondary` | Medio | CSS 7x selectors con `border-radius: 4px !important` |
| Sostituzione immagini locali | Alto | URL Pexels diretti (engine skippa https://) |
| Link color override | Medio | CSS override con `var(--zc-primary)` |
| Footer `.logo` class targeting | Medio | Classe `zc-footer-logo` |
| Counter text replacement | Basso | Valori in `data-number`, monitorare |
| Google Maps blank | Basso | Accettabile in preview |

## File Modificati

### HTML (8 pagine)
- `index.html` — rebrand completo + immagini Pexels
- `about.html` — rebrand + counters italiani + immagini
- `services.html` — rebrand + 7 servizi italiani
- `groomer.html` — rebrand + 8 veterinari italiani
- `blog.html` — rebrand + 6 articoli italiani
- `blog-single.html` — rebrand + articolo italiano + sidebar
- `pricing.html` — rebrand + 4 piani EUR
- `contact.html` — rebrand + contatti Torino

### CSS
- `css/petvet-shared.css` — NUOVO, override condiviso

### JS
- `js/main.js` — Stellar + Scrollax disabilitati

### Docs
- `adapter.yaml` — mapping completo per customizer
- `VISUAL_SYSTEM.md` — questo file
