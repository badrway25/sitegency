"""Batch 14: 5 families — transformation + deep audit + selective micro-polish."""
import sys, time, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'marketweb.settings'
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
import django; django.setup()
from catalog.models import TemplateItem
from playwright.sync_api import sync_playwright

FAMILIES = ['hotel', 'fitness', 'construction', 'portfolio', 'lawyer']
BASE = 'http://127.0.0.1:8000'
OUTDIR = os.path.join(os.getcwd(), 'docs', 'screenshots')
ALL = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for fam in FAMILIES:
        slugs = list(TemplateItem.objects.filter(
            category__slug=fam, is_active=True
        ).order_by('slug').values_list('slug', flat=True))
        print(f'\n=== {fam.upper()} ({len(slugs)} templates) ===')

        for slug in slugs:
            tpl = {'family': fam}

            # ── DESKTOP IT: full section audit ──
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(6)
            page.screenshot(path=os.path.join(OUTDIR, f'{slug}_it_b14.png'), full_page=True)

            tpl['desk'] = page.evaluate("""() => {
                var b = document.body;
                var nav = document.querySelector('header, nav.navbar, .site-navbar, .navigation');
                var ns = nav ? getComputedStyle(nav) : {};
                var footer = document.querySelector('footer, .site-footer, .ftco-footer, .footer');
                var fBg = footer ? getComputedStyle(footer).backgroundImage.substring(0, 25) : 'none';
                var nan = 0;
                document.querySelectorAll('*').forEach(function(el) {
                    if (el.children.length === 0 && el.textContent.trim() === 'NaN') nan++;
                });
                var hidden = 0;
                document.querySelectorAll('section, .ftco-section, [class*="section"]').forEach(function(el) {
                    var s = getComputedStyle(el);
                    if (el.getBoundingClientRect().height > 50 && (s.opacity === '0' || s.visibility === 'hidden')) hidden++;
                });
                var ftco = document.querySelectorAll('.ftco-animate');
                var ftcoVis = 0;
                ftco.forEach(function(el) {
                    var s = getComputedStyle(el);
                    if (s.opacity !== '0' && s.visibility !== 'hidden') ftcoVis++;
                });
                var h2s = document.querySelectorAll('h2');
                var accentH2 = 0;
                h2s.forEach(function(h) {
                    var c = getComputedStyle(h).color;
                    if (!c.includes('rgb(0, 0, 0)') && !c.includes('rgb(33,') && !c.includes('rgb(255, 255')) accentH2++;
                });
                var imgs = document.querySelectorAll('[class*="col-"] img, .container img, .row img, section img');
                var rounded = 0;
                imgs.forEach(function(i) { if (parseInt(getComputedStyle(i).borderRadius) > 4) rounded++; });
                // Weak section detection
                var weakSections = 0;
                var totalSections = 0;
                document.querySelectorAll('section, .site-section, .ftco-section, [class*="section"], [class*="area"]').forEach(function(el) {
                    var r = el.getBoundingClientRect();
                    if (r.height < 30) return;
                    var s = getComputedStyle(el);
                    if (s.display === 'none') return;
                    totalSections++;
                    var text = (el.innerText || '').trim();
                    if (text.length < 10 && r.height > 100) weakSections++;
                    if (parseInt(s.paddingTop) > 80) weakSections++;
                });
                return {
                    h: b.scrollHeight,
                    navH: nav ? Math.round(nav.getBoundingClientRect().height) : 0,
                    navPos: ns.position || '',
                    navBlur: (ns.backdropFilter || '').includes('blur'),
                    fBg: fBg, nan: nan, hidden: hidden,
                    ftco: ftcoVis + '/' + ftco.length,
                    h2: accentH2 + '/' + h2s.length,
                    imgs: rounded + '/' + imgs.length,
                    totalSections: totalSections,
                    weakSections: weakSections
                };
            }""")
            page.close()

            # ── MOBILE ──
            page = browser.new_page(viewport={'width': 375, 'height': 812})
            page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(4)
            tpl['mob'] = page.evaluate("""() => {
                return {
                    overflow: document.body.scrollWidth > 380,
                    w: document.body.scrollWidth,
                    h: document.body.scrollHeight
                };
            }""")
            page.close()

            # ── AR RTL ──
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/ar/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(4)
            tpl['ar'] = page.evaluate('() => ({dir: document.documentElement.getAttribute("dir") || "ltr"})')
            page.close()

            # ── FR ──
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/fr/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(3)
            tpl['fr'] = page.evaluate("""() => {
                var nan = 0;
                document.querySelectorAll('*').forEach(function(el) {
                    if (el.children.length === 0 && el.textContent.trim() === 'NaN') nan++;
                });
                var nav = [];
                document.querySelectorAll('nav a, .navbar a, header a').forEach(function(a) {
                    var t = a.textContent.trim();
                    if (t.length > 0 && t.length < 25) nav.push(t);
                });
                return {nan: nan, nav: nav.slice(0, 4)};
            }""")
            page.close()

            ALL[slug] = tpl
            d = tpl['desk']
            issues = []
            if d['nan'] > 0: issues.append(f"NaN:{d['nan']}")
            if d['hidden'] > 0: issues.append(f"HID:{d['hidden']}")
            if tpl['mob']['overflow']: issues.append('MOB_OVF')
            if tpl['ar']['dir'] != 'rtl': issues.append('NO_RTL')
            if tpl['fr']['nan'] > 0: issues.append(f"FR_NaN:{tpl['fr']['nan']}")
            if d['weakSections'] > 2: issues.append(f"WEAK:{d['weakSections']}")
            s = ' '.join(issues) if issues else 'CLEAN'

            print(f'  {slug}: nav={d["navH"]}px h2={d["h2"]} ftco={d["ftco"]} imgs={d["imgs"]} sec={d["totalSections"]} weak={d["weakSections"]} mob={tpl["mob"]["overflow"]} ar={tpl["ar"]["dir"]} {s}')

    browser.close()

