"""Batch 16: Final 7 families — complete all 192 templates."""
import sys, time, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'marketweb.settings'
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
import django; django.setup()
from catalog.models import TemplateItem
from playwright.sync_api import sync_playwright

FAMILIES = ['creative', 'education', 'fashion', 'finance', 'real-estate', 'technology', 'wedding']
BASE = 'http://127.0.0.1:8000'
OUTDIR = os.path.join(os.getcwd(), 'docs', 'screenshots')
ALL = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for fam in FAMILIES:
        slugs = list(TemplateItem.objects.filter(
            category__slug=fam, is_active=True
        ).order_by('slug').values_list('slug', flat=True))
        print(f'\n=== {fam.upper()} ({len(slugs)}) ===', flush=True)

        for slug in slugs:
            tpl = {'family': fam}

            # DESKTOP IT
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(6)
            page.screenshot(path=os.path.join(OUTDIR, f'{slug}_b16.png'), full_page=True)

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
                document.querySelectorAll('section, .ftco-section, [class*="section"], .heading-section, .section-heading, [data-aos]').forEach(function(el) {
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
                var weakSections = 0, totalSections = 0, emptyBlocks = 0;
                document.querySelectorAll('section, .site-section, .ftco-section, [class*="section"], [class*="area"]').forEach(function(el) {
                    var r = el.getBoundingClientRect();
                    if (r.height < 30) return;
                    var s = getComputedStyle(el);
                    if (s.display === 'none') return;
                    totalSections++;
                    var text = (el.innerText || '').trim();
                    if (text.length < 10 && r.height > 100) { weakSections++; emptyBlocks++; }
                    if (parseInt(s.paddingTop) > 80) weakSections++;
                });
                return {
                    h: b.scrollHeight, navH: nav ? Math.round(nav.getBoundingClientRect().height) : 0,
                    navPos: ns.position || '', navBlur: (ns.backdropFilter || '').includes('blur'),
                    fBg: fBg, nan: nan, hidden: hidden,
                    ftco: ftcoVis + '/' + ftco.length,
                    h2: accentH2 + '/' + h2s.length,
                    imgs: rounded + '/' + imgs.length,
                    totalSections: totalSections, weakSections: weakSections, emptyBlocks: emptyBlocks
                };
            }""")
            page.close()

            # MOBILE
            page = browser.new_page(viewport={'width': 375, 'height': 812})
            page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(4)
            tpl['mob'] = page.evaluate('() => ({overflow: document.body.scrollWidth > 380, w: document.body.scrollWidth})')
            page.close()

            # AR
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/ar/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(4)
            tpl['ar'] = page.evaluate('() => ({dir: document.documentElement.getAttribute("dir") || "ltr"})')
            page.close()

            # FR
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/fr/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(3)
            tpl['fr'] = page.evaluate("""() => {
                var nan = 0;
                document.querySelectorAll('*').forEach(function(el) {
                    if (el.children.length === 0 && el.textContent.trim() === 'NaN') nan++;
                });
                return {nan: nan};
            }""")
            page.close()

            ALL[slug] = tpl
            d = tpl['desk']
            issues = []
            if d['nan'] > 0: issues.append(f"NaN:{d['nan']}")
            if d['hidden'] > 0: issues.append(f"HID:{d['hidden']}")
            if tpl['mob']['overflow']: issues.append('OVF')
            if tpl['ar']['dir'] != 'rtl': issues.append('NO_RTL')
            if d['weakSections'] > 2: issues.append(f"WEAK:{d['weakSections']}")
            s = ' '.join(issues) if issues else 'OK'
            print(f'  {slug}: nav={d["navH"]}px ftco={d["ftco"]} imgs={d["imgs"]} h2={d["h2"]} weak={d["weakSections"]}/{d["totalSections"]} {s}', flush=True)

    browser.close()

with open('docs/b16_audit.json', 'w') as f:
    json.dump(ALL, f, indent=2, ensure_ascii=False, default=str)

print('\n' + '='*80, flush=True)
total = len(ALL)
clean = sum(1 for v in ALL.values() if v['desk']['nan'] == 0 and v['desk']['hidden'] == 0 and not v['mob']['overflow'] and v['ar']['dir'] == 'rtl')
total_weak = sum(v['desk']['weakSections'] for v in ALL.values())
total_sections = sum(v['desk']['totalSections'] for v in ALL.values())
print(f'TOTAL: {total} templates | {clean}/{total} clean | {total_weak} weak / {total_sections} sections ({round(total_weak/max(total_sections,1)*100,1)}%)', flush=True)

for fam in FAMILIES:
    items = {k: v for k, v in ALL.items() if v['family'] == fam}
    t = len(items)
    c = sum(1 for v in items.values() if v['desk']['nan'] == 0 and v['desk']['hidden'] == 0 and not v['mob']['overflow'] and v['ar']['dir'] == 'rtl')
    w = sum(v['desk']['weakSections'] for v in items.values())
    ftco_t = sum(int(v['desk']['ftco'].split('/')[1]) for v in items.values())
    ftco_v = sum(int(v['desk']['ftco'].split('/')[0]) for v in items.values())
    print(f'  {fam}: {c}/{t} clean | weak_avg={w/t:.1f} | ftco={ftco_v}/{ftco_t}', flush=True)
