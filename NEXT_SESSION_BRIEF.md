# NEXT SESSION BRIEF

## Stato attuale

Due template pilota completati e consolidati:
1. **Medilux** (Medical/drpro → slug `medical-medilux`) — 5 pagine, visual system, scroll jank fixato
2. **Nøva Creative** (Agency/avo → slug `agency-fluxwork`) — 6 pagine, adapter YAML, scroll jank fixato

PreviewEngine: aggiunto lazy loading automatico su immagini sostituite (session 5).

## Obiettivo — Fase 4

**Terzo template pilota verticale: Animal/petvet — analisi strutturale, adapter dedicato, rebranding, premium restyling, mapping text/image slots, prevenzione jank fin dall'inizio.**

## Perimetro esatto

### 1. Analisi strutturale Animal/petvet
- Esplorare `Templates/Animal/petvet/` — pagine disponibili, layout, plugin JS, immagini
- Verificare la struttura nell'import DB: `python -c "..." | grep petvet`
- Identificare parallax/slider/scroll listeners PRIMA di iniziare (prevenzione jank)

### 2. Adapter dedicato
- Creare `adapter.yaml` con mapping completo: slot testo, slot immagine, palette, tipografia
- Definire il brand italiano (nome, tagline, città, settore)

### 3. Rebranding + Premium Restyling
- Applicare il pattern consolidato: CSS condiviso (`xxx-shared.css`), 7x selectors, prefix brand
- Immagini esterne (Pexels) per zone critiche
- Tipografia premium (Google Fonts)
- Palette coerente su tutte le pagine

### 4. Prevenzione jank
- Disabilitare preventivamente parallax/scroll-heavy JS
- Aggiungere `loading="lazy"` e dimensioni alle immagini del template
- Il PreviewEngine ora inietta `loading="lazy"` automaticamente sulle `<img>` sostituite

### 5. Documentazione
- `VISUAL_SYSTEM.md` per il nuovo template
- Aggiornare `PROJECT_STATUS.md` e `KNOWN_ISSUES.md`

## Cosa NON toccare

- **Medilux** — consolidato
- **Nøva Creative** — consolidato
- **PreviewEngine** — non modificare (lazy loading già aggiunto)
- **Django apps** — non toccare
- **Database** — non resettare
- **i18n pipeline** — non modificare

## Startup

```bash
cd C:\tmp\sitoBadr\marketweb
python manage.py runserver 8999
# Preview Animal/petvet:
# Trovare lo slug: python -c "import django,os; os.environ['DJANGO_SETTINGS_MODULE']='marketweb.settings'; django.setup(); from catalog.models import TemplateItem; [print(f'{i.slug} - {i.name}') for i in TemplateItem.objects.filter(source_dir__icontains='petvet')]"
# http://127.0.0.1:8999/customize/<slug>/
```

## Riferimenti

- `Templates/Medical/drpro/VISUAL_SYSTEM.md` — visual system Medilux (primo pilota)
- `Templates/Agency/avo/VISUAL_SYSTEM.md` — visual system Nøva Creative (secondo pilota)
- `Templates/Agency/avo/adapter.yaml` — adapter di riferimento
- `KNOWN_ISSUES.md` — workaround PreviewEngine + problemi residui scroll
- `CLAUDE.md` — architettura Django

## Lezioni apprese (session 5)

- **Parallax JS è la causa principale di scroll jank** — disabilitare sempre prima di lavorare sul visual
- **PreviewEngine stripping srcset + eager loading** amplifica il problema — ora mitigato con lazy loading automatico
- **Background-image su div** non beneficia di `loading="lazy"` — solo `<img>` tag
- **Mapping source directory**: `Medical/drpro` = Medilux (`medical-medilux`), `Agency/avo` = Fluxwork/Nøva (`agency-fluxwork`)