# Save
with open('docs/b14_audit.json', 'w') as f:
    json.dump(ALL, f, indent=2, ensure_ascii=False, default=str)

# Phase 3: Identify weakest templates for micro-polish
print('\n' + '='*80)
print('PHASE 3: SELECTIVE MICRO-POLISH CANDIDATES')
print('='*80)
for fam in FAMILIES:
    fam_items = [(k, v) for k, v in ALL.items() if v['family'] == fam]
    fam_items.sort(key=lambda x: -x[1]['desk']['weakSections'])
    total = len(fam_items)
    target = max(2, int(total * 0.35))  # 30-40% of family
    print(f'\n{fam} ({total} templates, polish top {target}):')
    for i, (slug, v) in enumerate(fam_items):
        d = v['desk']
        marker = ' ← POLISH' if i < target else ''
        print(f'  {slug}: weak={d["weakSections"]}/{d["totalSections"]} h={d["h"]}{marker}')

# Summary
print('\n' + '='*80)
print('FAMILY SUMMARY')
print('='*80)
for fam in FAMILIES:
    items = {k: v for k, v in ALL.items() if v['family'] == fam}
    total = len(items)
    clean = sum(1 for v in items.values()
                if v['desk']['nan'] == 0 and v['desk']['hidden'] == 0
                and not v['mob']['overflow'] and v['ar']['dir'] == 'rtl')
    ftco_total = sum(int(v['desk']['ftco'].split('/')[1]) for v in items.values())
    ftco_vis = sum(int(v['desk']['ftco'].split('/')[0]) for v in items.values())
    print(f'{fam}: {clean}/{total} clean | ftco={ftco_vis}/{ftco_total} | '
          f'avg_weak={sum(v["desk"]["weakSections"] for v in items.values())/total:.1f}')
