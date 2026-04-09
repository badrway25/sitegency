# NEXT SESSION BRIEF

## Stato attuale

| Template | Slug | Stato | Engine Opt-Out |
|----------|------|-------|----------------|
| Nøva Creative | `agency-blueprint` | PULITO | Attivo |
| ZampaCura | `animal-vetaura-2` | PULITO | Attivo |
| Medilux | `medical-medilux` | NON PULITO | Attivo |

Engine opt-out funzionante per i 3 template pilota. Nøva e ZampaCura hanno superato audit forense completo (0 immagini originali, 0 lorem, 0 inglese residuo).

## Obiettivo — Medilux Triage + Recovery Plan

### Perimetro esatto

1. **Audit strutturale dettagliato** di Medilux (6 pagine HTML)
   - Quali pagine hanno contenuto italiano accettabile
   - Quali pagine hanno contenuto da rifare
   - Stato immagini pagina per pagina

2. **Decisione su elements.html**
   - Opzione A: rebrand completo (costo alto, ~55 residui)
   - Opzione B: escludere dalla navigazione/preview (esclusione pulita)
   - Opzione C: eliminare il file

3. **Sostituzione immagini** — 48 immagini locali originali da sostituire con URL Pexels
   - Priorità: hero backgrounds, team, testimonials
   - Strategia: stessa usata per ZampaCura (URL diretti bypass engine)

4. **Fix title/meta/lang** — 3 pagine con "Dr PRO", 3 con `lang="en"`

5. **Verifica finale** — stesso audit forense di ZampaCura/Nøva

### Cosa NON toccare

- Engine/customizer/services.py — opt-out già funzionante
- settings.py — Medilux già in allowlist
- Nøva Creative — PULITO, non modificare
- ZampaCura — PULITO, non modificare
- Database schema — non resettare
- Import pipeline — non modificare

### Deliverable obbligatori

- [ ] Tutte le pagine Medilux con `lang="it"`
- [ ] Zero `<title>` o `<meta>` con "Dr PRO"
- [ ] Zero immagini originali locali referenziate dall'HTML
- [ ] Zero lorem ipsum
- [ ] Zero testi inglesi visibili (escluso Colorlib CC BY 3.0)
- [ ] Decisione documentata su elements.html
- [ ] Audit forense finale con tabella per pagina
- [ ] PROJECT_STATUS.md aggiornato con stato "PULITO"

### Criteri di completamento

- Medilux supera lo stesso audit forense di ZampaCura/Nøva
- 0 immagini originali, 0 lorem, 0 inglese residuo visibile
- elements.html gestita (rebrandata o esclusa con documentazione)
- Nessuna regressione su Nøva o ZampaCura
- Documentazione aggiornata

## Startup

```bash
cd C:\tmp\sitoBadr\marketweb
python manage.py runserver 8999

# Preview dei 3 pilota:
# http://127.0.0.1:8999/customize/medical-medilux/
# http://127.0.0.1:8999/customize/agency-blueprint/
# http://127.0.0.1:8999/customize/animal-vetaura-2/
```

## Riferimenti

- `marketweb/settings.py` — allowlist (`ADAPTED_TEMPLATE_SLUGS`)
- `customizer/services.py` — `_inject_adapted_layer()` + guards
- `Templates/Medical/drpro/` — file Medilux
- `Templates/Medical/drpro/VISUAL_SYSTEM.md` — visual system Medilux
- `PROJECT_STATUS.md` — audit forense Medilux (sezione dettagliata)
- `KNOWN_ISSUES.md` — issues Medilux specifici

## Licensing

Stato licensing NON verificato. Colorlib templates usano CC BY 3.0 — l'attribuzione nel footer deve restare. Verificare vincoli prima di uso commerciale.
