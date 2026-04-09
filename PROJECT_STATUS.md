# PROJECT STATUS — Sitegency

Last updated: 2026-04-09 (session 7 — final handoff)

## Overview

Django-based marketplace for premium website templates. ~850+ templates organized by category. Users browse, customize live in-browser, and purchase download licenses.

## Source Directory Mapping

| Template Name | DB Slug | Display Name | Source Directory | Category | Status |
|---------------|---------|--------------|------------------|----------|--------|
| **Medilux** | `medical-medilux` | Medilux | `Templates/Medical/drpro` | Medical | NON PULITO |
| **Nøva Creative** | `agency-blueprint` | Blueprint | `Templates/Agency/avo` | Agency | PULITO |
| **ZampaCura** | `animal-vetaura-2` | ZampaCura | `Templates/Animal/petvet` | Animal | PULITO |

## Engine Opt-Out System

### Location
- **Allowlist**: `marketweb/settings.py` → `ADAPTED_TEMPLATE_SLUGS`
- **Engine**: `customizer/services.py` — guards in 4 functions

### How it works
Templates in the allowlist receive only a minimal structural CSS layer (~100 lines) instead of the engine's full visual layer (~2000+ lines). The following engine functions are skipped for adapted templates:
- `_inject_differentiation_layer` → replaced by `_inject_adapted_layer`
- `_inject_scroll_animations` → skipped entirely
- `_inject_premium_interactivity` → skipped entirely
- `_inject_brand_identity` → skipped entirely (adapted templates have their own brand HTML)

### Structural layer (always active for adapted templates)
- Hide off-canvas/mobile menus on desktop
- Force navbar visible on desktop
- Prevent mobile horizontal overflow
- Override animation libraries that hide content
- Prefers-reduced-motion, focus accessibility
- Disable sg-scroll-progress, sg-back-to-top, sg-cursor, sg-reveal

### How to add a new adapted template
1. Complete the template's visual system
2. Find the DB slug: `TemplateItem.objects.filter(source_dir='...').values('slug')`
3. Add the slug to `ADAPTED_TEMPLATE_SLUGS` in `settings.py`
4. Verify in browser

### How to rollback
Remove the slug from `ADAPTED_TEMPLATE_SLUGS`. Full engine layer re-applied immediately.

## Template Work

### Nøva Creative (Agency/avo) — PULITO

6/6 pagine rebrandate, visual system documentato, audit forense completato.

**Pagine**: Home (slider hero), Chi Siamo, Portfolio, Blog, Articolo, Contatti
**Brand**: Nøva Creative — Agenzia Creativa Digitale, Milano
**Palette**: navy scuro `#1a1a2e` + accent corallo `#e94560` + warm neutrals
**Typography**: Sora (headings) + Inter (body)
**Pattern CSS**: `avo-shared.css` centralizza override
**Image strategy**: Tutti URL Pexels diretti (0 immagini originali)
**Text audit**: 0 lorem, 0 inglese visibile, 0 brand originale
**Engine opt-out**: Attivo (`agency-blueprint` in allowlist)

### ZampaCura (Animal/petvet) — PULITO

8/8 pagine rebrandate, visual system documentato, audit forense completato.

**Pagine**: Home, Chi Siamo, Servizi, Il Team, Blog, Articolo, Tariffe, Contatti
**Brand**: ZampaCura — Centro Veterinario, Torino
**Palette**: verde fresco `#2a7d5f` + warm caramel `#d4a574` + verde scuro `#1e3a2f`
**Typography**: Lora (headings) + DM Sans (body)
**Pattern CSS**: `petvet-shared.css` centralizza override
**Image strategy**: Tutti URL Pexels diretti (0 immagini originali)
**Text audit**: 0 lorem, 0 inglese visibile, 0 brand originale
**Engine opt-out**: Attivo (`animal-vetaura-2` in allowlist)
**DB name**: Aggiornato da "VetAura" a "ZampaCura"

### Medilux (Medical/drpro) — NON PULITO

5 pagine rebrandate (contenuti italiani), 1 pagina completamente non toccata, immagini quasi tutte originali.

**Audit forense (session 7)**:
- 48 immagini originali locali su 49 (solo 1 hero ha URL Pexels)
- `elements.html` completamente non rebrandizzata (55+ residui, brand "Dr PRO", lorem ipsum, contatti placeholder)
- 3 pagine con `<title>Dr PRO</title>` e `<meta>` "Dr PRO template project"
- 3 pagine con `<html lang="en">`
- `services.html` con alt inglesi su immagini
- ~70 residui testuali totali
- **Engine opt-out attivo** (`medical-medilux` in allowlist) — il visual funziona ma il contenuto non è pulito

## Licensing

Lo stato di licensing dei template sorgente (Colorlib CC BY 3.0, etc.) NON è stato verificato in questa sessione. Il rebranding non implica libertà dai vincoli di licenza originali. Verificare separatamente prima di qualsiasi uso commerciale.

## Infrastructure (untouched)

- Django apps: core, catalog, customizer, orders, importer — all functional
- Database: db.sqlite3 (populated, ~460 templates)
- PreviewEngine: customizer/services.py — with adapted template opt-out
- Import pipeline: importer/management/commands/import_templates.py
- i18n: 4 languages configured (en, it, fr, ar)
