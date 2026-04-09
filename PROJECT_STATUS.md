# PROJECT STATUS — Sitegency

Last updated: 2026-04-09 (session 5)

## Overview

Django-based marketplace for premium website templates. ~850+ templates organized by category. Users browse, customize live in-browser, and purchase download licenses.

## Source Directory Mapping

| Template Name | DB Slug | Source Directory | Category |
|---------------|---------|------------------|----------|
| **Medilux** | `medical-medilux` | `Templates/Medical/drpro` | Medical |
| **Nøva Creative** (Fluxwork) | `agency-fluxwork` | `Templates/Agency/avo` | Agency |

## Template Work

### Medilux (Medical/drpro) — CONSOLIDATO

5/5 pagine complete, visual system estratto e documentato, scroll jank fixato.

**Pagine**: Home (split hero), Chi Siamo, Servizi, Blog, Contatti
**Palette**: navy `#111d2e` + gold `#b09560` + warm neutrals
**Typography**: Playfair Display (headings) + Montserrat (body)
**Pattern CSS**: `medilux-shared.css` centralizza override condivisi per le 4 inner pages
**Documentazione**: `VISUAL_SYSTEM.md` — riferimento completo riusabile per nuovi template
**PreviewEngine workarounds**: 7x class selectors per specificity, external URLs per immagini, `ml-` prefix per brand elements

#### File modificati (Templates/Medical/drpro/)
- HTML: `index.html`, `about.html`, `services.html`, `blog.html`, `contact.html`
- CSS: `main_styles.css`, `responsive.css`, `about.css`, `services.css`, `blog.css`, `contact.css`, `medilux-shared.css`, `services_responsive.css`
- Docs: `VISUAL_SYSTEM.md`
- Images: `images/hero.jpg`, `images/hero_main.jpg`

### Nøva Creative (Agency/avo) — CONSOLIDATO

6/6 pagine rebrandate, visual system documentato, scroll jank fixato.

**Pagine**: Home (slider hero), Chi Siamo, Portfolio, Blog, Articolo, Contatti
**Brand**: Nøva Creative — Agenzia Creativa Digitale, Milano
**Palette**: navy scuro `#1a1a2e` + accent corallo `#e94560` + warm neutrals
**Typography**: Sora (headings) + Inter (body)
**Pattern CSS**: `avo-shared.css` centralizza override condivisi (7x selectors, palette, tipografia)
**Documentazione**: `VISUAL_SYSTEM.md` + `adapter.yaml` — riferimento completo per customizer
**PreviewEngine workarounds**: 7x class selectors, direct Pexels URLs, `av-` prefix per brand
**Image strategy**: Tutti URL Pexels diretti (nessuna immagine locale nelle zone critiche)

#### File modificati (Templates/Agency/avo/)
- HTML: `index.html`, `about.html`, `work.html`, `blog.html`, `blog-single.html`, `contact.html`
- CSS: `css/avo-shared.css` (nuovo)
- JS: `js/main.js` (parallax disabilitato)
- Docs: `VISUAL_SYSTEM.md`, `adapter.yaml`

## Session 5 — Scroll/Image Jank Fix

### Diagnosi
Il jank durante lo scroll nelle preview di Medilux e Nøva Creative era causato da:
1. **Motori parallax JS** (70% dell'impatto): Stellar.js + Scrollax.js (Nøva), Parallax.js (Medilux) — DOM manipulation continua ad ogni pixel di scroll
2. **Caricamento eager di tutte le immagini remote** (30%): il PreviewEngine sostituiva tutte le `<img>` con URL Unsplash 1200px senza `loading="lazy"`

### Fix applicati
- **Template Nøva**: Stellar.js + Scrollax.js disabilitati in `js/main.js`
- **Template Medilux**: `data-parallax` rimosso da tutte le 5 pagine, inline `background-image` statico come fallback, CSS `.parallax-window` corretto
- **PreviewEngine**: aggiunto `loading="lazy"` a tutte le immagini sostituite tranne la prima (LCP → `fetchpriority="high"` + `loading="eager"`)
- **Blog-single Nøva**: aggiunti `width`/`height` e `loading="lazy"` alle immagini

### Problemi residui (non fixati — richiedono refactoring)
- Scroll listener non throttled in entrambi i template (`$(window).scroll()`)
- Waypoints + animazioni staggered in Nøva (32+ elementi)
- ScrollMagic milestone counters in Medilux

## Infrastructure (untouched)

- Django apps: core, catalog, customizer, orders, importer — all functional
- Database: db.sqlite3 (6 MB, populated)
- PreviewEngine: customizer/services.py — runtime HTML rewriting (lazy loading aggiunto in session 5)
- Import pipeline: importer/management/commands/import_templates.py
- i18n: 4 languages configured (en, it, fr, ar)

## Project Files

- `CLAUDE.md` — architecture guide for Claude Code
- `PROJECT_STATUS.md` — this file
- `KNOWN_ISSUES.md` — bug tracker with template vs PreviewEngine classification
- `NEXT_SESSION_BRIEF.md` — handoff for next session
