# KNOWN ISSUES

## PreviewEngine (sistemici — affliggono tutti i template)

### Image Replacement
- **What**: `_replace_hero_images` sostituisce TUTTE le URL immagini locali con foto dal content pool.
- **Impact**: Le immagini hero locali non appaiono in preview.
- **Workaround**: URL esterne dirette (Pexels `https://images.pexels.com/...`) — il motore salta URL che iniziano con `http://` o `https://`.
- **Location**: `customizer/services.py`

### Link Color Override
- **What**: Engine inietta `a:not(.btn)... { color: var(--sg-accent) !important; }`.
- **Impact**: Testo link nei bottoni diventa del colore accent engine.
- **Workaround**: 7x repeated class selectors nei CSS condivisi dei template.
- **Note**: Per i template in allowlist, l'intero layer visivo è skippato — questo problema non si applica.

### Nav/Hero Text Replacement
- **What**: `_replace_content_with_pool` sostituisce il testo del link nav attivo e talvolta il titolo hero con il nome del template.
- **Impact**: "Chi Siamo" diventa "ZampaCura" nella nav delle inner pages.
- **Workaround**: Nessuno trovato. Comportamento sistemico. Non affligge i file raw del template.

## PreviewEngine Opt-Out (adapted templates)

### Allowlist
- **Location**: `marketweb/settings.py` → `ADAPTED_TEMPLATE_SLUGS`
- **Templates**: `medical-medilux`, `agency-blueprint`, `animal-vetaura-2`
- **Effect**: Solo CSS strutturale (~100 righe) invece del mega-layer visivo (~2000+ righe)
- **Functions skipped**: `_inject_differentiation_layer`, `_inject_scroll_animations`, `_inject_premium_interactivity`, `_inject_brand_identity`

### Remaining sg-reveal Classes on DOM
- **What**: Previous page visits may leave `sg-reveal-pending` classes on elements.
- **Impact**: None — the adapted layer CSS neutralizes them.

## Template-specific (Medilux — NON PULITO)

### elements.html Completely Unrebranded
- **What**: Entire page retains original "Dr PRO / Plastic Surgery" content, English text, Lorem ipsum, placeholder contacts.
- **Impact**: Critical — 55+ residuals.
- **Status**: To be fixed in Medilux triage session.

### 48 Original Local Images
- **What**: Almost all images still reference local `images/` files from the original template.
- **Impact**: PreviewEngine replaces them in preview, but raw files are original stock photos.
- **Status**: To be replaced with Pexels URLs in Medilux triage.

### Title/Meta "Dr PRO" Residuals
- **What**: index.html, about.html, services.html still have `<title>Dr PRO</title>` and meta description "Dr PRO template project".
- **Status**: To be fixed in Medilux triage.

## Resolved

### Session 7 — Engine Opt-Out + Cleanup
- ~~Engine injects ~2000 lines of aggressive CSS on adapted templates~~ — Opt-out via allowlist
- ~~Engine injects IntersectionObserver conflicts~~ — `_inject_scroll_animations` skipped
- ~~Engine injects scroll-progress/back-to-top/cursor with gradient~~ — `_inject_premium_interactivity` skipped
- ~~Engine destroys template brand HTML with "VetAura"~~ — `_inject_brand_identity` skipped
- ~~DB name "VetAura" instead of "ZampaCura"~~ — Updated in DB
- ~~Slug mismatch: Nøva documented as `agency-fluxwork`~~ — Corrected to `agency-blueprint`
- ~~ZampaCura blog-single.html: 6 original avatars, 11 lorem blocks, English residuals~~ — All fixed
- ~~Nøva Creative: `lang="en"` on 6 pages, English aria-labels~~ — All fixed
- ~~ZampaCura: `lang="en"` on 8 pages, "or" separator, English footer headings~~ — All fixed
- ~~ZampaCura service cards: white text on hover (invisible)~~ — Fixed with explicit color overrides
- ~~ZampaCura navbar: not full-width on initial load~~ — Fixed with `background: white; top: 0`
- ~~ZampaCura team cards: text hidden behind bg (z-index:-1)~~ — Fixed with `z-index: 1`

### Session 6 — ZampaCura Template
- ~~Stellar.js/Scrollax causing scroll jank~~ — Disabled in main.js
- ~~All local images replaced by engine~~ — Pexels URLs
- ~~Original Petvet branding~~ — Complete rebrand

### Session 5 — Scroll/Image Jank Fix
- ~~Stellar.js + Scrollax in Nøva Creative~~ — Disabled
- ~~Parallax.js in Medilux~~ — data-parallax removed
- ~~PreviewEngine eager loading~~ — lazy loading added

## Licensing
Template licensing status (Colorlib CC BY 3.0, etc.) has NOT been audited. Rebranding does not remove original license obligations. Must be verified separately before commercial use.
