"""Batch 12: Deep visual audit — scroll every section of all 24 templates."""
import sys, time, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'marketweb.settings'
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
import django; django.setup()
from catalog.models import TemplateItem
from playwright.sync_api import sync_playwright

FAMILIES = ['medical', 'restaurant', 'e-commerce']
BASE = 'http://127.0.0.1:8000'
OUTDIR = os.path.join(os.getcwd(), 'docs', 'screenshots')
ALL = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for fam in FAMILIES:
        slugs = list(TemplateItem.objects.filter(
            category__slug=fam, is_active=True
        ).order_by('slug').values_list('slug', flat=True))

        for slug in slugs:
            tpl = {}

            # ═══ DESKTOP IT: per-section scroll audit ═══
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(7)

            tpl['desktop'] = page.evaluate("""() => {
                var b = document.body;
                var blocks = [];
                var all = document.querySelectorAll(
                    'section, .site-section, .ftco-section, [class*="section"], ' +
                    'header, footer, .footer, .ftco-footer, .site-footer'
                );
                var seen = new Set();
                all.forEach(function(el) {
                    if (seen.has(el)) return;
                    seen.add(el);
                    var r = el.getBoundingClientRect();
                    if (r.height < 15) return;
                    var s = getComputedStyle(el);
                    var text = (el.innerText || '');
                    var h2 = el.querySelector('h2');
                    var imgs = el.querySelectorAll('img');
                    var imgCount = 0;
                    imgs.forEach(function(i) { if (i.getBoundingClientRect().width > 30) imgCount++; });
                    // Check for broken/empty content
                    var visibleText = text.trim().length;
                    var isEmpty = visibleText < 10 && imgCount === 0 && r.height > 80;
                    // Check for excessive whitespace (height much larger than content)
                    var childH = 0;
                    for (var i = 0; i < el.children.length; i++) {
                        childH += el.children[i].getBoundingClientRect().height;
                    }
                    var excessWhitespace = r.height > 300 && childH < r.height * 0.3;
                    blocks.push({
                        cls: (el.className || '').substring(0, 50),
                        h: Math.round(r.height),
                        top: Math.round(r.top + window.scrollY),
                        pad: parseInt(s.paddingTop) + '/' + parseInt(s.paddingBottom),
                        bgImg: s.backgroundImage !== 'none' ? 'has' : 'none',
                        h2: h2 ? h2.textContent.trim().substring(0, 30) : '',
                        imgs: imgCount,
                        empty: isEmpty,
                        excessWS: excessWhitespace,
                        textLen: Math.min(visibleText, 999)
                    });
                });
                blocks.sort(function(a,b) { return a.top - b.top; });

                // NaN
                var nan = 0;
                document.querySelectorAll('*').forEach(function(el) {
                    if (el.children.length === 0 && el.textContent.trim() === 'NaN') nan++;
                });
                // Hidden
                var hidden = 0;
                document.querySelectorAll('section, .ftco-section, [class*="section"]').forEach(function(el) {
                    var s = getComputedStyle(el);
                    if (el.getBoundingClientRect().height > 50 && (s.opacity === '0' || s.visibility === 'hidden')) hidden++;
                });
                // Footer
                var footer = document.querySelector('footer, .site-footer, .ftco-footer, .footer');
                var fH = footer ? Math.round(footer.getBoundingClientRect().height) : 0;
                var fBg = footer ? getComputedStyle(footer).backgroundImage.substring(0, 25) : 'none';
                // Nav
                var nav = document.querySelector('header, nav.navbar, .site-navbar, .navigation');
                var navH = nav ? Math.round(nav.getBoundingClientRect().height) : 0;

                return {
                    h: b.scrollHeight, blocks: blocks,
                    nan: nan, hidden: hidden,
                    navH: navH, fH: fH, fBg: fBg
                };
            }""")
            page.close()

            # ═══ MOBILE IT: full-page ═══
            page = browser.new_page(viewport={'width': 375, 'height': 812})
            page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(5)
            tpl['mobile'] = page.evaluate("""() => {
                var b = document.body;
                // Check every section for overflow
                var overflowSections = 0;
                document.querySelectorAll('section, .ftco-section, [class*="section"], .container, .row').forEach(function(el) {
                    if (el.scrollWidth > 380) overflowSections++;
                });
                // Check stacking (text overlapping images)
                var overlaps = 0;
                var allRects = [];
                document.querySelectorAll('h1, h2, h3, img').forEach(function(el) {
                    var r = el.getBoundingClientRect();
                    if (r.width > 10 && r.height > 10) {
                        allRects.forEach(function(prev) {
                            if (r.top < prev.bottom && r.bottom > prev.top &&
                                r.left < prev.right && r.right > prev.left &&
                                prev.tag !== el.tagName) overlaps++;
                        });
                        allRects.push({top: r.top, bottom: r.bottom, left: r.left, right: r.right, tag: el.tagName});
                    }
                });
                return {
                    overflow: b.scrollWidth > 380,
                    w: b.scrollWidth,
                    h: b.scrollHeight,
                    overflowSections: overflowSections,
                    overlaps: overlaps
                };
            }""")
            page.close()

            # ═══ AR RTL: full-page ═══
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/ar/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(5)
            tpl['ar'] = page.evaluate("""() => {
                var html = document.documentElement;
                var b = document.body;
                // Check for LTR-only elements (text-align: left on visible content)
                var ltrLeaks = 0;
                document.querySelectorAll('h1, h2, h3, p, .btn, a').forEach(function(el) {
                    var s = getComputedStyle(el);
                    var r = el.getBoundingClientRect();
                    if (r.width > 50 && s.direction === 'ltr' && s.textAlign === 'left' && el.textContent.trim().length > 5) {
                        // Check if it contains Arabic
                        if (/[\u0600-\u06FF]/.test(el.textContent)) ltrLeaks++;
                    }
                });
                return {
                    dir: html.getAttribute('dir') || 'ltr',
                    h: b.scrollHeight,
                    ltrLeaks: ltrLeaks
                };
            }""")
            page.close()

            # ═══ FR verification ═══
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

            # Print summary
            d = tpl['desktop']
            empties = [b for b in d['blocks'] if b['empty']]
            excessWS = [b for b in d['blocks'] if b['excessWS']]
            issues = []
            if d['nan'] > 0: issues.append(f"NaN:{d['nan']}")
            if d['hidden'] > 0: issues.append(f"HIDDEN:{d['hidden']}")
            if empties: issues.append(f"EMPTY:{len(empties)}")
            if excessWS: issues.append(f"EXCESS_WS:{len(excessWS)}")
            if tpl['mobile']['overflow']: issues.append('MOB_OVERFLOW')
            if tpl['mobile']['overlaps'] > 3: issues.append(f"MOB_OVERLAPS:{tpl['mobile']['overlaps']}")
            if tpl['ar']['dir'] != 'rtl': issues.append('NO_RTL')
            if tpl['ar']['ltrLeaks'] > 0: issues.append(f"LTR_LEAKS:{tpl['ar']['ltrLeaks']}")
            if tpl['fr']['nan'] > 0: issues.append(f"FR_NaN:{tpl['fr']['nan']}")
            s = ' '.join(issues) if issues else 'CLEAN'

            print(f'  {slug}: {len(d["blocks"])} sections, h={d["h"]}px, nan={d["nan"]}, hid={d["hidden"]} | mob_w={tpl["mobile"]["w"]} | ar={tpl["ar"]["dir"]} | {s}')

    browser.close()

with open('docs/b12_deep_audit.json', 'w') as f:
    json.dump(ALL, f, indent=2, ensure_ascii=False, default=str)

# Family summaries
print('\n' + '='*80)
for fam in FAMILIES:
    items = {k: v for k, v in ALL.items() if k.startswith(fam.replace('-', '')[:4]) or k.startswith(fam[:4])}
    if not items:
        # Try matching by checking slug prefix
        items = {}
        for k, v in ALL.items():
            slug_fam = k.split('-')[0]
            if slug_fam in fam.replace('-', ''):
                items[k] = v
    total = len(items)
    clean = sum(1 for v in items.values()
                if v['desktop']['nan'] == 0 and v['desktop']['hidden'] == 0
                and not v['mobile']['overflow'] and v['ar']['dir'] == 'rtl')
    empties_total = sum(len([b for b in v['desktop']['blocks'] if b['empty']]) for v in items.values())
    ws_total = sum(len([b for b in v['desktop']['blocks'] if b['excessWS']]) for v in items.values())
    print(f'{fam}: {total} templates | clean={clean}/{total} | empty_blocks={empties_total} | excess_ws={ws_total}')
