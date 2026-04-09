import time, os, json
from playwright.sync_api import sync_playwright

TEMPLATES = [
    'business-axiom-corp', 'business-civitas', 'business-consular', 'business-corporis',
    'business-irondesk', 'business-meridia', 'business-north-bureau', 'business-prime-office'
]
BASE = 'http://127.0.0.1:8000'
OUTDIR = os.path.join(os.getcwd(), 'docs', 'screenshots')
ALL = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for slug in TEMPLATES:
        result = {}

        # DESKTOP IT full-page
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
        time.sleep(7)
        page.screenshot(path=os.path.join(OUTDIR, f'{slug}_it_b10.png'), full_page=True)

        result['desktop'] = page.evaluate("""() => {
            var b = document.body;
            var blocks = [];
            var all = document.querySelectorAll('section, .site-section, .ftco-section, [class*="section"], header, footer, .footer, .ftco-footer');
            var seen = new Set();
            all.forEach(function(el) {
                if (seen.has(el)) return;
                seen.add(el);
                var r = el.getBoundingClientRect();
                if (r.height < 20) return;
                var s = getComputedStyle(el);
                var text = (el.innerText || '').substring(0, 60);
                var h2 = el.querySelector('h2');
                blocks.push({
                    cls: (el.className || '').substring(0, 50),
                    h: Math.round(r.height),
                    top: Math.round(r.top + window.scrollY),
                    bgImg: s.backgroundImage !== 'none' ? 'has' : 'none',
                    pad: parseInt(s.paddingTop) + '/' + parseInt(s.paddingBottom),
                    h2: h2 ? h2.textContent.trim().substring(0, 30) : '',
                    empty: text.trim().length < 10
                });
            });
            blocks.sort(function(a,b) { return a.top - b.top; });
            var nav = document.querySelector('header, nav.navbar, .site-navbar, .navigation');
            var ns = nav ? getComputedStyle(nav) : {};
            var footer = document.querySelector('footer, .site-footer, .ftco-footer, .footer');
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
            return {
                h: b.scrollHeight, blocks: blocks,
                navH: nav ? Math.round(nav.getBoundingClientRect().height) : 0,
                navPos: ns.position || '', navBlur: (ns.backdropFilter || '').includes('blur'),
                footerH: footer ? Math.round(footer.getBoundingClientRect().height) : 0,
                footerBg: footer ? getComputedStyle(footer).backgroundImage.substring(0, 30) : 'none',
                nan: nan, hidden: hidden
            };
        }""")
        page.close()

        # AR RTL full-page
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        page.goto(f'{BASE}/ar/preview/{slug}/', wait_until='networkidle', timeout=30000)
        time.sleep(5)
        page.screenshot(path=os.path.join(OUTDIR, f'{slug}_ar_b10.png'), full_page=True)
        result['ar'] = page.evaluate("""() => {
            return {
                dir: document.documentElement.getAttribute('dir') || 'ltr',
                h: document.body.scrollHeight
            };
        }""")
        page.close()

        # MOBILE full-page
        page = browser.new_page(viewport={'width': 375, 'height': 812})
        page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
        time.sleep(5)
        page.screenshot(path=os.path.join(OUTDIR, f'{slug}_mob_b10.png'), full_page=True)
        result['mobile'] = page.evaluate("""() => {
            var b = document.body;
            var tog = false;
            document.querySelectorAll('.navbar-toggler, .hamburger, [class*="toggle"], [class*="menu-btn"], button.burger').forEach(function(btn) {
                var s = getComputedStyle(btn);
                if (s.display !== 'none' && s.visibility !== 'hidden') tog = true;
            });
            return {toggle: tog, overflow: b.scrollWidth > 380, w: b.scrollWidth, h: b.scrollHeight};
        }""")
        page.close()

        # FR
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        page.goto(f'{BASE}/fr/preview/{slug}/', wait_until='networkidle', timeout=30000)
        time.sleep(4)
        result['fr'] = page.evaluate("""() => {
            var nav = [];
            document.querySelectorAll('nav a, .navbar a, header a').forEach(function(a) {
                var t = a.textContent.trim();
                if (t.length > 0 && t.length < 25) nav.push(t);
            });
            return {nav: nav.slice(0, 5)};
        }""")
        page.close()

        ALL[slug] = result

        d = result['desktop']
        emptyBlocks = sum(1 for b in d['blocks'] if b['empty'])
        print(f'{slug}:')
        print(f'  DESKTOP: h={d["h"]} sections={len(d["blocks"])} empty={emptyBlocks} hidden={d["hidden"]} nan={d["nan"]}')
        print(f'    nav={d["navH"]}px/{d["navPos"]}/{d["navBlur"]} footer={d["footerH"]}px/{d["footerBg"][:20]}')
        for b in d['blocks']:
            marker = ' [EMPTY]' if b['empty'] else ''
            print(f'    @{b["top"]:5d} h={b["h"]:4d} pad={b["pad"]:7s} bg={b["bgImg"]:4s} h2="{b["h2"][:25]}"{marker}')
        print(f'  AR: dir={result["ar"]["dir"]} h={result["ar"]["h"]}')
        print(f'  FR: nav={result["fr"]["nav"][:3]}')
        print(f'  MOB: toggle={result["mobile"]["toggle"]} overflow={result["mobile"]["overflow"]} w={result["mobile"]["w"]}')
        print()

    browser.close()

with open('docs/business_b10_audit.json', 'w') as f:
    json.dump(ALL, f, indent=2, ensure_ascii=False, default=str)
print('Full audit data saved')
