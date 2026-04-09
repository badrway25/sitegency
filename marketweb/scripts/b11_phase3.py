"""Batch 11 Phase 3: Full audit of all 24 templates after fixes."""
import sys, time, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright

os.environ['DJANGO_SETTINGS_MODULE'] = 'marketweb.settings'
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
import django
django.setup()
from catalog.models import TemplateItem

FAMILIES = ['medical', 'restaurant', 'e-commerce']
BASE = 'http://127.0.0.1:8000'
OUTDIR = os.path.join(os.getcwd(), 'docs', 'screenshots')
ALL = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for fam in FAMILIES:
        slugs = list(TemplateItem.objects.filter(category__slug=fam, is_active=True).order_by('slug').values_list('slug', flat=True))

        for slug in slugs:
            # Desktop IT full-page
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(6)
            page.screenshot(path=os.path.join(OUTDIR, f'{slug}_it_b11f.png'), full_page=True)

            desk = page.evaluate("""() => {
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
                var h2s = document.querySelectorAll('h2');
                var accentH2 = 0;
                h2s.forEach(function(h) {
                    var c = getComputedStyle(h).color;
                    if (!c.includes('rgb(0, 0, 0)') && !c.includes('rgb(33,') && !c.includes('rgb(255, 255')) accentH2++;
                });
                return {
                    h: b.scrollHeight,
                    navH: nav ? Math.round(nav.getBoundingClientRect().height) : 0,
                    fBg: fBg, nan: nan, hidden: hidden,
                    h2: accentH2 + '/' + h2s.length
                };
            }""")
            page.close()

            # Mobile
            page = browser.new_page(viewport={'width': 375, 'height': 812})
            page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(4)
            mob = page.evaluate("""() => {
                var tog = false;
                document.querySelectorAll('.navbar-toggler, .hamburger, [class*="toggle"], [class*="menu-btn"], button.burger').forEach(function(btn) {
                    var s = getComputedStyle(btn);
                    if (s.display !== 'none' && s.visibility !== 'hidden') tog = true;
                });
                return {toggle: tog, overflow: document.body.scrollWidth > 380};
            }""")
            page.close()

            # AR
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/ar/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(4)
            ar_dir = page.evaluate('document.documentElement.getAttribute("dir") || "ltr"')
            page.close()

            # FR
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/fr/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(3)
            fr_nan = page.evaluate("""() => {
                var n = 0;
                document.querySelectorAll('*').forEach(function(el) {
                    if (el.children.length === 0 && el.textContent.trim() === 'NaN') n++;
                });
                return n;
            }""")
            page.close()

            status = []
            if desk['nan'] > 0: status.append(f"NaN:{desk['nan']}")
            if desk['hidden'] > 0: status.append(f"HIDDEN:{desk['hidden']}")
            if not mob['toggle']: status.append('NO_TOG')
            if mob['overflow']: status.append('OVERFLOW')
            if ar_dir != 'rtl': status.append('NO_RTL')
            s = ' '.join(status) if status else 'OK'

            ALL[slug] = {'desk': desk, 'mob': mob, 'ar': ar_dir, 'fr_nan': fr_nan, 'fam': fam}
            print(f'  {slug}: nav={desk["navH"]}px h2={desk["h2"]} nan={desk["nan"]} hid={desk["hidden"]} mob={mob["toggle"]} ar={ar_dir} {s}')

    browser.close()

with open('docs/b11_phase3.json', 'w') as f:
    json.dump(ALL, f, indent=2, ensure_ascii=False, default=str)

# Summary
print('\n=== SUMMARY ===')
for fam in FAMILIES:
    fam_items = {k: v for k, v in ALL.items() if v['fam'] == fam}
    total = len(fam_items)
    no_tog = sum(1 for v in fam_items.values() if not v['mob']['toggle'])
    nan_count = sum(1 for v in fam_items.values() if v['desk']['nan'] > 0)
    hidden = sum(1 for v in fam_items.values() if v['desk']['hidden'] > 0)
    rtl_ok = sum(1 for v in fam_items.values() if v['ar'] == 'rtl')
    print(f'{fam}: {total} templates | no_toggle={no_tog} nan={nan_count} hidden={hidden} rtl={rtl_ok}/{total}')
