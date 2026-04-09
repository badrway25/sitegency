"""Batch 13: Section-by-section quality audit for micro-polish."""
import sys, time, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'marketweb.settings'
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
import django; django.setup()
from catalog.models import TemplateItem
from playwright.sync_api import sync_playwright

FAMILIES = ['medical', 'restaurant', 'e-commerce']
BASE = 'http://127.0.0.1:8000'
ALL = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for fam in FAMILIES:
        slugs = list(TemplateItem.objects.filter(
            category__slug=fam, is_active=True
        ).order_by('slug').values_list('slug', flat=True))

        for slug in slugs:
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.goto(f'{BASE}/it/preview/{slug}/', wait_until='networkidle', timeout=30000)
            time.sleep(7)

            sections = page.evaluate("""() => {
                var results = [];
                // Find ALL structural blocks at section level
                var candidates = document.querySelectorAll(
                    'section, .site-section, .ftco-section, [class*="section"], ' +
                    'header, footer, .footer, .ftco-footer, .site-footer, ' +
                    '[class*="area"], [class*="block"], [class*="wrapper"]'
                );
                var seen = new Set();
                candidates.forEach(function(el) {
                    if (seen.has(el)) return;
                    seen.add(el);
                    var r = el.getBoundingClientRect();
                    if (r.height < 30 || r.width < 200) return;
                    var s = getComputedStyle(el);
                    if (s.display === 'none') return;

                    var text = (el.innerText || '').trim();
                    var h1 = el.querySelector('h1');
                    var h2 = el.querySelector('h2');
                    var h3 = el.querySelector('h3');
                    var imgs = el.querySelectorAll('img');
                    var visImgs = 0;
                    imgs.forEach(function(i) { if (i.getBoundingClientRect().width > 40) visImgs++; });
                    var btns = el.querySelectorAll('.btn, a.btn, button, [class*="button"], a[class*="more-"]');
                    var cards = el.querySelectorAll('.card, [class*="card"], [class*="feature"], [class*="service-box"]');

                    // Quality indicators
                    var issues = [];

                    // 1. Empty/near-empty
                    if (text.length < 15 && visImgs === 0 && r.height > 100) {
                        issues.push('EMPTY');
                    }

                    // 2. Excessive padding (>80px per side for non-hero)
                    var padTop = parseInt(s.paddingTop);
                    var padBot = parseInt(s.paddingBottom);
                    if (padTop > 80 || padBot > 80) {
                        issues.push('HIGH_PAD:' + padTop + '/' + padBot);
                    }

                    // 3. No visual hierarchy (large section with no headings)
                    if (r.height > 300 && !h1 && !h2 && !h3 && text.length > 50) {
                        issues.push('NO_HEADING');
                    }

                    // 4. Heading too large for context (>40px in non-hero)
                    if (h2) {
                        var h2s = getComputedStyle(h2);
                        var h2size = parseFloat(h2s.fontSize);
                        if (h2size > 45 && r.height < 500) {
                            issues.push('H2_TOO_LARGE:' + Math.round(h2size) + 'px');
                        }
                    }

                    // 5. Poor contrast (light text on light bg or dark on dark)
                    var bgR = s.backgroundColor.match(/\d+/g);
                    var txtR = s.color.match(/\d+/g);
                    if (bgR && txtR) {
                        var bgLum = (parseInt(bgR[0]) * 299 + parseInt(bgR[1]) * 587 + parseInt(bgR[2]) * 114) / 1000;
                        var txtLum = (parseInt(txtR[0]) * 299 + parseInt(txtR[1]) * 587 + parseInt(txtR[2]) * 114) / 1000;
                        var contrast = Math.abs(bgLum - txtLum);
                        if (contrast < 40 && text.length > 20) {
                            issues.push('LOW_CONTRAST:' + Math.round(contrast));
                        }
                    }

                    // 6. Section with cards but inconsistent sizing
                    if (cards.length > 2) {
                        var heights = [];
                        cards.forEach(function(c) { heights.push(Math.round(c.getBoundingClientRect().height)); });
                        var maxH = Math.max.apply(null, heights);
                        var minH = Math.min.apply(null, heights);
                        if (maxH > 0 && (maxH - minH) / maxH > 0.3) {
                            issues.push('CARD_UNEVEN:' + minH + '-' + maxH);
                        }
                    }

                    // 7. Images with aspect ratio issues
                    var imgIssues = 0;
                    imgs.forEach(function(img) {
                        var ir = img.getBoundingClientRect();
                        if (ir.width > 100 && ir.height > 0) {
                            var ratio = ir.width / ir.height;
                            if (ratio > 4 || ratio < 0.2) imgIssues++;
                        }
                    });
                    if (imgIssues > 0) issues.push('IMG_RATIO:' + imgIssues);

                    results.push({
                        cls: (el.className || '').substring(0, 45),
                        tag: el.tagName,
                        h: Math.round(r.height),
                        top: Math.round(r.top + window.scrollY),
                        h2: h2 ? h2.textContent.trim().substring(0, 25) : '',
                        imgs: visImgs,
                        btns: btns.length,
                        cards: cards.length,
                        textLen: Math.min(text.length, 999),
                        issues: issues
                    });
                });
                results.sort(function(a, b) { return a.top - b.top; });
                return results;
            }""")
            page.close()

            # Analyze
            total_sections = len(sections)
            weak_sections = [s for s in sections if s['issues']]
            weak_count = len(weak_sections)

            ALL[slug] = {
                'family': fam,
                'total_sections': total_sections,
                'weak_sections': weak_count,
                'sections': sections,
                'issues_summary': {}
            }

            # Count issue types
            for s in sections:
                for iss in s['issues']:
                    key = iss.split(':')[0]
                    ALL[slug]['issues_summary'][key] = ALL[slug]['issues_summary'].get(key, 0) + 1

            issues_str = ', '.join(f'{k}:{v}' for k, v in ALL[slug]['issues_summary'].items()) if ALL[slug]['issues_summary'] else 'CLEAN'
            print(f'  {slug}: {total_sections} sections, {weak_count} weak | {issues_str}')

    browser.close()

# Save
with open('docs/b13_micropolish.json', 'w') as f:
    json.dump(ALL, f, indent=2, ensure_ascii=False, default=str)

# Summary
print('\n' + '='*80)
print('MICRO-POLISH SUMMARY')
print('='*80)
total_sections = sum(v['total_sections'] for v in ALL.values())
total_weak = sum(v['weak_sections'] for v in ALL.values())
issue_counts = {}
for v in ALL.values():
    for k, c in v['issues_summary'].items():
        issue_counts[k] = issue_counts.get(k, 0) + c

print(f'Total sections reviewed: {total_sections}')
print(f'Weak sections found: {total_weak} ({round(total_weak/total_sections*100, 1)}%)')
print(f'Issue breakdown:')
for k, v in sorted(issue_counts.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')

for fam in FAMILIES:
    fam_items = {k: v for k, v in ALL.items() if v['family'] == fam}
    fam_sections = sum(v['total_sections'] for v in fam_items.values())
    fam_weak = sum(v['weak_sections'] for v in fam_items.values())
    clean = sum(1 for v in fam_items.values() if v['weak_sections'] == 0)
    print(f'\n{fam}: {fam_sections} sections, {fam_weak} weak, {clean}/{len(fam_items)} fully clean')
