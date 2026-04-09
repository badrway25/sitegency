# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sitegency** is a Django-based marketplace for premium, customizable website templates. Users browse ~850+ templates organized by category, customize them live in-browser, and purchase download licenses.

## Common Commands

```bash
# Development server
python manage.py runserver

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Import templates from /Templates/ directory into the DB
python manage.py import_templates
python manage.py import_templates --limit 50   # import only 50
python manage.py import_templates --reset       # clear and re-import

# Run tests
python manage.py test
python manage.py test catalog   # run a single app's tests

# Production static files
python manage.py collectstatic
```

## Architecture

The project is a standard Django multi-app structure under `marketweb/`:

| App | Responsibility |
|-----|----------------|
| `core` | Homepage, FAQs, testimonials, site config (singleton `SiteConfig` model) |
| `catalog` | Template browsing, category listing, detail pages, preview routing |
| `customizer` | Live editor sessions, `PreviewEngine` (HTML rewriting), media uploads |
| `orders` | Checkout, `Order`/`License` creation, confirmation |
| `importer` | `import_templates` management command — scans `Templates/` and upserts DB records |

### Data Flow

```
Templates/ (filesystem)
    └─ import_templates command
           └─ Category → TemplateItem → TemplatePage / TemplateAsset / TemplateSection / TemplateCustomizationField

User visits catalog → picks template → customizer session created (DemoSession)
    └─ PreviewEngine rewrites HTML on-the-fly, injects customization CSS/JS
           └─ /assets/{slug}/... serves raw assets dynamically

User checks out → Customer + Order + OrderItem + License created
```

### PreviewEngine (`customizer/services.py`)

This is the most complex component. It:
- Reads raw HTML from `Templates/{slug}/` on each request (no caching)
- Uses BeautifulSoup to rewrite relative asset URLs → `/assets/{slug}/path`
- Rewrites internal nav links to Django `reverse()` URLs
- Strips or neutralizes blocked nav items (buttons, demo/elements pages)
- Applies i18n translation overrides via `customizer/translation_map.py`
- Injects user customization as inline `<style>` + `<script>` tags
- **Critical**: Custom brand class names added during customization must survive engine rewrites — see memory notes for safe patterns

### Session / Customizer

- Sessions keyed by cookie `bw_token` (no auth required)
- `DemoSession.data` stores customization as JSON blob
- AJAX endpoints: `POST /customize/<slug>/save/` and `POST /customize/<slug>/upload/`
- Uploaded images land in `media/customizer/`

### Internationalization

- URL prefixes: `/en/`, `/it/`, `/fr/`, `/ar/` (English also at `/`)
- Arabic uses RTL layout (detected via `LANGUAGE_BIDI` context variable)
- Locale files in `locale/`; content fallbacks in `customizer/dynamic_content.py`

### Template Assets

Assets are served dynamically (not via `STATIC_FILES`):
- URL pattern: `/assets/<slug>/<path>`
- Resolved to `Templates/<slug>/<path>` on disk at request time

## Key Files

- `customizer/services.py` — PreviewEngine HTML rewriting logic
- `customizer/dynamic_content.py` — Localized demo content pool
- `importer/services/scanner.py` — Filesystem scanner for template discovery
- `importer/services/branding.py` — Category metadata, template name generation
- `catalog/models.py` — Core data models (Category, TemplateItem, TemplatePage, etc.)
- `marketweb/settings.py` — Django config, installed apps, i18n, static/media paths
- `static/css/badrway.css` — Main stylesheet (Bootstrap 5 loaded via CDN)

## Testing

Tests live in `catalog/tests.py`. The test suite covers template discovery and preview rendering. Django's standard test runner is used — no pytest or extra configuration needed.
