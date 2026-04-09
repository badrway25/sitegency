"""Batch 11 Phase 1: Baseline evaluation of 3 families (24 templates)."""
import sys, time, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright

FAMILIES = {
    'medical': [],
    'restaurant': [],
    'e-commerce': [],
}

# Get template slugs
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'marketweb.settings'
django.setup()
from catalog.models import TemplateItem
for fam in FAMILIES:
    FAMILIES[fam] = list(
        TemplateItem.objects.filter(category__slug=fam, is_active=True)
        .order_by('slug').values_list('slug', flat=True)
    )
    print(f'{fam}: {FAMILIES[fam]}')

BASE = 'http://127.0.0.1:8000'
OUTDIR = os.path.join(os.getcwd(), 'docs', 'screenshots')
ALL = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for fam, slugs in FAMILIES.items():
        for slug in slugs:
            # IT desktop
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(6)
            page.screenshot(path=os.path.join(OUTDIR, f'{slug}_it_b11.png'), full_page=True)

            data = page.evaluate("""() => {
                var b = document.body, html = document.documentElement;
                var nav = document.querySelector('header, nav.navbar, .site-navbar, .navigation');
                var ns = nav ? getComputedStyle(nav) : {};
                var navH = nav ? Math.round(nav.getBoundingClientRect().height) : 0;
                var navLinks = [];
                document.querySelectorAll('nav a, .navbar a, header a').forEach(function(a) {
                    var t = a.textContent.trim();
                    if (t.length > 0 && t.length < 25) navLinks.push(t);
                });
                var footer = document.querySelector('footer, .site-footer, .ftco-footer, .footer');
                var fBg = footer ? getComputedStyle(footer).backgroundImage.substring(0, 30) : 'none';
                var imgs = document.querySelectorAll('[class*="col-"] img, .container img, .row img, section img');
                var rounded = 0;
                imgs.forEach(function(i) { if (parseInt(getComputedStyle(i).borderRadius) > 4) rounded++; });
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
                var nan = 0;
                document.querySelectorAll('*').forEach(function(el) {
                    if (el.children.length === 0 && el.textContent.trim() === 'NaN') nan++;
                });
                var hidden = 0;
                document.querySelectorAll('section, .ftco-section, [class*="section"]').forEach(function(el) {
                    var s = getComputedStyle(el);
                    var r = el.getBoundingClientRect();
                    if (r.height > 50 && (s.opacity === '0' || s.visibility === 'hidden')) hidden++;
                });
                // English markers
                var enMarkers = ['About Us','Our Services','Contact Us','Read More','Subscribe','Latest News',
                                 'Book Now','Order Now','Make Appointment','Our Menu','Our Doctors','Shop Now'];
                var text = b.innerText.substring(0, 2000);
                var enFound = enMarkers.filter(function(m) { return text.includes(m); });
                return {
                    h: b.scrollHeight, navH: navH, navPos: ns.position || '',
                    navBlur: (ns.backdropFilter || '').includes('blur'),
                    nav: navLinks.slice(0, 5), fBg: fBg,
                    imgs: rounded + '/' + imgs.length,
                    ftco: ftcoVis + '/' + ftco.length,
                    h2: accentH2 + '/' + h2s.length,
                    nan: nan, hidden: hidden, en: enFound
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
                return {toggle: tog, overflow: document.body.scrollWidth > 380, w: document.body.scrollWidth};
            }""")
            page.close()

            # AR
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/ar/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(4)
            ar = page.evaluate('() => ({dir: document.documentElement.getAttribute("dir") || "ltr"})')
            page.close()

            # FR
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/fr/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(4)
            fr = page.evaluate("""() => {
                var nav = [];
                document.querySelectorAll('nav a, .navbar a, header a').forEach(function(a) {
                    var t = a.textContent.trim();
                    if (t.length > 0 && t.length < 25) nav.push(t);
                });
                return {nav: nav.slice(0, 4)};
            }""")
            page.close()

            en_str = f' EN:{data["en"]}' if data['en'] else ''
            status_parts = []
            if data['nan'] > 0: status_parts.append(f'NaN:{data["nan"]}')
            if data['hidden'] > 0: status_parts.append(f'HIDDEN:{data["hidden"]}')
            if mob['overflow']: status_parts.append('MOB_OVERFLOW')
            if not mob['toggle']: status_parts.append('NO_TOGGLE')
            if ar['dir'] != 'rtl': status_parts.append('NO_RTL')
            status = ' '.join(status_parts) if status_parts else 'CLEAN'

            print(f'  {slug}: nav={data["navH"]}px/{data["navPos"][:3]} ftco={data["ftco"]} imgs={data["imgs"]} h2={data["h2"]} footer={data["fBg"][:15]} {status}{en_str}')
            print(f'    mob={mob["overflow"]}/{mob["toggle"]} ar={ar["dir"]} fr={fr["nav"][:3]}')

            ALL[slug] = {'desktop': data, 'mobile': mob, 'ar': ar, 'fr': fr, 'family': fam}

    browser.close()

with open('docs/b11_baseline.json', 'w') as f:
    json.dump(ALL, f, indent=2, ensure_ascii=False, default=str)
print('\nBaseline data saved to docs/b11_baseline.json')
