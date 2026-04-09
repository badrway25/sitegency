# KNOWN ISSUES

## PreviewEngine (sistemici — affliggono tutti i template)

### Image Replacement
- **What**: `_replace_hero_images` sostituisce TUTTE le URL immagini locali (tag `<img>` e CSS `background-image`) con foto Unsplash dal content pool.
- **Impact**: Le immagini hero locali non appaiono in preview.
- **Workaround**: URL esterne dirette (Pexels `https://images.pexels.com/...`) — il motore salta URL che iniziano con `http://` o `https://`.
- **Location**: `customizer/services.py` ~linee 3308-3570, `should_skip_img()` ~linea 3358.

### Link Color Override
- **What**: Engine inietta `a:not(.btn):not(.button):not(.nav-link):not([class*="social"]):not([class*="navbar"]):not([class*="menu"]) { color: var(--sg-accent) !important; }` con specificita 0,6,1.
- **Impact**: Testo link nei bottoni diventa blu invece di bianco.
- **Workaround**: 7x repeated class selectors (specificita 0,7,1). Applicato in `medilux-shared.css` per tutti i bottoni.

### Button Pill Override
- **What**: Engine inietta `button:not([class*="close"]):not([class*="toggle"])... { border-radius: 999px !important; }`.
- **Impact**: Tutti i `<button>` diventano pill.
- **Workaround**: 7x repeated `button.class.class...` selectors. Applicato in `medilux-shared.css`.

### Nav/Hero Text Replacement
- **What**: Engine sostituisce il testo del link nav attivo e talvolta il titolo hero con il nome del template.
- **Impact**: "Servizi" diventa "MEDILUX" nella nav e "I Nostri Servizi" diventa "I Nostri Medilux" nell'hero.
- **Workaround**: Nessuno trovato. Comportamento sistemico del motore. Non affligge i file raw del template.

### Raw HTML Text in Hero
- **What**: Engine talvolta inietta un nodo di testo con markup HTML raw visibile nell'hero.
- **Workaround**: `font-size: 0; color: #111d2e;` su `.home`, poi restore `font-size: 14px` su `.home .home_container`.

## Template-specific (Medilux)

### "Why" Section Image Bleed (Home Page)
- **What**: `.why_image` usa `position: absolute; bottom: 0; right: 0;` — immagine deborda nella sezione sopra.
- **Impact**: Overlap visivo nella home page, sezione intro.
- **Severity**: Medium. Pre-existing layout issue.

### Home Page `.button_1` Pill Shape
- **What**: Nella home page, `.button_1` in alcune sezioni body prende `border-radius: 999px` dal PreviewEngine. Il CTA hero (`.ml-hero-cta`) non e affetto.
- **Impact**: Low — bottoni secondari in sezioni inferiori della home.

## Template-specific (Nøva Creative / Agency/avo)

### Scroll Listener Not Throttled
- **What**: `$(window).scroll()` in `js/main.js` fires on every pixel, queries DOM for `.ftco_navbar` and `.js-scroll-wrap` each time.
- **Impact**: Low-medium. Contributes to scroll jank on slower devices.
- **Status**: Not fixed — would require refactoring to `requestAnimationFrame` or throttle wrapper.

### Waypoints + Staggered Animations
- **What**: 32+ `.ftco-animate` elements use jQuery Waypoints with staggered `setTimeout` at 50ms intervals.
- **Impact**: Low — fires once per element, not continuous.
- **Status**: Not fixed — animation system is integral to the template's design.

## Resolved

### Session 5 — Scroll/Image Jank Fix
- ~~Stellar.js + Scrollax.js causing scroll jank in Nøva Creative~~ — Both disabled in `js/main.js` (parallax removed, layout preserved).
- ~~Parallax.js causing scroll jank in Medilux~~ — `data-parallax` attributes removed from all 5 pages, inline `background-image` added as static fallback, CSS `background: transparent` fixed.
- ~~PreviewEngine replacing all images eager without lazy loading~~ — Added `loading="lazy"` to all replaced images except the first (LCP gets `fetchpriority="high"` + `loading="eager"`).
- ~~Blog-single.html images in Nøva missing width/height and lazy loading~~ — Added `width`/`height` attributes and `loading="lazy"` to below-fold images.

### Session 3
- ~~Servizi page polish pass pending~~ — Audit visivo completo, `::selection` allineato, newsletter normalizzata, responsive fixed.
- ~~CSS duplication across inner pages~~ — Estratto in `medilux-shared.css`.
- ~~Inconsistent `::selection` color~~ — Tutti i 5 CSS ora usano navy.
- ~~`p a` coral link colors~~ — Allineati a gold/navy.
- ~~`services_responsive.css` old rules~~ — Rimossi hero fissi, aggiunto ml-hdr mobile.

### Session 2
- ~~Blog/Contact missing visual polish~~ — Playfair import, navy hero, button system applicati.
- ~~Playfair Display not imported in blog.css/contact.css~~ — `@import` aggiunto.
