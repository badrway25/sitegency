"""
Preview & customization engine.

Responsibilities:
- Serve the raw HTML of an imported template through Django (not as static files),
  so we can rewrite asset URLs, strip demo links, inject branding and live
  customization overrides.
- Serve binary/text assets from the template source directory with correct MIME types.
- Apply a DemoSession's customization data as a <style> + <script> injection that
  swaps text, colors and images at runtime via CSS selectors.
"""
from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse, quote as urlquote

from bs4 import BeautifulSoup, NavigableString
from django.conf import settings
from django.http import Http404, FileResponse, HttpResponse
from django.urls import reverse
from django.utils.translation import get_language

from catalog.models import TemplateItem
from .translation_map import build_lookup, translate_text
from .content_pool import pool_for


# Same keyword set used by scanner — double protection
BLOCKED_NAVIGATION_KEYWORDS = {
    'elements', 'element', 'typography', 'typo', 'shortcode', 'components',
    'buttons', 'tables', 'bootstrap', 'styleguide', 'style-guide',
    'ui-elements', 'ui-kit', 'form-elements', '404',
}


class PreviewEngine:
    """Serves a TemplateItem's HTML page through Django with transformations."""

    def __init__(self, template: TemplateItem, page_slug: Optional[str] = None,
                 session_data: Optional[Dict] = None, is_customizer: bool = False):
        self.template = template
        self.page_slug = page_slug
        self.session_data = session_data or {}
        self.is_customizer = is_customizer

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    @property
    def template_root(self) -> Path:
        return Path(settings.TEMPLATE_SOURCE_DIR) / self.template.source_dir

    def resolve_page(self):
        """Return the TemplatePage being previewed, falling back to entry."""
        if self.page_slug:
            page = self.template.pages.filter(slug=self.page_slug, is_public=True).first()
            if page:
                return page
        return self.template.pages.filter(is_entry=True).first() or \
               self.template.pages.filter(is_public=True).first()

    def asset_base_url(self) -> str:
        # Build manually because regex requires at least 1 char for asset_path
        return f"/assets/{self.template.slug}/"

    def page_url(self, page_slug: str) -> str:
        if self.is_customizer:
            return reverse('customizer:customize_page',
                           kwargs={'slug': self.template.slug, 'page': page_slug})
        return reverse('catalog:template_preview_page',
                       kwargs={'slug': self.template.slug, 'page': page_slug})

    # ------------------------------------------------------------------
    # Main render
    # ------------------------------------------------------------------
    def render(self) -> HttpResponse:
        page = self.resolve_page()
        if not page:
            raise Http404("Template page not found")

        file_path = self.template_root / page.file_path
        if not file_path.exists():
            raise Http404(f"Source file missing: {file_path}")

        try:
            html = file_path.read_text(encoding='utf-8', errors='ignore')
        except OSError as e:
            raise Http404(str(e))

        soup = BeautifulSoup(html, 'html.parser')

        self._rewrite_assets(soup)
        self._rewrite_internal_links(soup)
        self._strip_blocked_nav_links(soup)
        self._deduplicate_nav(soup)
        self._strip_original_credits(soup)
        self._translate_content(soup)
        self._replace_content_with_pool(soup)
        self._rebrand_footer(soup)
        self._inject_base_tag(soup)
        self._inject_rtl(soup)
        self._inject_differentiation_layer(soup)
        self._inject_runtime_translator(soup)
        self._inject_badrway_footer(soup)
        self._inject_customizer_runtime(soup)
        self._replace_hero_images(soup)
        self._inject_brand_identity(soup)
        self._cleanup_placeholder_text(soup)
        self._hide_empty_sections(soup)
        self._inject_premium_content(soup)
        self._inject_scroll_animations(soup)
        self._inject_premium_interactivity(soup)
        self._neutralize_google_maps(soup)
        self._inject_plugin_fallbacks(soup)

        return HttpResponse(str(soup), content_type='text/html; charset=utf-8')

    # ------------------------------------------------------------------
    # Transformations
    # ------------------------------------------------------------------
    def _rewrite_assets(self, soup: BeautifulSoup) -> None:
        """Point <link>, <script>, <img>, <source> at the Django asset endpoint."""
        asset_base = self.asset_base_url()

        def rewrite_attr(tag, attr):
            url = _safe_get_attr(tag, attr)
            if not url or not isinstance(url, str):
                return
            if url.startswith(('http://', 'https://', '//', 'data:', 'mailto:',
                               'tel:', '#', 'javascript:')):
                return
            clean = url.lstrip('/').lstrip('./')
            # Check CDN library map first — redirect to CDN for common libs
            cdn = _cdn_redirect_for(clean)
            if cdn:
                try:
                    tag[attr] = cdn
                    return
                except Exception:
                    pass
            try:
                tag[attr] = asset_base + urlquote(clean, safe='/')
            except Exception:
                pass

        for tag in soup.find_all(['link', 'script', 'img', 'source', 'video', 'audio']):
            if not getattr(tag, 'attrs', None):
                continue
            for attr in ('href', 'src', 'srcset'):
                val = _safe_get_attr(tag, attr)
                if not val:
                    continue
                if attr == 'srcset' and isinstance(val, str):
                    try:
                        new_parts = []
                        for part in val.split(','):
                            bits = part.strip().split(' ', 1)
                            if bits and not bits[0].startswith(('http', 'data:', '//')):
                                bits[0] = asset_base + urlquote(bits[0].lstrip('/').lstrip('./'), safe='/')
                            new_parts.append(' '.join(bits))
                        tag[attr] = ', '.join(new_parts)
                    except Exception:
                        pass
                else:
                    rewrite_attr(tag, attr)

        # Rewrite data-* attributes that commonly reference images
        # (lazy loading / JS-driven backgrounds used by many Bootstrap themes)
        DATA_ATTRS = [
            'data-background', 'data-bg', 'data-bg-image', 'data-bg-img',
            'data-src', 'data-srcset', 'data-image', 'data-image-src',
            'data-img', 'data-lazy', 'data-lazy-src', 'data-original',
            'data-poster', 'data-thumb', 'data-bg-color-image',
        ]
        for tag in soup.find_all(True):
            if not getattr(tag, 'attrs', None):
                continue
            for attr in DATA_ATTRS:
                val = _safe_get_attr(tag, attr)
                if not val or not isinstance(val, str):
                    continue
                v = val.strip()
                if v.startswith(('http://', 'https://', '//', 'data:', '#')):
                    continue
                if not re.search(r'\.(jpe?g|png|gif|svg|webp|ico|bmp|tiff?)(\?|$)', v, re.I):
                    continue
                clean = v.lstrip('/').lstrip('./')
                try:
                    tag[attr] = asset_base + urlquote(clean, safe='/')
                except Exception:
                    pass

        # Rewrite inline url(...) in style attributes
        # Handles both relative ("images/x.jpg") AND absolute ("/images/x.jpg") paths.
        for tag in soup.find_all(style=True):
            style = _safe_get_attr(tag, 'style')
            if not style or not isinstance(style, str):
                continue
            try:
                tag['style'] = re.sub(
                    r'url\(([\'"]?)(?!https?://|//|data:)([^\'")]+)\1\)',
                    lambda m: f"url({m.group(1)}{asset_base}{m.group(2).lstrip('/').lstrip('./')}{m.group(1)})",
                    style,
                )
            except Exception:
                pass

        # Also rewrite url() inside <style> blocks (embedded CSS)
        for style_tag in soup.find_all('style'):
            if not style_tag.string:
                continue
            try:
                style_tag.string = re.sub(
                    r'url\(([\'"]?)(?!https?://|//|data:)([^\'")]+)\1\)',
                    lambda m: f"url({m.group(1)}{asset_base}{m.group(2).lstrip('/').lstrip('./')}{m.group(1)})",
                    style_tag.string,
                )
            except Exception:
                pass

    def _rewrite_internal_links(self, soup: BeautifulSoup) -> None:
        """Make <a href="about.html"> point to Django preview route.

        CRITICAL: any internal link that doesn't match a public page is redirected
        to '#' so the user NEVER sees a 404 during preview.
        """
        try:
            public_pages = {p.file_path.lower(): p for p in self.template.pages.filter(is_public=True)}
        except Exception:
            public_pages = {}

        # Build entry page URL for fallback
        entry_page = self.template.pages.filter(is_entry=True).first() or \
                     self.template.pages.filter(is_public=True).first()

        for a in soup.find_all('a'):
            href = _safe_get_attr(a, 'href')
            if not href or not isinstance(href, str):
                continue
            if href.startswith(('http://', 'https://', '//', '#', 'mailto:', 'tel:', 'javascript:')):
                continue
            # Skip image hrefs (handled by _replace_hero_images)
            if re.search(r'\.(jpe?g|png|webp|gif|svg|ico|bmp)(\?|$)', href, re.I):
                continue
            # Skip asset hrefs (css, js, fonts, etc.)
            if re.search(r'\.(css|js|woff2?|ttf|otf|eot|mp4|mp3|pdf)(\?|$)', href, re.I):
                continue

            clean = href.split('?')[0].split('#')[0].lstrip('./').lstrip('/').lower()
            page = public_pages.get(clean)
            try:
                if page:
                    a['href'] = self.page_url(page.slug)
                else:
                    # No matching public page — neutralize to prevent 404
                    a['href'] = '#'
            except Exception:
                continue

    def _deduplicate_nav(self, soup: BeautifulSoup) -> None:
        """Remove ONLY clearly separate duplicate/offcanvas menus.

        CONSERVATIVE approach: only removes top-level sibling elements that
        are clearly offcanvas/mobile menus OUTSIDE the header. Never touches
        anything nested inside the header or inside a <nav>.
        """
        body = soup.find('body')
        if not body:
            return
        header = soup.find(['header'])
        if not header:
            return

        # Build signature from header's nav links
        header_links = header.find_all('a', href=True)
        if len(header_links) < 3:
            return
        header_sig = '|'.join(a.get('href', '') for a in header_links[:8])

        # Only look at TOP-LEVEL body children that are NOT the header
        # and are clearly offcanvas/sidebar menus
        OFFCANVAS_KEYWORDS = ('offcanvas', 'mobile-menu', 'side-menu', 'slide-menu',
                              'canvas-menu', 'push-menu', 'overlay-menu', 'mobile-nav')
        for child in list(body.children):
            if not hasattr(child, 'name') or not child.name:
                continue
            if child == header or child.name in ('script', 'style', 'link'):
                continue
            # Check if this element is clearly an offcanvas/mobile menu
            cls = ' '.join(child.get('class', []) or []).lower()
            is_offcanvas = any(kw in cls for kw in OFFCANVAS_KEYWORDS)
            if not is_offcanvas:
                continue
            # Verify it has similar links to the header (it's a duplicate)
            child_links = child.find_all('a', href=True)
            if len(child_links) < 3:
                continue
            child_sig = '|'.join(a.get('href', '') for a in child_links[:8])
            if child_sig == header_sig:
                try:
                    child.decompose()
                except Exception:
                    pass

    def _strip_blocked_nav_links(self, soup: BeautifulSoup) -> None:
        """Remove nav items that link to demo/element/typography pages,
        and strip generic placeholder nav labels (Menu One, Sub Menu, etc.)."""
        # Placeholder nav labels that template authors leave in as demo content
        PLACEHOLDER_LABELS = {
            'menu one', 'menu two', 'menu three', 'menu four',
            'sub menu one', 'sub menu two', 'sub menu three',
            'sub menu 1', 'sub menu 2', 'sub menu 3',
            'deep drop down 1', 'deep drop down 2', 'deep drop down 3',
            'deep drop down 4', 'deep drop down 5',
            'drop down 1', 'drop down 2', 'drop down 3',
            '- home', 'home (current)', 'pagine', 'pages',
        }

        for a in list(soup.find_all('a')):
            try:
                text = (a.get_text() or '').strip().lower() if hasattr(a, 'get_text') else ''
            except Exception:
                text = ''
            href = _safe_get_attr(a, 'href', '') or ''
            if not isinstance(href, str):
                href = ''
            href = href.lower()
            combined = f"{text} {href}"
            should_remove = (
                any(kw in combined for kw in BLOCKED_NAVIGATION_KEYWORDS) or
                text in PLACEHOLDER_LABELS
            )
            if should_remove:
                try:
                    parent = a.find_parent(['li', 'nav', 'ul'])
                    if parent and parent.name == 'li':
                        parent.decompose()
                    elif parent and parent.name in ('nav', 'ul'):
                        a.decompose()
                except Exception:
                    continue

    def _strip_original_credits(self, soup: BeautifulSoup) -> None:
        """Remove credits / copyright lines from original template authors
        (Colorlib, Themewagon, FreeHTML5, TemplateMo, ThemeWagon, etc.).

        Replace any matching block with a clean Sitegency credit. Handles:
        - <a href="https://colorlib.com">Colorlib</a>
        - "This template is made with love by Colorlib"
        - "Copyright © 2024 All rights reserved"
        """
        ORIGINAL_CREDITS = [
            'colorlib', 'themewagon', 'freehtml5', 'templatemo', 'template mo',
            'uideck', 'htmlcodex', 'html5up', 'bootstrapmade', 'untree', 'templateshub',
            'startbootstrap', 'themesberg', 'free-css', 'w3layouts', 'themefisher',
            'w3schools', 'wrapbootstrap', 'mozello', 'themezaa', 'themerella',
            'themeforest', 'codewithtea', 'creativetim', 'tooplate', 'vironeer',
            'ausperio', 'gettemplate', 'htmlmag', 'tutorialzine',
        ]

        # 1) Remove HTML comments that mention forbidden brands
        from bs4 import Comment
        for comment in list(soup.find_all(string=lambda s: isinstance(s, Comment))):
            try:
                if any(kw in str(comment).lower() for kw in ORIGINAL_CREDITS):
                    comment.extract()
            except Exception:
                pass

        # 2) Remove <a> tags pointing to credit domains / containing credit text
        for a in list(soup.find_all('a')):
            href = _safe_get_attr(a, 'href') or ''
            if not isinstance(href, str):
                continue
            href_l = href.lower()
            try:
                text_l = (a.get_text() or '').lower()
            except Exception:
                text_l = ''
            if any(kw in href_l for kw in ORIGINAL_CREDITS) or \
               any(kw in text_l for kw in ORIGINAL_CREDITS):
                try:
                    a.decompose()
                except Exception:
                    pass

        # 3) Remove entire <p>/<div>/<span> blocks that contain copyright text
        # Strategy: walk elements; if their *full text* matches a copyright
        # pattern, remove the whole element (not just the matching text node).
        FULL_BLOCK_PATTERNS = [
            re.compile(r'copyright[\s\S]*?(?:all\s*)?rights?\s*reserved', re.I),
            re.compile(r'this\s+template\s+is\s+(?:made|designed)', re.I),
            re.compile(r'made\s+with\s+(?:love|heart|[\u2764\u2665\u2661])', re.I),
            re.compile(r'designed\s+(?:with|by)\s+\w', re.I),
            re.compile(r'template\s+by\s+\w', re.I),
            re.compile(r'powered\s+by\s+\w', re.I),
        ]

        def full_text(el):
            try:
                return (el.get_text(' ', strip=True) or '').lower()
            except Exception:
                return ''

        # Check small leaf blocks in footer-like areas
        for tag_name in ('p', 'div', 'span', 'small', 'li'):
            for el in list(soup.find_all(tag_name)):
                txt = full_text(el)
                if not txt or len(txt) > 400:
                    continue
                # If the block contains a copyright phrase OR any forbidden brand
                contains_brand = any(kw in txt for kw in ORIGINAL_CREDITS)
                matches_pattern = any(p.search(txt) for p in FULL_BLOCK_PATTERNS)
                if contains_brand or matches_pattern:
                    try:
                        el.decompose()
                    except Exception:
                        pass

        # 3b) Sanitize <title>, meta descriptions and attribute values (alt/title)
        for title_tag in soup.find_all('title'):
            try:
                txt = title_tag.get_text() or ''
                low = txt.lower()
                if any(kw in low for kw in ORIGINAL_CREDITS):
                    # Replace with template name or generic
                    title_tag.string = f"{self.template.name} — Sitegency"
            except Exception:
                pass

        for meta in soup.find_all('meta'):
            try:
                name = (_safe_get_attr(meta, 'name') or '').lower()
                content = _safe_get_attr(meta, 'content') or ''
                if not isinstance(content, str):
                    continue
                low = content.lower()
                if name in ('author', 'description', 'keywords') and \
                   any(kw in low for kw in ORIGINAL_CREDITS):
                    meta['content'] = ''
            except Exception:
                pass

        # Sanitize alt, title, aria-label attributes on any tag
        for tag in soup.find_all(True):
            if not getattr(tag, 'attrs', None):
                continue
            for attr in ('alt', 'title', 'aria-label'):
                val = _safe_get_attr(tag, attr)
                if val and isinstance(val, str):
                    low = val.lower()
                    if any(kw in low for kw in ORIGINAL_CREDITS):
                        try:
                            tag[attr] = ''
                        except Exception:
                            pass

        # 4) Final pass: remove any remaining text nodes containing forbidden words
        # AND comment-like separator text (===, ---, ###)
        COMMENT_PATTERN = re.compile(r'^\s*[=\-#~*]{4,}.*[=\-#~*]{4,}\s*$')

        def clean_text_nodes(node, depth=0):
            if depth > 20:
                return
            try:
                for child in list(getattr(node, 'children', [])):
                    if isinstance(child, NavigableString):
                        orig = str(child)
                        low = orig.lower()
                        if any(kw in low for kw in ORIGINAL_CREDITS) or \
                           any(p.search(orig) for p in FULL_BLOCK_PATTERNS) or \
                           COMMENT_PATTERN.search(orig):
                            try:
                                child.replace_with('')
                            except Exception:
                                pass
                    else:
                        name = getattr(child, 'name', None)
                        if name in ('script', 'style'):
                            continue
                        clean_text_nodes(child, depth + 1)
            except Exception:
                return

        body = soup.find('body')
        if body:
            clean_text_nodes(body)

    def _replace_content_with_pool(self, soup: BeautifulSoup) -> None:
        """Deep content replacement for previews.

        For non-English locales: swap headings and paragraphs with locale-native
        industry-appropriate copy from CONTENT_POOL.

        For English: replace "Lorem ipsum" paragraphs with real English copy
        so previews never show placeholder text.
        """
        try:
            locale = (get_language() or 'en').split('-')[0]
        except Exception:
            locale = 'en'

        try:
            pool = pool_for(self.template.category.name, locale)
        except Exception:
            pool = {}

        # For English, also try to get English pool for Lorem ipsum replacement
        en_pool = None
        if locale == 'en':
            try:
                en_pool = pool_for(self.template.category.name, 'en')
            except Exception:
                en_pool = {}
            if not en_pool:
                return
            pool = en_pool

        if not pool:
            return
        if not pool:
            return

        h1_pool = pool.get('h1', [])
        h2_pool = pool.get('h2', [])
        h3_pool = pool.get('h3', [])
        p_short_pool = pool.get('p_short', [])
        p_long_pool = pool.get('p_long', [])

        # Elements that are purely structural/decorative text wrappers
        # (safe to clear their text when parent heading is replaced)
        INLINE_TEXT_TAGS = {'span', 'em', 'strong', 'b', 'i', 'u', 'mark',
                           'small', 'sub', 'sup', 'del', 's'}
        # Elements that must NEVER be touched (media, icons, links)
        PRESERVE_TAGS = {'img', 'svg', 'picture', 'video', 'iframe',
                         'canvas', 'a', 'button', 'input', 'select',
                         'textarea', 'br', 'hr'}

        def is_icon_element(el):
            """True if element is an icon (Font Awesome, flaticon, etc.)"""
            cls = ' '.join(el.get('class', []) or []).lower()
            return any(p in cls for p in ('fa-', 'fa ', 'fas ', 'far ', 'fab ',
                                          'flaticon', 'icon-', 'ti-', 'bi-',
                                          'ion-', 'icofont'))

        def replace_text_content(el, new_text):
            """Replace the text content of a heading/paragraph while preserving
            icons, images, and other media. Also clears text inside child <a>
            links to prevent "FrenchHeadingOriginal English Title" concatenation.
            """
            try:
                first_replaced = False
                for child in list(el.children):
                    if isinstance(child, NavigableString):
                        if not first_replaced:
                            child.replace_with(new_text)
                            first_replaced = True
                        else:
                            child.replace_with('')
                    elif hasattr(child, 'name'):
                        name = (child.name or '').lower()
                        # Preserve icons and media elements
                        if name in ('img', 'svg', 'picture', 'video', 'iframe',
                                    'canvas', 'button', 'input', 'br', 'hr'):
                            continue
                        if is_icon_element(child):
                            continue
                        # For <a> links: clear their text (keep the link element)
                        if name == 'a':
                            for a_child in list(child.children):
                                if isinstance(a_child, NavigableString):
                                    a_child.replace_with('')
                                elif hasattr(a_child, 'name') and a_child.name in INLINE_TEXT_TAGS:
                                    if not is_icon_element(a_child):
                                        a_child.string = ''
                            continue
                        # For inline text wrappers: clear their text
                        if name in INLINE_TEXT_TAGS:
                            has_media = any(
                                getattr(d, 'name', None) in ('img', 'svg', 'picture')
                                or is_icon_element(d)
                                for d in child.descendants
                                if hasattr(d, 'name') and d.name
                            )
                            if not has_media:
                                child.string = ''
                # If no text node existed, prepend the text
                if not first_replaced:
                    el.insert(0, new_text)
            except Exception:
                pass

        # ============================================================
        # CONSERVATIVE CONTENT REPLACEMENT STRATEGY
        # ============================================================
        # Only replace content that is clearly "body copy" and won't break
        # card grids, badges, buttons, or visual components.
        #
        # Rules:
        # - Replace ONLY the first H1 (hero headline)
        # - Replace up to 3 section-level H2s (not inside cards/grid items)
        # - DO NOT replace H3/H4/H5/H6 (these are typically card titles,
        #   feature names, team member names — replacing them causes
        #   card height misalignment and content incoherence)
        # - Replace standalone <p> with >60 chars (body paragraphs)
        # - DO NOT replace <p> inside card grids (causes height mismatch)
        # - DO NOT replace spans, badges, tags, buttons
        # - Mark replaced elements with data-sg-replaced to prevent
        #   _translate_content from double-processing
        # ============================================================

        # Hints for repeated card/grid ITEMS — must be specific enough
        # to NOT match Bootstrap utility classes like 'align-items-center'.
        # We check individual CSS classes, not substrings of the full class string.
        CARD_CLASS_EXACT = {
            'card', 'card-body', 'card-text', 'card-content',
            'grid-item', 'masonry-item',
            'team-member', 'team-card', 'member-card', 'team-item',
            'pricing-card', 'pricing-table', 'price-card', 'pricing-item',
            'testimonial-item', 'review-card', 'testi-card',
            'portfolio-item', 'project-item', 'work-item',
            'blog-card', 'blog-item', 'post-card', 'post-item',
            'news-item', 'news-card',
            'feature-box', 'feature-item', 'service-box', 'service-item',
            'single-service', 'single-feature', 'single-team',
            # Counter/stat elements — NEVER replace (breaks counter plugins)
            'counter', 'counter_item', 'counter-item', 'count-item',
            'funfact', 'fun-factor', 'fun-fact', 'funfact-item',
            'counter-box', 'count-box', 'stat-item', 'stats-item',
        }
        SKIP_PARENTS = {'nav', 'menu', 'button', 'form', 'select', 'input',
                        'a', 'label', 'figcaption'}

        def is_inside_card_grid(el):
            """Check if element is inside a repeated card/grid structure.
            Uses exact class name matching to avoid false positives with
            Bootstrap utility classes like 'align-items-center'."""
            ancestor = el.parent
            depth = 0
            while ancestor and depth < 8:
                classes = [c.lower() for c in (ancestor.get('class') or [])]
                if any(c in CARD_CLASS_EXACT for c in classes):
                    return True
                ancestor = ancestor.parent
                depth += 1
            return False

        def is_inside_skip_parent(el):
            ancestor = el.parent
            depth = 0
            while ancestor and depth < 8:
                if getattr(ancestor, 'name', None) in SKIP_PARENTS:
                    return True
                ancestor = ancestor.parent
                depth += 1
            return False

        def safe_replace(el, new_text):
            """Replace text and mark element to prevent double-processing."""
            replace_text_content(el, new_text)
            try:
                el['data-sg-replaced'] = '1'
            except Exception:
                pass

        # --- H1: replace section-level H1s, but NOT logo/brand H1s ---
        # For English: skip (keep original headings, they're usually real content)
        LOGO_CLASS_KEYWORDS = ('logo', 'brand', 'navbar', 'site-title', 'site-name',
                               'counter', 'count', 'number', 'timer', 'funfact', 'stat')
        if h1_pool and locale != 'en':
            h1_count = 0
            for h1 in soup.find_all('h1'):
                try:
                    txt = h1.get_text(strip=True)
                except Exception:
                    continue
                if not txt or not (2 < len(txt) < 150):
                    continue
                if is_inside_card_grid(h1):
                    continue
                if is_inside_skip_parent(h1):
                    continue
                # Skip logo/brand H1s
                h1_cls = ' '.join(h1.get('class', []) or []).lower()
                if any(kw in h1_cls for kw in LOGO_CLASS_KEYWORDS):
                    continue
                safe_replace(h1, h1_pool[h1_count % len(h1_pool)])
                h1_count += 1

        # --- H2: replace section-level H2s (NOT for English — keep original headings) ---
        COUNTER_KEYWORDS = ('counter', 'count', 'number', 'timer', 'funfact',
                            'fun-fact', 'stat', 'fact', 'digit')
        def _is_counter_context(el):
            """Check if element or its ancestors have counter-related classes."""
            # Check self
            el_cls = ' '.join(el.get('class', []) or []).lower()
            if any(kw in el_cls for kw in COUNTER_KEYWORDS):
                return True
            # Check if text is numeric (e.g. "350", "99%", "$1.2M", "5,000+")
            txt = el.get_text(strip=True)
            if txt and re.match(r'^[\d\s$€£%+,.\-kKmMbB/]+$', txt):
                return True
            # Check ancestors up to 4 levels
            ancestor = el.parent
            depth = 0
            while ancestor and depth < 4:
                anc_cls = ' '.join(ancestor.get('class', []) or []).lower()
                if any(kw in anc_cls for kw in COUNTER_KEYWORDS):
                    return True
                ancestor = ancestor.parent
                depth += 1
            return False

        if h2_pool and locale != 'en':
            h2_count = 0
            for h2 in soup.find_all('h2'):
                try:
                    txt = h2.get_text(strip=True)
                except Exception:
                    continue
                if not txt or not (2 < len(txt) < 150):
                    continue
                if is_inside_card_grid(h2):
                    continue
                if is_inside_skip_parent(h2):
                    continue
                if _is_counter_context(h2):
                    continue
                safe_replace(h2, h2_pool[h2_count % len(h2_pool)])
                h2_count += 1

        # --- H3/H4/H5/H6: replace ONLY section-level ones (NOT for English) ---
        if h3_pool and locale != 'en':
            h_count = 0
            for tag_name in ('h3', 'h4', 'h5', 'h6'):
                for h in soup.find_all(tag_name):
                    try:
                        txt = h.get_text(strip=True)
                    except Exception:
                        continue
                    if not txt or not (2 < len(txt) < 150):
                        continue
                    # PROTECT card titles — skip if inside a card grid
                    if is_inside_card_grid(h):
                        continue
                    if is_inside_skip_parent(h):
                        continue
                    if _is_counter_context(h):
                        continue
                    safe_replace(h, h3_pool[h_count % len(h3_pool)])
                    h_count += 1

        # --- Paragraphs: replace standalone body paragraphs (NOT in cards) ---
        # For English: only replace "Lorem ipsum" placeholder text
        # For other locales: replace all long paragraphs
        PLACEHOLDER_MARKERS = ('lorem ipsum', 'dolor sit amet', 'consectetur adipisicing',
                               'consectetur adipiscing', 'sed do eiusmod', 'ut enim ad minim',
                               'far far away, behind the word', 'countries vokalia',
                               'there live the blind texts', 'blind texts',
                               'officia quaerat eaque', 'possimus aut consequuntur',
                               'dolorum esse odio', 'architecto sint')
        if p_long_pool or p_short_pool:
            para_idx = 0
            MAX_PARAGRAPHS = 30 if locale == 'en' else 12  # Higher for EN (only Lorem)
            for el in soup.find_all('p'):
                if para_idx >= MAX_PARAGRAPHS:
                    break
                try:
                    txt = el.get_text(' ', strip=True)
                except Exception:
                    continue
                if not txt or len(txt) < 60 or len(txt) > 500:
                    continue
                # For English locale, ONLY replace Lorem ipsum placeholders
                if locale == 'en':
                    if not any(m in txt.lower() for m in PLACEHOLDER_MARKERS):
                        continue
                # Skip card grid paragraphs
                if is_inside_card_grid(el):
                    continue
                if is_inside_skip_parent(el):
                    continue
                # Skip media-heavy wrappers
                try:
                    media = sum(1 for d in el.descendants
                                if getattr(d, 'name', None) in
                                ('img', 'picture', 'video', 'iframe'))
                    if media >= 1:
                        continue
                except Exception:
                    pass
                # Length-matched replacement
                if len(txt) < 170 and p_short_pool:
                    new = p_short_pool[para_idx % len(p_short_pool)]
                elif p_long_pool:
                    new = p_long_pool[para_idx % len(p_long_pool)]
                else:
                    continue
                safe_replace(el, new)
                para_idx += 1

        # NOTE: H3/H4/H5/H6 and spans are NOT replaced by pool content.
        # They will be handled by _translate_content (dictionary-based
        # word-by-word translation) which preserves original structure,
        # length, and visual balance much better than pool replacement.

    def _rebrand_footer(self, soup: BeautifulSoup) -> None:
        """After stripping credits, inject a clean localized Sitegency credit
        into the original footer so it never looks empty.

        We append a small <p> with translated text at the end of any <footer>
        element found in the document.
        """
        try:
            locale = (get_language() or 'en').split('-')[0]
        except Exception:
            locale = 'en'

        MESSAGES = {
            'en': '© {year} · Crafted and delivered by Sitegency — premium website templates for every professional.',
            'it': '© {year} · Creato e distribuito da Sitegency — template premium per ogni professionista.',
            'fr': '© {year} · Conçu et livré par Sitegency — templates premium pour chaque professionnel.',
            'ar': '© {year} · صُنع ويُقدَّم بواسطة بدرواي — قوالب فاخرة لكل محترف.',
        }
        from datetime import datetime
        msg = MESSAGES.get(locale, MESSAGES['en']).format(year=datetime.now().year)

        footers = soup.find_all('footer')
        for footer in footers:
            try:
                credit = soup.new_tag('p')
                credit['class'] = 'badrway-credit'
                credit['style'] = (
                    "text-align:center;padding:18px 16px;margin:0;"
                    "font-family:'Inter',system-ui,sans-serif;font-size:13px;"
                    "color:#9ca3af;border-top:1px solid rgba(255,255,255,.08);"
                    "letter-spacing:0.2px;"
                )
                credit.string = msg
                footer.append(credit)
            except Exception:
                pass

    def _translate_content(self, soup: BeautifulSoup) -> None:
        """Translate navigation labels, buttons, headings, footer text to the
        active Django locale using the phrase dictionary."""
        try:
            locale = get_language() or 'en'
        except Exception:
            locale = 'en'
        if locale.startswith('en'):
            return
        locale_short = locale.split('-')[0]
        lookup = build_lookup(locale_short)
        if not lookup:
            return

        # Walk text nodes but skip script/style/pre/code/noscript
        SKIP_TAGS = {'script', 'style', 'pre', 'code', 'noscript', 'textarea'}

        def walk(node):
            try:
                for child in list(getattr(node, 'children', [])):
                    if isinstance(child, NavigableString):
                        new_text = translate_text(str(child), lookup)
                        if new_text != str(child):
                            try:
                                child.replace_with(new_text)
                            except Exception:
                                pass
                    else:
                        name = getattr(child, 'name', None)
                        if name and name.lower() in SKIP_TAGS:
                            continue
                        # Skip elements already replaced by pool content
                        if _safe_get_attr(child, 'data-sg-replaced'):
                            continue
                        walk(child)
            except Exception:
                return

        body = soup.find('body')
        if body:
            walk(body)

        # Translate alt, title, placeholder, aria-label, and value on buttons
        for tag in soup.find_all(True):
            for attr in ('alt', 'title', 'placeholder', 'aria-label'):
                val = _safe_get_attr(tag, attr)
                if val and isinstance(val, str):
                    new = translate_text(val, lookup)
                    if new != val:
                        try:
                            tag[attr] = new
                        except Exception:
                            pass
            # Translate value attribute on submit/button inputs
            if getattr(tag, 'name', None) == 'input':
                input_type = (_safe_get_attr(tag, 'type') or '').lower()
                if input_type in ('submit', 'button'):
                    val = _safe_get_attr(tag, 'value')
                    if val and isinstance(val, str):
                        new = translate_text(val, lookup)
                        if new != val:
                            try:
                                tag['value'] = new
                            except Exception:
                                pass

        # Convert dollar prices to euro for IT/FR locales
        # (Original template pricing like "$49" → "€49")
        if locale_short in ('it', 'fr'):
            for node in body.descendants if body else []:
                if isinstance(node, NavigableString):
                    txt = str(node)
                    if '$' in txt and len(txt) < 30:
                        new_txt = re.sub(r'\$(\d)', r'€\1', txt)
                        if new_txt != txt:
                            try:
                                node.replace_with(new_txt)
                            except Exception:
                                pass

    def _inject_rtl(self, soup: BeautifulSoup) -> None:
        """Enable RTL for Arabic with surgical CSS overrides.

        Strategy:
        - Set dir="rtl" on <html> → browser does the heavy lifting
        - Inject a minimal RTL stylesheet that ONLY fixes known-broken patterns
          without forcing text-align on everything (which previously broke
          templates with custom text alignment)
        - Use Noto Kufi Arabic font with graceful fallback
        """
        try:
            locale = get_language() or 'en'
        except Exception:
            return
        if not locale.startswith('ar'):
            return
        html = soup.find('html')
        if html:
            try:
                html['dir'] = 'rtl'
                html['lang'] = 'ar'
            except Exception:
                pass
        head = soup.find('head')
        if head:
            # Load Noto Kufi Arabic from Google Fonts
            font_link = soup.new_tag('link')
            font_link['rel'] = 'stylesheet'
            font_link['href'] = ('https://fonts.googleapis.com/css2?'
                                 'family=Noto+Kufi+Arabic:wght@400;500;600;700&display=swap')
            head.append(font_link)

            style = soup.new_tag('style')
            style['data-bw'] = 'rtl-overrides'
            style.string = """
/* Sitegency RTL overrides — surgical, no global text-align forcing */
html[dir="rtl"] {
  direction: rtl;
}
html[dir="rtl"] body {
  font-family: 'Noto Kufi Arabic', 'Segoe UI', Tahoma, sans-serif;
  unicode-bidi: embed;
}
/* Headings and paragraphs inherit RTL naturally; only override font */
html[dir="rtl"] h1, html[dir="rtl"] h2, html[dir="rtl"] h3,
html[dir="rtl"] h4, html[dir="rtl"] h5, html[dir="rtl"] h6,
html[dir="rtl"] p, html[dir="rtl"] li, html[dir="rtl"] a,
html[dir="rtl"] span, html[dir="rtl"] button, html[dir="rtl"] label,
html[dir="rtl"] input, html[dir="rtl"] textarea {
  font-family: 'Noto Kufi Arabic', 'Segoe UI', Tahoma, sans-serif;
}
/* Keep numeric / latin content LTR where sensible */
html[dir="rtl"] .price, html[dir="rtl"] .phone,
html[dir="rtl"] [href^="tel:"], html[dir="rtl"] [href^="mailto:"],
html[dir="rtl"] code, html[dir="rtl"] pre {
  direction: ltr;
  unicode-bidi: isolate;
}
/* Mirror arrow icons typically used as right-chevrons */
html[dir="rtl"] .fa-arrow-right, html[dir="rtl"] .fa-chevron-right,
html[dir="rtl"] .bi-arrow-right, html[dir="rtl"] .bi-chevron-right,
html[dir="rtl"] .lnr-arrow-right, html[dir="rtl"] .lnr-chevron-right {
  transform: scaleX(-1);
  display: inline-block;
}
/* Avoid breaking inline flex/grid containers — let the template handle them */
"""
            head.append(style)

    def _inject_base_tag(self, soup: BeautifulSoup) -> None:
        """Add a <base> tag so relative URLs in inline scripts resolve correctly."""
        head = soup.find('head')
        if not head:
            return
        if head.find('base'):
            return
        base = soup.new_tag('base', href=self.asset_base_url())
        # Insert as first child
        head.insert(0, base)

        # Inject an early shim that silences deprecated `unload` warnings
        # emitted by legacy jQuery (1.x / 2.x) and older plugins. We transparently
        # redirect `unload` listeners to `pagehide` (the modern equivalent) so
        # functionality is preserved but Chrome's "Permissions policy violation"
        # Violation warning disappears.
        shim = soup.new_tag('script')
        shim.string = (
            "(function(){"
            "try{"
              "var origAdd=EventTarget.prototype.addEventListener;"
              "EventTarget.prototype.addEventListener=function(t,fn,opts){"
                "if(t==='unload')t='pagehide';"
                "return origAdd.call(this,t,fn,opts);"
              "};"
              "if(typeof window.onunload!=='undefined'){"
                "Object.defineProperty(window,'onunload',{set:function(v){"
                  "if(typeof v==='function')window.addEventListener('pagehide',v);"
                "},get:function(){return null;},configurable:true});"
              "}"
            "}catch(e){}"
            "})();"
        )
        head.insert(1, shim)

    def _inject_badrway_footer(self, soup: BeautifulSoup) -> None:
        """Inject a discreet Sitegency watermark / footer signature — localized."""
        body = soup.find('body')
        if not body:
            return

        # Localize the banner text per active locale
        try:
            locale = (get_language() or 'en').split('-')[0]
        except Exception:
            locale = 'en'

        BANNER_MESSAGES = {
            'en': ('Sitegency', 'LIVE PREVIEW · fully customizable'),
            'it': ('Sitegency', 'ANTEPRIMA LIVE · completamente personalizzabile'),
            'fr': ('Sitegency', 'APERÇU EN DIRECT · entièrement personnalisable'),
            'ar': ('بدرواي', 'معاينة مباشرة · قابل للتخصيص بالكامل'),
        }
        brand_label, preview_label = BANNER_MESSAGES.get(locale, BANNER_MESSAGES['en'])

        # RTL: position banner on left instead of right for Arabic
        side_style = 'left:16px' if locale == 'ar' else 'right:16px'
        dir_attr = ' dir="rtl"' if locale == 'ar' else ''

        banner_html = f"""
<div id="badrway-preview-banner"{dir_attr} style="
  position:fixed;bottom:16px;{side_style};z-index:2147483000;
  background:linear-gradient(135deg,#0f172a 0%,#6366f1 100%);
  color:#fff;padding:10px 18px;border-radius:999px;
  font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:12px;
  box-shadow:0 10px 40px -10px rgba(99,102,241,.6);
  display:flex;align-items:center;gap:8px;pointer-events:auto;
  backdrop-filter:blur(8px);">
  <span style="width:8px;height:8px;background:#22c55e;border-radius:50%;
    box-shadow:0 0 0 3px rgba(34,197,94,.25);animation:bwpulse 2s infinite;"></span>
  <span style="font-weight:600;letter-spacing:.5px;">{brand_label}</span>
  <span style="opacity:.7;">{preview_label}</span>
</div>
<style>@keyframes bwpulse{{0%,100%{{opacity:1}}50%{{opacity:.5}}}}
#badrway-preview-banner a{{color:#fff}}</style>
"""
        banner = BeautifulSoup(banner_html, 'html.parser')
        body.append(banner)

    def _inject_runtime_translator(self, soup: BeautifulSoup) -> None:
        """Inject a JS runtime that translates remaining English text nodes at
        load time, and uses MutationObserver to catch content added dynamically
        via JavaScript (sliders, modals, carousels, AJAX).

        The phrase dictionary is serialized as JSON and embedded in the page.
        The client script walks the DOM, translates matching text nodes, then
        observes mutations to keep translating new content.
        """
        try:
            locale = (get_language() or 'en').split('-')[0]
        except Exception:
            locale = 'en'
        if locale == 'en':
            return

        from .translation_map import PHRASE_TRANSLATIONS
        import json

        # Build a flat lookup {lowercase_english: localized}
        lookup = {}
        for src, variants in PHRASE_TRANSLATIONS.items():
            if locale in variants:
                lookup[src.lower()] = variants[locale]

        if not lookup:
            return

        body = soup.find('body')
        if not body:
            return

        script = soup.new_tag('script')
        script.string = (
            "(function(){"
            "var DICT=" + json.dumps(lookup, ensure_ascii=False) + ";"
            "var LOC=" + json.dumps(locale) + ";"
            "var SKIP={SCRIPT:1,STYLE:1,CODE:1,PRE:1,NOSCRIPT:1,TEXTAREA:1};"
            "function translate(t){"
              "if(!t||typeof t!=='string')return t;"
              "var s=t.trim();"
              "if(!s||s.length>120)return t;"
              "var low=s.toLowerCase();"
              "if(DICT[low])return t.replace(s,DICT[low]);"
              "var m=low.match(/^(.+?)[\\.\\!\\?:;,]+$/);"
              "if(m&&DICT[m[1]])return t.replace(s.slice(0,m[1].length),DICT[m[1]]);"
              "return t;"
            "}"
            "function walkNode(n){"
              "if(!n)return;"
              "if(n.nodeType===3){"
                "var p=n.parentNode;"
                "if(p&&SKIP[p.nodeName])return;"
                "var nw=translate(n.nodeValue);"
                "if(nw!==n.nodeValue)n.nodeValue=nw;"
                "return;"
              "}"
              "if(n.nodeType!==1)return;"
              "if(SKIP[n.nodeName])return;"
              "['alt','title','placeholder','aria-label','value'].forEach(function(a){"
                "if(n.hasAttribute&&n.hasAttribute(a)){"
                  "var v=n.getAttribute(a);"
                  "var nv=translate(v);"
                  "if(nv!==v)n.setAttribute(a,nv);"
                "}"
              "});"
              "if(n.tagName==='INPUT'&&(n.type==='button'||n.type==='submit')){"
                "var bv=translate(n.value);if(bv!==n.value)n.value=bv;"
              "}"
              "var c=n.childNodes;"
              "for(var i=0;i<c.length;i++)walkNode(c[i]);"
            "}"
            "function run(){walkNode(document.body);}"
            "if(document.readyState==='loading'){"
              "document.addEventListener('DOMContentLoaded',run);"
            "}else{run();}"
            "try{"
              "var obs=new MutationObserver(function(muts){"
                "muts.forEach(function(m){"
                  "m.addedNodes&&m.addedNodes.forEach(function(nd){walkNode(nd);});"
                  "if(m.type==='characterData'&&m.target){"
                    "var nv=translate(m.target.nodeValue);"
                    "if(nv!==m.target.nodeValue)m.target.nodeValue=nv;"
                  "}"
                "});"
              "});"
              "if(document.body)obs.observe(document.body,{childList:true,subtree:true,characterData:true});"
              "else document.addEventListener('DOMContentLoaded',function(){obs.observe(document.body,{childList:true,subtree:true,characterData:true});});"
            "}catch(e){}"
            "document.documentElement.setAttribute('lang',LOC);"
            "if(LOC==='ar')document.documentElement.setAttribute('dir','rtl');"
            "})();"
        )
        body.append(script)

    def _inject_differentiation_layer(self, soup: BeautifulSoup) -> None:
        """Inject a comprehensive premium stylesheet that deeply transforms every
        template into an ultra-premium, Sitegency-branded experience.

        This is NOT a gentle overlay — it's a dramatic visual transformation:
        - Premium fonts (Playfair Display + Plus Jakarta Sans)
        - Dual-hue accent system (unique per template)
        - Glassmorphism cards and navbar
        - Animated gradient buttons and CTAs
        - Dramatic hero overlays with mesh gradients
        - Premium shadows (layered depth)
        - Elegant typography hierarchy
        - Animated hover states
        - Grain textures on heroes
        - Premium scrollbar and selection
        - Section dividers and accent strips
        """
        head = soup.find('head')
        if not head:
            return

        # Deterministic per-template dual-hue system
        slug = getattr(self.template, 'slug', '')
        seed = sum(ord(c) for c in slug)
        # Primary hue: rich violet-to-rose spectrum
        primary_hues = [225, 235, 248, 258, 268, 278, 290, 300, 312, 325, 338, 210]
        hue = primary_hues[seed % len(primary_hues)]
        # Secondary hue: golden-ratio offset for complementary harmony
        hue2 = (hue + 137) % 360
        # Tertiary: triadic
        hue3 = (hue + 60) % 360

        # Layout variation: some templates get row-reverse hero
        flip_hero = (seed % 4 == 0)
        # Dark hero variant: some templates get dark hero text
        dark_hero = (seed % 3 != 0)

        # Detect dark-themed templates (body/html bg is very dark)
        is_dark_template = False
        for el in [soup.find('body'), soup.find('html')]:
            if el:
                style = el.get('style', '') or ''
                cls_str = ' '.join(el.get('class', []) or []).lower()
                # Check inline style for dark bg
                if any(c in style.lower() for c in ['background:#0', 'background: #0', 'background:#1',
                    'background-color:#0', 'background-color: #0', 'background-color:#1',
                    'background:black', 'background-color:black', 'background: black',
                    'background-color: rgb(0', 'background: rgb(0']):
                    is_dark_template = True
                # Check class hints
                if any(kw in cls_str for kw in ('dark', 'bg-dark', 'bg-black', 'dark-theme')):
                    is_dark_template = True
        # Also check <style> tags in head for body { background: dark }
        if not is_dark_template:
            for style_tag in soup.find_all('style')[:5]:
                txt = (style_tag.string or '')[:3000].lower()
                if 'body' in txt and ('background' in txt) and any(c in txt for c in ['#000', '#111', '#0b0', 'rgb(0']):
                    is_dark_template = True
                    break

        css = f"""
/* ================================================================
   SITEGENCY ULTRA-PREMIUM LAYER — {slug}
   Deep visual transformation — NOT a gentle overlay
   Dual-hue: {hue}° / {hue2}°
   ================================================================ */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,500&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── CSS Custom Properties ── */
:root {{
  --sg-hue: {hue};
  --sg-hue2: {hue2};
  --sg-accent: hsl({hue}, 72%, 55%);
  --sg-accent-dark: hsl({hue}, 72%, 40%);
  --sg-accent-light: hsl({hue}, 72%, 94%);
  --sg-accent-glow: hsl({hue}, 85%, 65%);
  --sg-accent2: hsl({hue2}, 60%, 55%);
  --sg-accent2-light: hsl({hue2}, 60%, 92%);
  --sg-ink: #0B0F19;
  --sg-ink-soft: #334155;
  --sg-ink-muted: #94a3b8;
  --sg-surface: #ffffff;
  --sg-surface-dim: #f8fafc;
  --sg-surface-glass: rgba(255,255,255,0.72);
  --sg-border: rgba(0,0,0,0.06);
  --sg-radius: 16px;
  --sg-radius-lg: 24px;
  --sg-radius-xl: 32px;
  --sg-ease: cubic-bezier(0.16, 1, 0.3, 1);
  --sg-ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
  --sg-ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
  --sg-shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
  --sg-shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 4px 8px -2px rgba(0,0,0,0.04);
  --sg-shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 12px 24px -4px rgba(0,0,0,0.05);
  --sg-shadow-lg: 0 8px 16px -4px rgba(0,0,0,0.08), 0 24px 48px -8px rgba(0,0,0,0.06);
  --sg-shadow-xl: 0 20px 40px -8px rgba(0,0,0,0.12), 0 48px 80px -16px rgba(0,0,0,0.08);
  --sg-shadow-glow: 0 8px 40px -8px hsla({hue}, 72%, 55%, 0.4);
  --sg-shadow-glow2: 0 8px 40px -8px hsla({hue2}, 60%, 55%, 0.3);
  --sg-grad-accent: linear-gradient(135deg, hsl({hue}, 72%, 55%) 0%, hsl({hue2}, 60%, 55%) 100%);
  --sg-grad-accent-vivid: linear-gradient(135deg, hsl({hue}, 85%, 60%) 0%, hsl({hue3}, 70%, 55%) 50%, hsl({hue2}, 75%, 58%) 100%);
  --sg-grad-dark: linear-gradient(180deg, #0B0F19 0%, #050710 100%);
  --sg-grad-hero: linear-gradient(135deg, hsl({hue}, 45%, 12%) 0%, hsl({hue2}, 35%, 8%) 100%);
  --sg-grad-glass: linear-gradient(135deg, rgba(255,255,255,0.85), rgba(255,255,255,0.65));
  --sg-grad-warm: linear-gradient(135deg, hsl({hue}, 45%, 97%) 0%, hsl({hue2}, 35%, 95%) 100%);
  --sg-space-xs: 0.5rem;
  --sg-space-sm: 1rem;
  --sg-space-md: 2rem;
  --sg-space-lg: 4rem;
  --sg-space-xl: 6rem;
  --sg-space-2xl: 10rem;
  --sg-transition-fast: 0.2s var(--sg-ease);
  --sg-transition-base: 0.4s var(--sg-ease);
  --sg-transition-slow: 0.7s var(--sg-ease);
}}

/* ── HIDE OFF-CANVAS / MOBILE MENUS on desktop (they leak into flow in preview) ── */
.site-mobile-menu, .mobile-menu-overlay, .offcanvas,
[class*="offcanvas-menu"], [class*="mobile-nav-wrapper"],
[class*="sidebar-menu-wrapper"], [class*="side-menu-wrapper"],
.canvas-menu, .push-menu, .slide-menu {{
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  overflow: hidden !important;
}}

/* ── Anti-aliasing & Base ── */
html, body {{
  -webkit-font-smoothing: antialiased !important;
  -moz-osx-font-smoothing: grayscale !important;
  text-rendering: optimizeLegibility !important;
  scroll-behavior: smooth;
}}

/* ── Premium Typography ── */
body {{
  font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif !important;
  line-height: 1.7 !important;
  font-size: 1rem !important;
  font-weight: 400 !important;
}}

h1, h2, h3, h4, h5, h6 {{
  font-family: 'Playfair Display', Georgia, 'Times New Roman', serif !important;
  font-weight: 700 !important;
  letter-spacing: -0.025em !important;
  line-height: 1.15 !important;
}}
h1 {{ font-size: clamp(1.8rem, 4vw, 3.2rem) !important; font-weight: 800 !important; }}
h2 {{ font-size: clamp(1.5rem, 3vw, 2.4rem) !important; }}
h3 {{ font-size: clamp(1.15rem, 2vw, 1.5rem) !important; font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 700 !important; }}
h4, h5, h6 {{ font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 600 !important; letter-spacing: -0.01em !important; }}

p {{
  line-height: 1.75 !important;
}}

/* ── NAVBAR — Preserve template identity, only enhance transitions ── */
header, .header, .main-header, .top-header, nav.navbar, .navigation,
.navbar-area, .header-area, .site-header, .nav-section {{
  transition: all 0.35s var(--sg-ease) !important;
  z-index: 1000 !important;
}}
/* Scrolled state — subtle enhancement only */
.navbar-brand, .site-title, .logo, .logo-text, .header-logo a {{
  font-family: 'Playfair Display', serif !important;
  font-weight: 700 !important;
  font-size: 1.5rem !important;
  letter-spacing: -0.02em !important;
  text-decoration: none !important;
}}
.nav-link, .navbar-nav a, .main-menu a, .nav a,
nav a, .navigation a, .menu a {{
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 500 !important;
  font-size: 0.9rem !important;
  letter-spacing: 0.01em !important;
  transition: color 0.3s ease !important;
  position: relative !important;
}}
.nav-link::after, .navbar-nav a::after, .main-menu a::after {{
  content: '' !important;
  position: absolute !important;
  bottom: -2px !important;
  left: 50% !important;
  width: 0 !important;
  height: 2px !important;
  background: var(--sg-grad-accent) !important;
  transition: all 0.3s var(--sg-ease) !important;
  transform: translateX(-50%) !important;
  border-radius: 999px !important;
}}
.nav-link:hover::after, .navbar-nav a:hover::after, .main-menu a:hover::after,
.nav-link.active::after, .navbar-nav a.active::after {{
  width: 100% !important;
}}
/* Force navbar menu visible on desktop (templates hide it for mobile by default) */
@media (min-width: 768px) {{
  .navbar-collapse, .collapse.navbar-collapse, .nav-collapse,
  nav .collapse, [class*="navbar-collapse"] {{
    display: flex !important;
    visibility: visible !important;
    height: auto !important;
    overflow: visible !important;
    flex-basis: auto !important;
  }}
  .navbar-nav, nav ul.nav, nav ul[class*="menu"],
  ul.navbar-nav, ul.nav-menu, .main-menu ul,
  header ul.nav, nav ul {{
    display: flex !important;
    visibility: visible !important;
    list-style: none !important;
    gap: 4px !important;
    align-items: center !important;
    flex-wrap: wrap !important;
  }}
  .navbar-toggler, .menu-toggle, .hamburger,
  [class*="navbar-toggler"], [class*="menu-toggle"],
  [class*="hamburger"], button[data-toggle="collapse"],
  button[data-bs-toggle="collapse"] {{
    display: none !important;
  }}
}}
/* Navbar link hover — template handles its own hover colors */

/* ── HERO — Dramatic Transformation ── */
.hero-wrap, .hero-section, section.hero, #hero,
.banner-area, .slider-area, .home-slider,
.hero-bg, .banner, .jumbotron, .hero-banner,
.main-banner, .slider-section, .page-header {{
  position: relative !important;
  overflow: hidden !important;
}}

/* Hero mesh gradient overlay — animated drift */
.hero-wrap::before, .hero-section::before, section.hero::before,
#hero::before, .banner-area::before, .slider-area::before,
.home-slider::before, .banner::before, .jumbotron::before,
.main-banner::before, .page-header::before,
[class*="blocks-cover"]::before {{
  content: '' !important;
  position: absolute !important;
  inset: -20% !important;
  background:
    radial-gradient(ellipse 60% 40% at 20% 40%, hsla({hue}, 85%, 55%, 0.35), transparent 55%),
    radial-gradient(ellipse 50% 50% at 80% 20%, hsla({hue2}, 75%, 50%, 0.30), transparent 50%),
    radial-gradient(ellipse 55% 60% at 50% 90%, hsla({hue3}, 60%, 45%, 0.20), transparent 50%),
    radial-gradient(ellipse 70% 80% at 50% 100%, rgba(0,0,0,0.50), transparent 55%) !important;
  z-index: 1 !important;
  pointer-events: none !important;
  animation: sg-mesh-drift 15s ease-in-out infinite alternate !important;
}}

/* Hero grain texture overlay */
.hero-wrap::after, .hero-section::after, section.hero::after,
#hero::after, .banner-area::after, .slider-area::after,
.home-slider::after, .banner::after, .jumbotron::after,
.main-banner::after, [class*="blocks-cover"]::after {{
  content: '' !important;
  position: absolute !important;
  inset: 0 !important;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='5' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E") !important;
  z-index: 2 !important;
  pointer-events: none !important;
  mix-blend-mode: overlay !important;
  opacity: 0.7 !important;
}}

/* Hero — prevent templates' own min-height from creating excessive whitespace */
.hero-wrap, .hero-section, section.hero, #hero,
.banner-area, .slider-area, .home-slider,
.site-blocks-cover, [class*="hero-wrap"], [class*="hero-section"],
[class*="hero-bg"], [class*="hero_area"], [class*="slider-section"],
[class*="main-banner"], [class*="page-header"],
[class*="blocks-cover"] {{
  min-height: auto !important;
}}
/* Hero height — let template decide its own hero dimensions */
.hero-wrap .row, .hero-section .row, section.hero .row, #hero .row,
.banner-area .row, .slider-area .row, .home-slider .row,
.site-blocks-cover .row, [class*="hero"] .row, [class*="banner"] .row {{
  min-height: auto !important;
}}

/* Hero content sits above overlays */
.hero-wrap > *, .hero-section > *, section.hero > *, #hero > *,
.banner-area > *, .slider-area > *, .home-slider > *,
.banner > *, .jumbotron > *, .main-banner > * {{
  position: relative !important;
  z-index: 3 !important;
}}

/* Hero title — dramatic, with gradient text option */
.hero-wrap h1, .hero-section h1, section.hero h1, #hero h1,
.banner-area h1, .banner h1, .jumbotron h1, .hero-banner h1,
.main-banner h1, .slider-area h1, .home-slider h1 {{
  font-size: clamp(2.2rem, 5vw, 4rem) !important;
  font-weight: 800 !important;
  line-height: 1.08 !important;
  letter-spacing: -0.03em !important;
  margin-bottom: 1.2rem !important;
  overflow-wrap: break-word !important;
  word-wrap: break-word !important;
  text-shadow: 0 2px 40px rgba(0,0,0,0.10) !important;
}}
/* Gradient text on hero h1 when on light/white backgrounds */
.hero-wrap h1 span, .hero-section h1 span,
section.hero h1 span, #hero h1 span {{
  background: var(--sg-grad-accent) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}}
/* Hero badge / overline text */
.hero-wrap .subtitle, .hero-section .subtitle,
.hero-wrap .overline, .hero-section .overline,
.hero-wrap .hero-subtitle, .hero-section small {{
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.8rem !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  color: var(--sg-accent) !important;
  margin-bottom: 0.75rem !important;
  display: inline-block !important;
}}

/* Hero subtitle */
.hero-wrap p, .hero-section p, section.hero p, #hero p,
.banner-area p, .banner p, .jumbotron p {{
  font-size: clamp(0.95rem, 1.3vw, 1.15rem) !important;
  line-height: 1.7 !important;
  max-width: 580px !important;
}}

/* Hero layout flip for some templates */
{('''
.hero-wrap .container .row, .hero-section .container .row,
section.hero .container .row, #hero .container .row {{
  flex-direction: row-reverse !important;
}}
''' if flip_hero else '')}

/* ── BUTTONS — Premium Pill with Gradient ── */
.btn, button:not([class*="close"]):not([class*="toggle"]):not([class*="navbar"]):not([class*="carousel"]):not([class*="slick"]):not([class*="owl"]),
.button, input[type="submit"], input[type="button"],
a.btn, .cta-btn, .theme-btn, .main-btn, .btn-theme {{
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  border-radius: 999px !important;
  font-weight: 600 !important;
  padding: 14px 34px !important;
  font-size: 0.9rem !important;
  letter-spacing: 0.01em !important;
  transition: all 0.4s var(--sg-ease) !important;
  border: 2px solid transparent !important;
  position: relative !important;
  overflow: hidden !important;
  cursor: pointer !important;
  text-transform: none !important;
}}

.btn-primary, .btn-default, .btn-main, .main-btn,
.theme-btn, .btn-theme, .bt-btn, .cta-btn,
.btn-accent, .btn-colored, .btn-submit {{
  background: var(--sg-grad-accent) !important;
  color: #fff !important;
  border-color: transparent !important;
  box-shadow: var(--sg-shadow-sm), 0 4px 16px -4px hsla({hue}, 72%, 55%, 0.35) !important;
}}
/* Shine sweep on primary buttons */
.btn-primary::after, .btn-default::after, .btn-main::after, .main-btn::after,
.theme-btn::after, .btn-theme::after, .bt-btn::after, .cta-btn::after {{
  content: '' !important;
  position: absolute !important;
  top: 0 !important; left: -100% !important;
  width: 60% !important; height: 100% !important;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.30), transparent) !important;
  transition: none !important;
  transform: skewX(-20deg) !important;
  pointer-events: none !important;
}}
.btn-primary:hover::after, .btn-default:hover::after, .btn-main:hover::after, .main-btn:hover::after,
.theme-btn:hover::after, .btn-theme:hover::after, .bt-btn:hover::after, .cta-btn:hover::after {{
  animation: sg-btn-shine 0.6s ease forwards !important;
}}
.btn-primary:hover, .btn-default:hover, .btn-main:hover, .main-btn:hover,
.theme-btn:hover, .btn-theme:hover, .bt-btn:hover, .cta-btn:hover {{
  transform: translateY(-3px) scale(1.03) !important;
  box-shadow: var(--sg-shadow-xl), 0 16px 40px -8px hsla({hue}, 72%, 55%, 0.50) !important;
  filter: brightness(1.10) !important;
}}
.btn-primary:active, .btn-default:active, .btn-main:active {{
  transform: translateY(-1px) scale(0.98) !important;
  box-shadow: var(--sg-shadow-sm) !important;
}}

/* Secondary/outline buttons */
.btn-secondary, .btn-outline, .btn-outline-primary, .btn-border, .btn-ghost {{
  background: transparent !important;
  border: 2px solid var(--sg-accent) !important;
  color: var(--sg-accent) !important;
}}
.btn-secondary:hover, .btn-outline:hover, .btn-outline-primary:hover {{
  background: var(--sg-accent) !important;
  color: #fff !important;
  transform: translateY(-2px) !important;
  box-shadow: var(--sg-shadow-glow) !important;
}}

/* ── CARDS — Ultra-premium 3D hover with depth ── */
.card, .service-box, .team-member, .project-item, .blog-post,
.services-item, .feature-box, .pricing-box, .testimonial,
.single-service, .single-feature, .work-item, .portfolio-item,
.blog-card, .news-item, .event-item, .course-card {{
  border-radius: var(--sg-radius-lg) !important;
  box-shadow: var(--sg-shadow-md) !important;
  transition: all 0.5s var(--sg-ease) !important;
  overflow: hidden !important;
  position: relative !important;
  border: 1px solid rgba(0,0,0,0.04) !important;
  background: rgba(255,255,255,0.95) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}}
.card:hover, .service-box:hover, .team-member:hover, .project-item:hover,
.blog-post:hover, .services-item:hover, .feature-box:hover,
.pricing-box:hover, .single-service:hover, .single-feature:hover,
.work-item:hover, .portfolio-item:hover, .blog-card:hover {{
  transform: translateY(-8px) scale(1.01) !important;
  box-shadow: var(--sg-shadow-xl), 0 0 0 1px rgba(0,0,0,0.02) !important;
}}
/* Card top accent line */
.card::after, .service-box::after, .feature-box::after,
.single-service::after, .single-feature::after {{
  content: '' !important;
  position: absolute !important;
  top: 0 !important; left: 0 !important; right: 0 !important;
  height: 3px !important;
  background: var(--sg-grad-accent) !important;
  opacity: 0 !important;
  transition: opacity 0.4s ease !important;
}}
.card:hover::after, .service-box:hover::after, .feature-box:hover::after,
.single-service:hover::after, .single-feature:hover::after {{
  opacity: 1 !important;
}}

/* Card images */
.card img, .service-box img, .team-member img, .project img, .post-img img,
.blog-post img, .about img, .portfolio img, .gallery img,
.blog-card img, .course-card img {{
  border-radius: var(--sg-radius) !important;
  transition: transform 0.7s var(--sg-ease) !important;
  object-fit: cover !important;
}}
.card:hover img, .service-box:hover img, .team-member:hover img,
.project:hover img, .portfolio:hover img, .blog-card:hover img {{
  transform: scale(1.03) !important;
}}

/* ── ICON BOXES ── */
.icon-box, .feature-icon, .service-icon,
[class*="icon-wrap"], [class*="icon-box"],
.flaticon, .lnr, .feature .icon {{
  transition: all 0.4s var(--sg-ease) !important;
}}
.service-box .icon-box, .feature-box .icon,
.single-service .icon, .single-feature .icon {{
  background: var(--sg-accent-light) !important;
  color: var(--sg-accent) !important;
  border-radius: var(--sg-radius) !important;
  transition: all 0.4s var(--sg-ease) !important;
}}
.service-box:hover .icon-box, .feature-box:hover .icon,
.single-service:hover .icon, .single-feature:hover .icon {{
  background: var(--sg-accent) !important;
  color: #fff !important;
  transform: scale(1.1) rotate(5deg) !important;
  box-shadow: var(--sg-shadow-glow) !important;
}}

/* ── FORM INPUTS — Elegant ── */
input[type="text"], input[type="email"], input[type="tel"], input[type="url"],
input[type="password"], input[type="search"], input[type="number"],
input[type="date"], textarea, select, .form-control {{
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  border-radius: 14px !important;
  border: 1.5px solid rgba(0,0,0,0.08) !important;
  padding: 15px 20px !important;
  font-size: 0.95rem !important;
  transition: all 0.3s var(--sg-ease) !important;
  background: rgba(255,255,255,0.9) !important;
}}
input:focus, textarea:focus, select:focus, .form-control:focus {{
  outline: none !important;
  border-color: var(--sg-accent) !important;
  box-shadow: 0 0 0 4px hsla({hue}, 72%, 55%, 0.1), var(--sg-shadow-sm) !important;
  background: #fff !important;
}}

/* ── SECTION SPACING — gentle, not forced ── */
section, .section {{
  position: relative !important;
}}

/* Section headings — only style font, not color (preserve template contrast) */
.section-title h2, .section-heading h2 {{
  margin-bottom: 1rem !important;
}}

/* ── COUNTER / STATS SECTIONS ── */
.counter-area, .counts, .funfact-area, .fun-factor,
.counter_section, .counter-section, .fun-facts {{
  background: var(--sg-grad-hero) !important;
  color: #fff !important;
  position: relative !important;
}}
.counter-area::before, .counts::before, .funfact-area::before {{
  content: '' !important;
  position: absolute !important;
  inset: 0 !important;
  background:
    radial-gradient(ellipse at 30% 50%, hsla({hue}, 80%, 55%, 0.2), transparent 50%),
    radial-gradient(ellipse at 70% 50%, hsla({hue2}, 70%, 50%, 0.15), transparent 50%) !important;
  pointer-events: none !important;
}}
.counter-area *, .counts *, .funfact-area *, .fun-factor *,
.counter_section *, .counter-section * {{
  color: #fff !important;
}}

/* ── FOOTER — Ultra Premium Dark ── */
footer, .footer, .footer-area, .main-footer, .footer-section {{
  background: var(--sg-grad-dark) !important;
  color: rgba(255,255,255,0.7) !important;
  position: relative !important;
  padding-top: 80px !important;
  overflow: hidden !important;
}}
footer::before, .footer::before, .footer-area::before {{
  content: '' !important;
  position: absolute !important;
  top: 0 !important; left: 0 !important; right: 0 !important;
  height: 2px !important;
  background: linear-gradient(90deg, transparent 2%, hsla({hue}, 72%, 55%, 0.7), hsla({hue2}, 60%, 55%, 0.7), transparent 98%) !important;
  z-index: 1 !important;
}}
/* Footer decorative mesh */
footer::after, .footer::after, .footer-area::after {{
  content: '' !important;
  position: absolute !important;
  inset: 0 !important;
  background:
    radial-gradient(ellipse 50% 30% at 10% 90%, hsla({hue}, 70%, 40%, 0.08), transparent),
    radial-gradient(ellipse 40% 40% at 90% 80%, hsla({hue2}, 60%, 40%, 0.06), transparent) !important;
  pointer-events: none !important;
}}
footer h1, footer h2, footer h3, footer h4, footer h5, footer h6,
.footer h1, .footer h2, .footer h3, .footer h4, .footer h5, .footer h6 {{
  color: #fff !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 700 !important;
}}
footer a, .footer a {{
  color: rgba(255,255,255,0.6) !important;
  transition: color 0.3s ease !important;
}}
footer a:hover, .footer a:hover {{
  color: var(--sg-accent-glow) !important;
}}
footer p, .footer p {{
  color: rgba(255,255,255,0.55) !important;
}}

/* ── PRICING CARDS ── */
.pricing-table, .pricing-box, .price-card, .pricing-card,
.pricing-item, .single-pricing, .price-table {{
  background: #fff !important;
  border: 1.5px solid rgba(0,0,0,0.04) !important;
  border-radius: var(--sg-radius-xl) !important;
  overflow: hidden !important;
  transition: all 0.5s var(--sg-ease) !important;
  position: relative !important;
}}
.pricing-table.active, .pricing-box.active, .pricing-box.featured,
.price-card.popular, .pricing-card.active, .pricing-item.active,
.pricing-item.featured, .single-pricing.active {{
  border-color: var(--sg-accent) !important;
  box-shadow: 0 24px 64px -16px hsla({hue}, 72%, 50%, 0.35),
              0 0 0 1.5px var(--sg-accent),
              0 0 80px -20px hsla({hue}, 80%, 55%, 0.2) !important;
  transform: scale(1.06) translateY(-12px) !important;
}}
/* Pricing price number — gradient */
.pricing-table .price, .pricing-box .price, .pricing-card .price,
.pricing-item .price, .single-pricing .price,
.pricing-table h3, .pricing-box h3 {{
  background: var(--sg-grad-accent) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  font-weight: 800 !important;
}}
.pricing-table.active::before, .pricing-box.active::before,
.pricing-box.featured::before, .pricing-card.active::before {{
  content: '' !important;
  position: absolute !important;
  top: 0 !important; left: 0 !important; right: 0 !important;
  height: 4px !important;
  background: var(--sg-grad-accent) !important;
}}

/* ── TESTIMONIALS — Luxurious ── */
.testimonial, .testimonial-item, .testi-card, .review-card,
.testimonial-box, .testimony-wrap, .single-testimonial {{
  background: #fff !important;
  border: 1px solid rgba(0,0,0,0.03) !important;
  border-radius: var(--sg-radius-xl) !important;
  padding: 40px 36px !important;
  box-shadow: var(--sg-shadow-lg) !important;
  position: relative !important;
  overflow: visible !important;
  transition: all 0.5s var(--sg-ease) !important;
}}
.testimonial:hover, .testimonial-item:hover, .testi-card:hover {{
  transform: translateY(-4px) !important;
  box-shadow: var(--sg-shadow-xl) !important;
}}
.testimonial::before, .testimonial-item::before,
.testi-card::before, .single-testimonial::before {{
  content: '\\201C' !important;
  position: absolute !important;
  top: -10px !important;
  left: 32px !important;
  font-size: 6rem !important;
  font-family: 'Playfair Display', serif !important;
  background: var(--sg-grad-accent) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  line-height: 1 !important;
  pointer-events: none !important;
  opacity: 0.6 !important;
}}
/* Testimonial avatar ring */
.testimonial img, .testimonial-item img, .testi-card img,
.single-testimonial img, .review-card img {{
  border: 3px solid transparent !important;
  background-image: linear-gradient(#fff, #fff), var(--sg-grad-accent) !important;
  background-origin: border-box !important;
  background-clip: padding-box, border-box !important;
  border-radius: 50% !important;
}}

/* ── LINKS ── */
a:not(.btn):not(.button):not(.nav-link):not([class*="social"]):not([class*="navbar"]):not([class*="menu"]) {{
  color: var(--sg-accent) !important;
  text-decoration: none !important;
  transition: color 0.3s ease !important;
}}
a:not(.btn):not(.button):not(.nav-link):not([class*="social"]):not([class*="navbar"]):not([class*="menu"]):hover {{
  color: var(--sg-accent-dark) !important;
}}

/* ── BADGES / TAGS ── */
.badge, .tag, .label:not(label), .category-tag {{
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  border-radius: 999px !important;
  font-weight: 600 !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.05em !important;
  text-transform: uppercase !important;
  padding: 4px 12px !important;
}}

/* ── IMAGES — Unified Premium ── */
img {{
  transition: opacity 0.5s ease !important;
}}
.about img, .about-section img, #about img,
.team img, .team-section img {{
  border-radius: var(--sg-radius-lg) !important;
  box-shadow: var(--sg-shadow-lg) !important;
}}

/* ── DIVIDERS & SEPARATORS ── */
hr {{
  border: none !important;
  height: 1px !important;
  background: linear-gradient(90deg, transparent, var(--sg-border), transparent) !important;
  margin: 2rem 0 !important;
}}

/* ── SELECTION ── */
::selection {{
  background: hsla({hue}, 72%, 55%, 0.15);
  color: inherit;
}}

/* ── PREMIUM SCROLLBAR ── */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: var(--sg-surface-dim); }}
::-webkit-scrollbar-thumb {{
  background: linear-gradient(180deg, var(--sg-accent), var(--sg-accent2));
  border-radius: 999px;
}}

/* ── ACCENT STRIP SIGNATURE — top of page ── */
body::before {{
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--sg-accent), var(--sg-accent2), var(--sg-accent));
  background-size: 200% 100%;
  animation: sg-strip-shift 8s ease infinite;
  z-index: 2147482000;
  pointer-events: none;
}}
@keyframes sg-strip-shift {{
  0%, 100% {{ background-position: 0% 50%; }}
  50% {{ background-position: 100% 50%; }}
}}

/* ── SCROLL REVEAL ANIMATIONS ── */
@keyframes sg-fade-up {{
  from {{ opacity: 0; transform: translateY(40px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes sg-fade-in {{
  from {{ opacity: 0; }}
  to {{ opacity: 1; }}
}}
@keyframes sg-scale-in {{
  from {{ opacity: 0; transform: scale(0.92); }}
  to {{ opacity: 1; transform: scale(1); }}
}}
@keyframes sg-slide-left {{
  from {{ opacity: 0; transform: translateX(-40px); }}
  to {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes sg-slide-right {{
  from {{ opacity: 0; transform: translateX(40px); }}
  to {{ opacity: 1; transform: translateX(0); }}
}}

.sg-reveal {{
  animation: sg-fade-up 0.8s var(--sg-ease) both;
}}
.sg-reveal-delay-1 {{ animation-delay: 0.1s; }}
.sg-reveal-delay-2 {{ animation-delay: 0.2s; }}
.sg-reveal-delay-3 {{ animation-delay: 0.3s; }}
.sg-reveal-delay-4 {{ animation-delay: 0.4s; }}

/* ── BACKGROUND PATTERNS ── */
.sg-pattern-dots {{
  background-image: radial-gradient(circle, rgba(0,0,0,0.04) 1px, transparent 1px) !important;
  background-size: 24px 24px !important;
}}

/* ── FORCE ACCENT COLORS onto template's own colored elements ── */
.bg-primary, [class*="bg-primary"], [class*="bg-theme"],
[class*="bg-color"], [class*="bg-main"], [class*="theme-bg"],
[class*="bg-accent"] {{
  background: var(--sg-grad-accent) !important;
  color: #fff !important;
}}
.text-primary, [class*="text-primary"], [class*="text-theme"],
[class*="theme-color"], [class*="text-accent"] {{
  color: var(--sg-accent) !important;
}}
.border-primary, [class*="border-primary"], [class*="border-theme"] {{
  border-color: var(--sg-accent) !important;
}}

/* ── Heading font styling (no forced colors — preserve template contrast) ── */
section h2, .section h2, .container h2 {{
  font-family: 'Playfair Display', Georgia, serif !important;
  font-weight: 700 !important;
  font-size: clamp(1.4rem, 2.8vw, 2.2rem) !important;
  letter-spacing: -0.02em !important;
  margin-bottom: 1rem !important;
}}
section p, .section p {{
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  line-height: 1.75 !important;
}}

/* ── CTA SECTIONS — dramatic gradient ── */
.cta-area, .call-to-action, .cta-section, .cta,
[class*="cta-wrap"], [class*="call-action"] {{
  background: var(--sg-grad-hero) !important;
  color: #fff !important;
  position: relative !important;
  overflow: hidden !important;
}}
.cta-area *, .call-to-action *, .cta-section * {{
  color: #fff !important;
}}
.cta-area::before, .call-to-action::before, .cta-section::before {{
  content: '' !important;
  position: absolute !important;
  inset: 0 !important;
  background:
    radial-gradient(ellipse at 20% 50%, hsla({hue}, 80%, 55%, 0.25), transparent 50%),
    radial-gradient(ellipse at 80% 50%, hsla({hue2}, 70%, 50%, 0.2), transparent 50%) !important;
  pointer-events: none !important;
}}

/* ── ANIMATED GRADIENT BORDERS on featured cards ── */
.card.featured, .pricing-box.active, .pricing-table.active,
.pricing-card.active, .pricing-item.featured {{
  position: relative !important;
  background: #fff !important;
  z-index: 1 !important;
}}
.card.featured::before, .pricing-box.active::before,
.pricing-table.active::before {{
  content: '' !important;
  position: absolute !important;
  inset: -2px !important;
  background: var(--sg-grad-accent-vivid) !important;
  border-radius: inherit !important;
  z-index: -1 !important;
  background-size: 200% 200% !important;
  animation: sg-gradient-rotate 4s ease infinite !important;
}}
@keyframes sg-gradient-rotate {{
  0%, 100% {{ background-position: 0% 50%; }}
  50% {{ background-position: 100% 50%; }}
}}

/* ── CONTACT / FORM SECTIONS ── */
.contact-area, .contact-section, #contact, .contact-form,
[class*="contact-wrap"] {{
  background: var(--sg-surface-dim) !important;
}}
.contact-area h2, .contact-section h2, #contact h2 {{
  /* color inherited from template — no forced override */
}}

/* ── PROCESS / STEPS SECTIONS ── */
.process-area, .how-it-works, .steps-section,
[class*="process-wrap"], [class*="step-area"] {{
  background: #fff !important;
}}

/* ── TEAM MEMBERS — subtle refinement ── */
.team-member img, .team-card img, .single-team img, .team-item img {{
  object-fit: cover !important;
  transition: transform 0.5s var(--sg-ease) !important;
}}

/* ── PROGRESS BARS — accent colored ── */
.progress-bar, [class*="progress-bar"], .skill-bar {{
  background: var(--sg-grad-accent) !important;
  border-radius: 999px !important;
}}

/* ── TABS & PILLS — accent active state ── */
.nav-tabs .nav-link.active, .nav-pills .nav-link.active,
.tab-btn.active, [class*="tab-btn"].active {{
  background: var(--sg-accent) !important;
  color: #fff !important;
  border-color: var(--sg-accent) !important;
  border-radius: 999px !important;
}}

/* ── LIST ICONS — accent colored ── */
ul.list-check li::before, ul[class*="check"] li::before,
.feature-list li::before {{
  color: var(--sg-accent) !important;
}}

/* ── IMAGE OVERLAYS on hover for portfolio/gallery ── */
.portfolio-item, .project-item, .gallery-item, .work-item {{
  position: relative !important;
  overflow: hidden !important;
  border-radius: var(--sg-radius-lg) !important;
}}
.portfolio-item::after, .project-item::after, .gallery-item::after, .work-item::after {{
  content: '' !important;
  position: absolute !important;
  inset: 0 !important;
  background: linear-gradient(180deg, transparent 20%,
    hsla({hue}, 72%, 15%, 0.4) 60%,
    hsla({hue}, 72%, 10%, 0.85) 100%) !important;
  opacity: 0 !important;
  transition: opacity 0.5s var(--sg-ease) !important;
  pointer-events: none !important;
  border-radius: inherit !important;
}}
.portfolio-item:hover::after, .project-item:hover::after,
.gallery-item:hover::after, .work-item:hover::after {{
  opacity: 1 !important;
}}
/* Portfolio image zoom on hover */
.portfolio-item img, .project-item img, .gallery-item img, .work-item img {{
  transition: transform 0.8s var(--sg-ease) !important;
}}
.portfolio-item:hover img, .project-item:hover img,
.gallery-item:hover img, .work-item:hover img {{
  transform: scale(1.08) !important;
}}

/* ── SOCIAL ICONS — accent hover ── */
.social-links a, [class*="social"] a, .social a {{
  transition: all 0.3s ease !important;
}}
.social-links a:hover, [class*="social"] a:hover, .social a:hover {{
  color: var(--sg-accent) !important;
  transform: translateY(-3px) !important;
}}

/* ── ACCORDION / FAQ — elegant with proper spacing ── */
.accordion-button, .faq-title, [class*="accordion"] .card-header,
.accordion-item > a, [class*="accordion"] > a {{
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 600 !important;
  border-radius: var(--sg-radius) !important;
  padding: 16px 20px !important;
  display: block !important;
}}
.accordion-item, [class*="accordion"] .card,
.accordion > .card, .accordion > div {{
  margin-bottom: 8px !important;
  border-radius: var(--sg-radius) !important;
  overflow: hidden !important;
}}
.accordion-button:not(.collapsed), .faq-title.active {{
  background: var(--sg-accent-light) !important;
  color: var(--sg-accent-dark) !important;
}}

/* ── BREADCRUMBS — subtle ── */
.breadcrumb, .breadcrumb-area, [class*="breadcrumb"] {{
  background: var(--sg-surface-dim) !important;
}}

/* ── PREFERS-REDUCED-MOTION ── */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }}
}}

/* ── FOCUS ACCESSIBILITY ── */
:focus-visible {{
  outline: 2px solid var(--sg-accent) !important;
  outline-offset: 3px !important;
  border-radius: 4px !important;
}}

/* ── IMAGES — ensure proper fit and proportions ── */
img[src*="unsplash.com"] {{
  object-fit: cover !important;
}}

/* Large content images (hero, about, blog) — fill width, cap height */
section img[src*="unsplash"]:not([class*="rounded-circle"]),
.hero img[src*="unsplash"], .banner img[src*="unsplash"],
.about img[src*="unsplash"], .blog img[src*="unsplash"] {{
  width: 100% !important;
  height: auto !important;
  max-height: 450px !important;
  object-fit: cover !important;
  border-radius: var(--sg-radius-lg) !important;
}}

/* Card/blog images — uniform aspect ratio */
.card img[src*="unsplash"], .blog-post img[src*="unsplash"],
.blog-entry img[src*="unsplash"], .d-lg-flex img[src*="unsplash"],
.portfolio-item img[src*="unsplash"], .project-item img[src*="unsplash"],
.work-item img[src*="unsplash"], .gallery-item img[src*="unsplash"] {{
  aspect-ratio: 16/10 !important;
  width: 100% !important;
  max-height: 260px !important;
}}

/* Small circular/avatar images (services, team, testimonials) — uniform size */
.owl-carousel img[src*="unsplash"],
[class*="testimony"] img[src*="unsplash"],
[class*="testimonial"] img[src*="unsplash"],
[class*="block-testimony"] img[src*="unsplash"] {{
  width: 80px !important;
  height: 80px !important;
  border-radius: 50% !important;
  object-fit: cover !important;
}}

/* Ensure all images in the same row/grid are same height */
.row img[src*="unsplash"] {{
  object-fit: cover !important;
}}

/* ================================================================
   ULTRA-PREMIUM ADDITIONS — Dramatic Visual Transformation
   ================================================================ */

/* ── ANIMATED MESH GRADIENT KEYFRAMES ── */
@keyframes sg-mesh-drift {{
  0% {{ transform: translate(0, 0) scale(1); }}
  25% {{ transform: translate(5%, -3%) scale(1.05); }}
  50% {{ transform: translate(-3%, 5%) scale(1.02); }}
  75% {{ transform: translate(3%, 2%) scale(1.06); }}
  100% {{ transform: translate(-5%, -2%) scale(1.03); }}
}}

/* ── BUTTON SHINE KEYFRAME ── */
@keyframes sg-btn-shine {{
  0% {{ left: -100%; }}
  100% {{ left: 120%; }}
}}

/* ── GRADIENT TEXT — Section headings get gradient accent ── */
.section-title h2::after, .section-heading h2::after,
section > .container > h2::first-line {{
  /* Gradient underline on section headings */
}}
.section-title h2, .section-heading h2 {{
  position: relative !important;
  display: inline-block !important;
}}
.section-title h2::after, .section-heading h2::after {{
  content: '' !important;
  position: absolute !important;
  bottom: -8px !important;
  left: 0 !important;
  width: 60px !important;
  height: 4px !important;
  background: var(--sg-grad-accent) !important;
  border-radius: 999px !important;
}}

/* ── FLOATING DECORATIVE SHAPES ── */
.hero-wrap .container, .hero-section .container,
section.hero .container, #hero .container {{
  position: relative !important;
}}
/* Decorative circle blob — top-right of hero */
body > .hero-wrap, body > .hero-section, body > section.hero,
body > header + .hero-wrap, body > header + .hero-section,
body > header + section.hero, body > nav + .hero-wrap,
body > nav + .hero-section {{
  --sg-blob-size: clamp(200px, 30vw, 450px);
}}

/* ── WAVE SECTION DIVIDER ── */
section + section, .section + .section {{
  position: relative !important;
}}

/* ── GLASSMORPHISM UTILITY LAYER ── */
.sg-glass {{
  background: rgba(255,255,255,0.65) !important;
  backdrop-filter: saturate(180%) blur(20px) !important;
  -webkit-backdrop-filter: saturate(180%) blur(20px) !important;
  border: 1px solid rgba(255,255,255,0.3) !important;
}}

/* ── BACK TO TOP BUTTON ── */
.sg-back-to-top {{
  position: fixed !important;
  bottom: 32px !important;
  right: 32px !important;
  width: 48px !important;
  height: 48px !important;
  border-radius: 50% !important;
  background: var(--sg-grad-accent) !important;
  color: #fff !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 1.2rem !important;
  box-shadow: var(--sg-shadow-lg), var(--sg-shadow-glow) !important;
  cursor: pointer !important;
  z-index: 2147481000 !important;
  opacity: 0 !important;
  transform: translateY(20px) !important;
  transition: all 0.4s var(--sg-ease) !important;
  border: none !important;
}}
.sg-back-to-top.visible {{
  opacity: 1 !important;
  transform: translateY(0) !important;
}}
.sg-back-to-top:hover {{
  transform: translateY(-4px) scale(1.1) !important;
  box-shadow: var(--sg-shadow-xl), 0 12px 40px -8px hsla({hue}, 72%, 55%, 0.5) !important;
}}
.sg-back-to-top svg {{
  width: 20px !important;
  height: 20px !important;
  fill: none !important;
  stroke: #fff !important;
  stroke-width: 2.5 !important;
  stroke-linecap: round !important;
  stroke-linejoin: round !important;
}}

/* ── SCROLL PROGRESS INDICATOR ── */
.sg-scroll-progress {{
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  height: 3px !important;
  background: var(--sg-grad-accent) !important;
  z-index: 2147483000 !important;
  transition: width 0.1s linear !important;
  pointer-events: none !important;
  box-shadow: 0 0 10px hsla({hue}, 72%, 55%, 0.5) !important;
}}

/* ── STAGGERED REVEAL ANIMATION (for card grids) ── */
.sg-stagger {{ opacity: 0; transform: translateY(30px); }}
.sg-stagger.sg-visible {{
  animation: sg-fade-up 0.7s var(--sg-ease) both !important;
}}
.sg-stagger.sg-visible:nth-child(1) {{ animation-delay: 0s !important; }}
.sg-stagger.sg-visible:nth-child(2) {{ animation-delay: 0.08s !important; }}
.sg-stagger.sg-visible:nth-child(3) {{ animation-delay: 0.16s !important; }}
.sg-stagger.sg-visible:nth-child(4) {{ animation-delay: 0.24s !important; }}
.sg-stagger.sg-visible:nth-child(5) {{ animation-delay: 0.32s !important; }}
.sg-stagger.sg-visible:nth-child(6) {{ animation-delay: 0.40s !important; }}
.sg-stagger.sg-visible:nth-child(7) {{ animation-delay: 0.48s !important; }}
.sg-stagger.sg-visible:nth-child(8) {{ animation-delay: 0.56s !important; }}

/* ── COUNTER / STAT NUMBERS — Large gradient ── */
.counter-area h2, .counter-area .counter, .counter-area .number,
.counts .counter, .funfact-area .counter, .fun-factor .number,
.counter_section .counter, [class*="counter"] span.count,
[class*="funfact"] .number, [class*="counter"] .number {{
  font-family: 'Playfair Display', serif !important;
  font-size: clamp(2.5rem, 4vw, 3.5rem) !important;
  font-weight: 800 !important;
  letter-spacing: -0.02em !important;
}}

/* ── NEWSLETTER / SUBSCRIBE — Premium inline form ── */
.newsletter, .subscribe-form, [class*="newsletter"], [class*="subscribe"] {{
  position: relative !important;
}}
.newsletter input[type="email"], .subscribe-form input[type="email"],
[class*="newsletter"] input[type="email"] {{
  border-radius: 999px !important;
  padding: 16px 160px 16px 24px !important;
  border: 2px solid rgba(255,255,255,0.15) !important;
  background: rgba(255,255,255,0.08) !important;
  color: #fff !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}}
.newsletter input[type="email"]:focus, .subscribe-form input[type="email"]:focus {{
  border-color: var(--sg-accent) !important;
  background: rgba(255,255,255,0.12) !important;
  box-shadow: 0 0 0 4px hsla({hue}, 72%, 55%, 0.15) !important;
}}
.newsletter .btn, .subscribe-form .btn, [class*="newsletter"] .btn {{
  position: absolute !important;
  right: 6px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  border-radius: 999px !important;
  padding: 12px 28px !important;
}}

/* ── SOCIAL ICONS — Gradient hover circles ── */
.social-links a, [class*="social"] a, .social a,
footer .social a, .footer .social a {{
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 40px !important;
  height: 40px !important;
  border-radius: 50% !important;
  background: rgba(255,255,255,0.08) !important;
  transition: all 0.4s var(--sg-ease) !important;
  margin: 0 4px !important;
}}
.social-links a:hover, [class*="social"] a:hover, .social a:hover,
footer .social a:hover, .footer .social a:hover {{
  background: var(--sg-grad-accent) !important;
  color: #fff !important;
  transform: translateY(-4px) scale(1.1) !important;
  box-shadow: 0 8px 24px -4px hsla({hue}, 72%, 55%, 0.4) !important;
}}

/* ── LOADING SHIMMER (for images before load) ── */
@keyframes sg-shimmer {{
  0% {{ background-position: -200% 0; }}
  100% {{ background-position: 200% 0; }}
}}
img[data-sg-loading] {{
  background: linear-gradient(90deg,
    var(--sg-surface-dim) 25%,
    rgba(0,0,0,0.04) 37%,
    var(--sg-surface-dim) 63%) !important;
  background-size: 200% 100% !important;
  animation: sg-shimmer 1.5s ease infinite !important;
}}

/* ── SEPARATOR WITH ICON ── */
.sg-separator {{
  display: flex !important;
  align-items: center !important;
  gap: 16px !important;
  margin: 3rem 0 !important;
}}
.sg-separator::before, .sg-separator::after {{
  content: '' !important;
  flex: 1 !important;
  height: 1px !important;
  background: linear-gradient(90deg, transparent, var(--sg-border), transparent) !important;
}}

/* ── DARK SECTIONS — alternate styling ── */
.bg-dark, [class*="dark-bg"], [class*="bg-dark"],
.dark-section, [class*="bg-black"] {{
  background: var(--sg-grad-dark) !important;
  color: rgba(255,255,255,0.85) !important;
  position: relative !important;
}}
.bg-dark h1, .bg-dark h2, .bg-dark h3, .bg-dark h4,
[class*="dark-bg"] h1, [class*="dark-bg"] h2, [class*="dark-bg"] h3 {{
  color: #fff !important;
}}
.bg-dark p, [class*="dark-bg"] p {{
  color: rgba(255,255,255,0.7) !important;
}}

/* ── ABOUT SECTION — Premium layout ── */
.about-section, .about-area, #about, [class*="about-wrap"] {{
  position: relative !important;
}}
.about-section img, .about-area img, #about img {{
  border-radius: var(--sg-radius-xl) !important;
  box-shadow: var(--sg-shadow-xl) !important;
  position: relative !important;
}}

/* ── IMAGE FRAMES — Decorative border on about/team images ── */
.about img, .about-section img, #about img {{
  border: 4px solid transparent !important;
  background-image: linear-gradient(#fff, #fff), var(--sg-grad-accent) !important;
  background-origin: border-box !important;
  background-clip: padding-box, border-box !important;
}}

/* ── LISTS — Premium styled ── */
ul:not(.navbar-nav):not(.nav):not(.menu):not(.social-links):not([class*="slick"]):not([class*="owl"]) li {{
  line-height: 1.8 !important;
}}

/* ── BLOCKQUOTES — Elegant ── */
blockquote {{
  border-left: 4px solid var(--sg-accent) !important;
  padding: 20px 28px !important;
  background: var(--sg-accent-light) !important;
  border-radius: 0 var(--sg-radius) var(--sg-radius) 0 !important;
  font-style: italic !important;
  font-family: 'Playfair Display', serif !important;
  font-size: 1.1rem !important;
  position: relative !important;
  margin: 2rem 0 !important;
}}

/* ── TABLE — Premium styling ── */
table {{
  border-radius: var(--sg-radius) !important;
  overflow: hidden !important;
  box-shadow: var(--sg-shadow-sm) !important;
}}
table thead, table thead tr {{
  background: var(--sg-grad-accent) !important;
  color: #fff !important;
}}
table thead th {{
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 600 !important;
  padding: 14px 16px !important;
  color: #fff !important;
}}
table tbody tr {{
  transition: background 0.2s ease !important;
}}
table tbody tr:hover {{
  background: var(--sg-accent-light) !important;
}}
table td {{
  padding: 12px 16px !important;
}}

/* ── MODALS — Glassmorphism backdrop ── */
.modal-backdrop {{
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
  background: rgba(11, 15, 25, 0.6) !important;
}}
.modal-content {{
  border-radius: var(--sg-radius-xl) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  box-shadow: var(--sg-shadow-xl) !important;
  overflow: hidden !important;
}}

/* ── DROPDOWN MENUS — Elegant animation ── */
.dropdown-menu {{
  border-radius: var(--sg-radius) !important;
  border: 1px solid rgba(0,0,0,0.04) !important;
  box-shadow: var(--sg-shadow-xl) !important;
  padding: 8px !important;
  animation: sg-dropdown-in 0.25s var(--sg-ease) !important;
  backdrop-filter: blur(16px) !important;
  background: rgba(255,255,255,0.97) !important;
}}
@keyframes sg-dropdown-in {{
  from {{ opacity: 0; transform: translateY(-8px) scale(0.97); }}
  to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
.dropdown-item {{
  border-radius: 8px !important;
  padding: 10px 16px !important;
  transition: all 0.2s ease !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}}
.dropdown-item:hover {{
  background: var(--sg-accent-light) !important;
  color: var(--sg-accent-dark) !important;
}}

/* ── PAGINATION — Premium pills ── */
.pagination .page-item .page-link, .pagination a {{
  border-radius: 12px !important;
  margin: 0 3px !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 600 !important;
  transition: all 0.3s ease !important;
  border: 1px solid rgba(0,0,0,0.06) !important;
}}
.pagination .page-item.active .page-link, .pagination a.active {{
  background: var(--sg-grad-accent) !important;
  border-color: transparent !important;
  color: #fff !important;
  box-shadow: var(--sg-shadow-glow) !important;
}}

/* ── SKILL / PROGRESS — Enhanced bars ── */
.progress {{
  height: 8px !important;
  border-radius: 999px !important;
  background: var(--sg-surface-dim) !important;
  overflow: hidden !important;
}}
.progress-bar, .skill-bar {{
  background: var(--sg-grad-accent) !important;
  border-radius: 999px !important;
  position: relative !important;
}}
.progress-bar::after, .skill-bar::after {{
  content: '' !important;
  position: absolute !important;
  inset: 0 !important;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent) !important;
  animation: sg-shimmer 2s ease infinite !important;
  background-size: 200% 100% !important;
}}

/* ── ELEGANT CHECKMARKS in pricing/feature lists ── */
.pricing-table li::before, .pricing-box li::before,
.pricing-card li::before, .single-pricing li::before {{
  color: var(--sg-accent) !important;
  font-weight: bold !important;
}}

/* ── PAGE LOAD ANIMATION ── */
@keyframes sg-page-enter {{
  from {{ opacity: 0; }}
  to {{ opacity: 1; }}
}}
body {{
  animation: sg-page-enter 0.6s var(--sg-ease-smooth) !important;
}}

/* ── PARALLAX-READY SECTIONS ── */
[data-sg-parallax] {{
  will-change: transform !important;
  transition: transform 0.1s linear !important;
}}

/* ── BRAND LOGO GLOW ── */
.navbar-brand svg, .logo svg, .header-logo svg {{
  filter: drop-shadow(0 2px 8px hsla({hue}, 72%, 55%, 0.3)) !important;
  transition: filter 0.3s ease !important;
}}
.navbar-brand:hover svg, .logo:hover svg {{
  filter: drop-shadow(0 4px 16px hsla({hue}, 72%, 55%, 0.5)) !important;
}}

/* ── HOVER CARD GLOW ── */
.card:hover, .service-box:hover, .feature-box:hover {{
  box-shadow: var(--sg-shadow-xl),
    0 0 60px -15px hsla({hue}, 72%, 55%, 0.15) !important;
}}

/* ── ENHANCED ICON STYLING ── */
i[class*="fa-"], i[class*="bi-"], i[class*="icon-"],
i[class*="flaticon-"], i[class*="lnr-"], .material-icons {{
  transition: all 0.4s var(--sg-ease) !important;
}}

/* ── ANIMATED NUMBERS (for counter JS) ── */
.sg-counter-animated {{
  display: inline-block !important;
  font-variant-numeric: tabular-nums !important;
}}

/* ── VIDEO PLAY BUTTON ── */
.play-btn, .video-btn, .play-button, [class*="play-btn"],
[class*="video-btn"] {{
  width: 72px !important;
  height: 72px !important;
  border-radius: 50% !important;
  background: var(--sg-grad-accent) !important;
  color: #fff !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: var(--sg-shadow-glow), 0 0 0 12px hsla({hue}, 72%, 55%, 0.15) !important;
  transition: all 0.4s var(--sg-ease) !important;
  position: relative !important;
}}
.play-btn:hover, .video-btn:hover, .play-button:hover {{
  transform: scale(1.1) !important;
  box-shadow: var(--sg-shadow-glow), 0 0 0 20px hsla({hue}, 72%, 55%, 0.1) !important;
}}
/* Pulse ring on play button */
.play-btn::before, .video-btn::before, .play-button::before {{
  content: '' !important;
  position: absolute !important;
  inset: -8px !important;
  border-radius: 50% !important;
  border: 2px solid hsla({hue}, 72%, 55%, 0.3) !important;
  animation: sg-pulse-ring 2s ease-out infinite !important;
}}
@keyframes sg-pulse-ring {{
  0% {{ transform: scale(1); opacity: 1; }}
  100% {{ transform: scale(1.4); opacity: 0; }}
}}

/* ── MAP / CONTACT SECTION ENHANCEMENT ── */
iframe[src*="google.com/maps"], iframe[src*="openstreetmap"],
.google-map, .map-container, [class*="map-wrap"] {{
  border-radius: var(--sg-radius-lg) !important;
  box-shadow: var(--sg-shadow-lg) !important;
  border: 4px solid #fff !important;
}}

/* ── FEATURE / ICON CARDS — Larger icons ── */
.service-box .icon i, .feature-box .icon i,
.single-service .icon i, .single-feature .icon i,
.service-box i[class*="flaticon"], .feature-box i {{
  font-size: 2.5rem !important;
  line-height: 1 !important;
}}

/* ── HOVER UNDERLINE ANIMATION for text links ── */
a:not(.btn):not(.button):not(.nav-link):not([class*="social"]):not([class*="navbar"]):not([class*="menu"]) {{
  position: relative !important;
}}

/* ── CUSTOM CHECKBOX / RADIO ── */
input[type="checkbox"], input[type="radio"] {{
  accent-color: var(--sg-accent) !important;
}}

/* ── ENHANCED MOBILE NAV ── */
@media (max-width: 991px) {{
  .navbar-collapse, .mobile-menu, .main-menu {{
    background: rgba(255,255,255,0.98) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-radius: var(--sg-radius-lg) !important;
    box-shadow: var(--sg-shadow-xl) !important;
    padding: 16px !important;
    margin-top: 8px !important;
  }}
  .navbar-toggler, .menu-toggle, .hamburger {{
    border: 2px solid var(--sg-accent) !important;
    border-radius: 12px !important;
    padding: 8px 12px !important;
    color: var(--sg-accent) !important;
    transition: all 0.3s ease !important;
  }}
  .navbar-toggler:hover, .menu-toggle:hover {{
    background: var(--sg-accent) !important;
    color: #fff !important;
  }}
}}

/* ── CURSOR BLEND ── */
@media (pointer: fine) {{
  .sg-cursor {{
    position: fixed !important;
    width: 32px !important;
    height: 32px !important;
    border: 2px solid var(--sg-accent) !important;
    border-radius: 50% !important;
    pointer-events: none !important;
    z-index: 2147483647 !important;
    transition: transform 0.15s var(--sg-ease), opacity 0.2s ease, width 0.3s ease, height 0.3s ease !important;
    mix-blend-mode: difference !important;
    transform: translate(-50%, -50%) !important;
    opacity: 0.6 !important;
  }}
  .sg-cursor.sg-cursor-hover {{
    width: 52px !important;
    height: 52px !important;
    background: hsla({hue}, 72%, 55%, 0.1) !important;
    opacity: 0.8 !important;
  }}
}}

/* ── MORE ANIMATION KEYFRAMES ── */
@keyframes sg-float {{
  0%, 100% {{ transform: translateY(0); }}
  50% {{ transform: translateY(-12px); }}
}}
@keyframes sg-rotate-slow {{
  from {{ transform: rotate(0deg); }}
  to {{ transform: rotate(360deg); }}
}}
@keyframes sg-bounce-gentle {{
  0%, 100% {{ transform: translateY(0); }}
  50% {{ transform: translateY(-6px); }}
}}
@keyframes sg-gradient-shift {{
  0% {{ background-position: 0% 50%; }}
  50% {{ background-position: 100% 50%; }}
  100% {{ background-position: 0% 50%; }}
}}
@keyframes sg-text-reveal {{
  from {{ clip-path: inset(0 100% 0 0); }}
  to {{ clip-path: inset(0 0 0 0); }}
}}

/* ── FLOATING ELEMENTS ── */
.sg-float {{ animation: sg-float 6s ease-in-out infinite !important; }}
.sg-float-delay {{ animation: sg-float 6s ease-in-out 1.5s infinite !important; }}

/* ── BREADCRUMB — More premium ── */
.breadcrumb-area, .page-title-area, .page-header:not(.hero-section) {{
  background: var(--sg-grad-hero) !important;
  color: #fff !important;
  padding: 60px 0 !important;
  position: relative !important;
}}
.breadcrumb-area::before, .page-title-area::before {{
  content: '' !important;
  position: absolute !important;
  inset: 0 !important;
  background:
    radial-gradient(ellipse at 20% 50%, hsla({hue}, 80%, 55%, 0.2), transparent 50%),
    radial-gradient(ellipse at 80% 50%, hsla({hue2}, 70%, 50%, 0.15), transparent 50%) !important;
  pointer-events: none !important;
}}
.breadcrumb-area h1, .page-title-area h1,
.breadcrumb-area h2, .page-title-area h2 {{
  color: #fff !important;
}}
.breadcrumb-area a, .breadcrumb a, .page-title-area a {{
  color: rgba(255,255,255,0.7) !important;
}}
.breadcrumb-area a:hover, .breadcrumb a:hover {{
  color: var(--sg-accent-glow) !important;
}}

/* ── ENHANCED RESPONSIVE ── */
@media (max-width: 768px) {{
  .btn, .button, a.btn {{
    padding: 12px 24px !important;
    font-size: 0.85rem !important;
  }}
  .testimonial, .testimonial-item, .testi-card {{ padding: 24px !important; }}
  .pricing-table.active, .pricing-box.active, .pricing-box.featured {{
    transform: scale(1.02) translateY(-4px) !important;
  }}
  h1 {{ font-size: clamp(1.6rem, 6vw, 2.4rem) !important; }}
  h2 {{ font-size: clamp(1.3rem, 5vw, 1.8rem) !important; }}
}}
@media (max-width: 480px) {{
  .card, .service-box, .feature-box {{
    border-radius: var(--sg-radius) !important;
  }}
  .btn, .button, a.btn {{
    padding: 11px 20px !important;
    font-size: 0.82rem !important;
    width: 100% !important;
    text-align: center !important;
  }}
  .hero-wrap, .hero-section, section.hero {{
    min-height: 60vh !important;
  }}
}}

/* ── DARK TEMPLATE OVERRIDES ── */
{('''
/* This template has a dark body background — DO NOT force light colors */
header, .header, .main-header, .top-header, nav.navbar, .navigation,
.navbar-area, .header-area, .site-header, .nav-section {
  background: rgba(0,0,0,0.85) !important;
  border-bottom-color: rgba(255,255,255,0.08) !important;
}
.card, .service-box, .team-member, .project-item, .blog-post,
.services-item, .feature-box, .pricing-box, .testimonial,
.single-service, .single-feature, .work-item, .portfolio-item,
.blog-card, .news-item, .event-item, .course-card {
  background: rgba(255,255,255,0.05) !important;
  border-color: rgba(255,255,255,0.08) !important;
}
.pricing-table, .pricing-box, .price-card, .pricing-card,
.pricing-item, .single-pricing, .price-table {
  background: rgba(255,255,255,0.05) !important;
  border-color: rgba(255,255,255,0.08) !important;
}
.testimonial, .testimonial-item, .testi-card, .review-card,
.testimonial-box, .testimony-wrap, .single-testimonial {
  background: rgba(255,255,255,0.05) !important;
  border-color: rgba(255,255,255,0.08) !important;
}
.contact-area, .contact-section, #contact, .contact-form,
[class*="contact-wrap"] {
  background: rgba(0,0,0,0.3) !important;
}
.process-area, .how-it-works, .steps-section,
[class*="process-wrap"], [class*="step-area"] {
  background: rgba(0,0,0,0.2) !important;
}
.breadcrumb, .breadcrumb-area, [class*="breadcrumb"] {
  background: rgba(0,0,0,0.3) !important;
}
.dropdown-menu {
  background: rgba(20,20,30,0.97) !important;
  border-color: rgba(255,255,255,0.1) !important;
}
.dropdown-item:hover {
  background: rgba(255,255,255,0.08) !important;
}
/* Ensure text visibility on dark backgrounds */
body, section, .section, div {
  color: rgba(255,255,255,0.85) !important;
}
h1, h2, h3, h4, h5, h6 {
  color: #fff !important;
}
p {
  color: rgba(255,255,255,0.7) !important;
}
a:not(.btn):not(.button) {
  color: var(--sg-accent-glow) !important;
}
.modal-content {
  background: rgba(20,20,30,0.95) !important;
}
''' if is_dark_template else '')}

/* ── SYSTEMIC: Prevent mobile horizontal overflow ── */
html, body {{
  overflow-x: hidden !important;
  max-width: 100vw !important;
}}
@media (max-width: 768px) {{
  .container, .container-fluid, .row, section, [class*="section"],
  .site-wrap, main, .wrapper, [class*="wrapper"] {{
    max-width: 100vw !important;
    overflow-x: hidden !important;
  }}
  img, video, iframe, table, pre {{
    max-width: 100% !important;
  }}
  /* Force flex/grid items to shrink */
  [class*="col-"], .owl-item, .slick-slide {{
    flex-shrink: 1 !important;
    min-width: 0 !important;
  }}
}}

/* ── SYSTEMIC: Override template animation libraries that hide content ── */
/* Many Colorlib/FLAVOR templates use .ftco-animate with jQuery Waypoints which
   never fires in iframe preview. Force visibility so sections are always shown.
   Sitegency's own sg-reveal system handles the actual scroll animations. */
.ftco-animate,
.animate-box,
[data-animate-effect],
.wow,
[data-aos],
[class*="aos-init"],
.heading-section,
.section-heading,
.site-section-heading,
.element-animate,
.untree_co-section {{
  opacity: 1 !important;
  visibility: visible !important;
  -webkit-animation-fill-mode: none !important;
  animation-fill-mode: none !important;
}}

/* ── SYSTEMIC: Hide typewriter/typed.js artifacts ── */
/* Template typewriter scripts cycle English words that are not translatable.
   Hide typed spans so the replaced heading text stands on its own. */
.typed-words,
.typed-cursor,
.typed-cursor--blink {{
  display: none !important;
}}

/* ── SYSTEMIC: Tighten excessive section padding ── */
/* Many templates use 100-150px section padding. Normalize to 64px for premium rhythm. */
.site-section:not(footer):not(.footer):not(.site-footer):not(.ftco-footer),
.ftco-section:not(.ftco-footer):not(.footer),
[class*="section-"]:not(nav):not(header):not(footer):not(.site-footer),
.spad:not(footer):not(.footer),
[class*="section_padding"]:not(footer),
[class*="_area"]:not(nav):not(header):not(footer):not(.navbar):not(.header),
[class*="top-padding"], [class*="pb-padding"],
[class*="padding_top"]:not(nav):not(header) {{
  padding-top: 64px !important;
  padding-bottom: 64px !important;
}}

/* ── SYSTEMIC: Hide stripped-credit empty shells ── */
/* After _strip_original_credits removes attribution text, some footer-like
   sections become empty shells with only social icons. Hide them. */
.site-section:empty,
.ftco-section:empty {{
  display: none !important;
}}

/* blocks-cover hero needs position relative for the gradient (consolidated from hero section) */
[class*="blocks-cover"] {{
  position: relative !important;
  overflow: hidden !important;
}}
.site-section-cover.half-bg {{
  position: relative !important;
  overflow: hidden !important;
}}
/* Override the beige half-bg pseudo with a more premium gradient */
.half-bg::before {{
  background: linear-gradient(135deg,
    hsla({hue}, 30%, 95%, 1) 0%,
    hsla({hue2}, 25%, 90%, 0.8) 100%) !important;
  width: 50% !important;
  right: 0 !important;
  left: auto !important;
}}

/* ── Template-specific: agency-vantage hero overlap fix ── */
.section-1 .text-wrap {{
  position: relative !important;
  margin-top: 0 !important;
  top: auto !important;
  left: auto !important;
  z-index: 3 !important;
}}
/* Fix the figure-wrap overflow that causes overlap */
.section-1 .figure-wrap {{
  overflow: visible !important;
  position: relative !important;
}}

/* ── Template-specific: agency-vantage hide dollar prices (not locale-appropriate) ── */
.product strong,
.owl-4-slider .product .text-center strong {{
  display: none !important;
}}

/* ── Template-specific: Strip placeholder nav labels ── */
/* Generically hide dropdown sub-items that are clearly "Menu One" / "Sub Menu" placeholders */
nav a[href="#"]:not(.navbar-brand) {{
  /* keep visible — some legitimate anchors use # */
}}

/* ═══════════════════════════════════════════════════════════════
   AGGRESSIVE PREMIUM UPGRADE LAYER
   These rules transform templates beyond their original design.
   Targets patterns that the original premium layer misses because
   template-specific class names don't match standard selectors.
   ═══════════════════════════════════════════════════════════════ */

/* ── A1: Force ALL section headings to use accent color (no black h2) ── */
section h2, .site-section h2, [class*="section"] h2,
.ftco-section h2, .container h2, main h2 {{
  color: hsla({hue}, 72%, 45%, 1) !important;
  font-weight: 800 !important;
  position: relative !important;
}}

/* ── A2: Image premium treatment (border-radius, hover zoom) ── */
/* Broad selectors: catch images in any section-like container, skip icons/logos */
section img, .site-section img, [class*="section"] img,
.ftco-section img, .container img, main img,
[class*="col-"] img, .row img {{
  border-radius: 10px !important;
  transition: transform 0.4s cubic-bezier(0.22,1,0.36,1), box-shadow 0.4s ease !important;
}}
/* Exempt icons, logos, and tiny images from rounding */
nav img, header img, .navbar-brand img, .navbar img,
img[class*="icon"], img[class*="logo"], img[width="1"],
footer img, .footer img {{
  border-radius: 0 !important;
}}
section img:hover, .site-section img:hover, .ftco-section img:hover,
.container img:hover, [class*="col-"] img:hover {{
  transform: scale(1.03) !important;
  box-shadow: 0 12px 40px rgba(0,0,0,0.12) !important;
}}

/* ── A3: CTA text-links → premium pill buttons ── */
/* Catches ironquill's .more-XXXXX links and similar bare CTA patterns */
a[class*="more-"],
a.read-more,
a[class*="btn-link"],
a[class*="view-more"] {{
  display: inline-block !important;
  padding: 14px 32px !important;
  background: linear-gradient(135deg, hsla({hue}, 72%, 50%, 1), hsla({hue2}, 65%, 55%, 1)) !important;
  color: #fff !important;
  border-radius: 50px !important;
  text-decoration: none !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
  text-transform: uppercase !important;
  box-shadow: 0 4px 15px hsla({hue}, 70%, 50%, 0.35) !important;
  transition: transform 0.3s, box-shadow 0.3s !important;
  border: none !important;
}}
a[class*="more-"]:hover, a.read-more:hover, a[class*="btn-link"]:hover {{
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 25px hsla({hue}, 70%, 50%, 0.45) !important;
}}

/* ── A4: Feature/service card premium treatment ── */
/* Catches elements with "feature" or "service" in class name */
[class*="feature-"],
[class*="service-box"],
.media-body {{
  background: rgba(255,255,255,0.85) !important;
  border-radius: 16px !important;
  padding: 28px 24px !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06) !important;
  transition: transform 0.35s cubic-bezier(0.22,1,0.36,1), box-shadow 0.35s ease !important;
  border: 1px solid rgba(0,0,0,0.04) !important;
}}
[class*="feature-"]:hover,
[class*="service-box"]:hover {{
  transform: translateY(-6px) !important;
  box-shadow: 0 16px 48px rgba(0,0,0,0.10) !important;
}}

/* ── A5: Team/profile circular images — larger, with glow ring ── */
img[style*="border-radius: 50%"],
.team-img,
.team-member img,
.testimonial-img {{
  width: 110px !important;
  height: 110px !important;
  border: 3px solid hsla({hue}, 60%, 85%, 1) !important;
  box-shadow: 0 0 0 6px hsla({hue}, 70%, 50%, 0.15), 0 8px 24px rgba(0,0,0,0.10) !important;
  transition: box-shadow 0.3s !important;
}}

/* ── A6: Portfolio/work grid hover overlay ── */
.work-thumb, .portfolio-thumb, .image, .project-item a,
.ftco-media, [class*="portfolio-"] .img-wrap,
[class*="work-"] a {{
  position: relative !important;
  overflow: hidden !important;
  border-radius: 12px !important;
}}

/* ── A7: Override leaking template accent colors to premium palette ── */
/* Many templates have leftover red/orange/green accents from original design.
   Override both text color and background-color for common leak patterns. */
[style*="color: rgb(255, 99"],
[style*="color: #ff6363"],
[style*="color:#ff6363"],
.text-danger:not(.alert *) {{
  color: hsla({hue}, 72%, 50%, 1) !important;
}}
/* Override bright green backgrounds (rgb(49,222,121) and similar) */
[style*="background-color: rgb(49"],
[style*="background: rgb(49"] {{
  background: linear-gradient(135deg, hsla({hue}, 72%, 50%, 1), hsla({hue2}, 65%, 55%, 1)) !important;
  background-color: hsla({hue}, 72%, 50%, 1) !important;
}}

/* ── A8: Blog/content cards — add card surface ── */
.blog-entry, .post-entry, .blog-card, article.post,
[class*="blog-"] > [class*="col-"],
.section-3 [class*="col-lg-3"],
.section-3 [class*="col-6"] {{
  background: #fff !important;
  border-radius: 14px !important;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06) !important;
  overflow: hidden !important;
  transition: transform 0.3s, box-shadow 0.3s !important;
  padding-bottom: 20px !important;
  margin-bottom: 16px !important;
}}
.blog-entry:hover, .post-entry:hover, .blog-card:hover,
.section-3 [class*="col-"]:hover {{
  transform: translateY(-4px) !important;
  box-shadow: 0 12px 36px rgba(0,0,0,0.10) !important;
}}

/* ── A8b: Equalize card heights within rows ── */
.row > [class*="col-"] > .card,
.row > [class*="col-"] > [class*="card"],
.row > [class*="col-"] > [class*="feature"],
.row > [class*="col-"] > [class*="service"] {{
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}}

/* ── A9: Alternating section backgrounds for visual rhythm ── */
.site-section:nth-child(even):not(.footer):not(.site-footer):not(.ftco-footer),
[class*="section"]:nth-child(even):not(nav):not(header):not(footer):not(.site-footer) {{
  background: linear-gradient(180deg,
    rgba({int(127 + 40 * (hue % 3))}, {int(127 + 30 * (hue % 5))}, {int(200 + 20 * (hue % 4))}, 0.04) 0%,
    rgba({int(127 + 40 * (hue % 3))}, {int(127 + 30 * (hue % 5))}, {int(200 + 20 * (hue % 4))}, 0.02) 100%) !important;
}}

/* ── A10: Section heading accent bar — adds a small colored line above h2 ── */
section h2::before, .site-section h2::before, .ftco-section h2::before,
.container h2::before, main h2::before {{
  content: '' !important;
  display: block !important;
  width: 48px !important;
  height: 3px !important;
  background: linear-gradient(90deg, hsla({hue}, 72%, 50%, 1), hsla({hue2}, 65%, 55%, 1)) !important;
  margin-bottom: 16px !important;
  border-radius: 2px !important;
}}

/* ── B1: Vantage-specific — hero section background gradient ── */
.section-1 {{
  background: linear-gradient(135deg,
    hsla({hue}, 30%, 97%, 1) 0%,
    hsla({hue2}, 25%, 95%, 0.6) 40%,
    hsla({hue}, 20%, 98%, 0.4) 100%) !important;
  position: relative !important;
}}

/* ── B2: ALL templates — footer dark treatment for consistency ── */
.site-footer, .ftco-footer, footer.footer,
footer[class*="footer"], .footer-area {{
  background: linear-gradient(180deg, rgb(17, 24, 39), rgb(7, 10, 18)) !important;
  color: rgba(255,255,255,0.75) !important;
  border-top: 1px solid rgba(255,255,255,0.06) !important;
  padding-top: 64px !important;
  padding-bottom: 40px !important;
}}
.site-footer h3, .site-footer h4, .site-footer .heading,
.ftco-footer h3, .ftco-footer h4, .ftco-footer .heading,
footer h3, footer h4 {{
  color: #fff !important;
}}
.site-footer a, .ftco-footer a, footer.footer a {{
  color: hsla({hue}, 70%, 70%, 1) !important;
}}
.site-footer .social a, .site-footer .social-icons a,
.ftco-footer .social a, footer .social a {{
  background: rgba(255,255,255,0.08) !important;
  color: rgba(255,255,255,0.7) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
}}
.site-footer p, .ftco-footer p, footer.footer p {{
  color: rgba(255,255,255,0.55) !important;
}}

/* ── B3: Nav polish — let templates keep their own navbar identity ── */

/* ── B4: Ironquill-specific — CTA band upgrade ── */
.bg-tertiary {{
  background: linear-gradient(135deg,
    hsla({hue}, 50%, 92%, 1) 0%,
    hsla({hue2}, 40%, 88%, 1) 100%) !important;
  text-align: center !important;
  padding: 72px 40px !important;
  border-radius: 0 !important;
}}
.bg-tertiary h2 {{
  margin-bottom: 24px !important;
}}

/* ── B5: Vantage hero H1 — dramatic, not flat black ── */
.section-1 h1,
.owl-single-text h1 {{
  background: linear-gradient(135deg,
    hsla({hue}, 72%, 30%, 1) 0%,
    hsla({hue2}, 65%, 35%, 1) 100%) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  text-shadow: none !important;
}}

/* ── B6: Vantage slide counter hide (amateurish) ── */
.owl-current, .owl-total {{
  font-size: 0 !important;
}}
em.serif {{
  font-size: 0 !important;
}}

/* ── B7: Override ALL instances of original template accent colors ── */
/* Red accents */
[style*="rgb(255, 99"],
.text-uppercase[style*="color"],
.post-meta {{
  color: hsla({hue}, 72%, 50%, 1) !important;
}}
/* Green accent backgrounds (Colorlib digilab, etc.) — force to premium gradient */
.nav-link.active, .nav.nav-pills .nav-link.active,
.ftco-section .nav-link.active {{
  background: linear-gradient(135deg, hsla({hue}, 72%, 50%, 1), hsla({hue2}, 65%, 55%, 1)) !important;
  color: #fff !important;
}}
/* Override inline bg green on .text containers used by Colorlib templates */
.text.px-4, .col-md-4.ftco-animate.py-5.nav {{
  background: linear-gradient(135deg, hsla({hue}, 72%, 50%, 1), hsla({hue2}, 65%, 55%, 1)) !important;
  color: #fff !important;
}}

{f"""
/* agency-ironquill — identity-preserving styles */
/* Intentionally empty for now — will be built step by step */
""" if slug == 'agency-ironquill' else ''}

/* ── PRINT STYLING ── */
@media print {{
  body::before, .sg-scroll-progress, .sg-back-to-top, .sg-cursor {{ display: none !important; }}
  * {{ box-shadow: none !important; animation: none !important; }}
}}
"""

        style = soup.new_tag('style')
        style['data-bw'] = 'signature'
        style.string = css
        head.append(style)

    def _inject_customizer_runtime(self, soup: BeautifulSoup) -> None:
        """Inject the runtime that listens for customizer messages and applies them."""
        body = soup.find('body')
        if not body:
            return

        # If we have session data, apply it immediately
        initial_data = self.session_data or {}

        import json
        runtime = soup.new_tag('script')
        runtime.string = f"""
(function(){{
  var BW_SELECTORS = {{
    brand_name: ['.site-title','.logo','.navbar-brand','[data-bw="brand_name"]','header h1'],
    brand_tagline: ['.tagline','.site-tagline','[data-bw="brand_tagline"]'],
    hero_title: ['.hero h1','.banner h1','section.hero h1','#hero h1','[data-bw="hero_title"]','header.hero h1','.jumbotron h1'],
    hero_subtitle: ['.hero p','.banner p','section.hero p','#hero p','[data-bw="hero_subtitle"]','.jumbotron p'],
    about_title: ['#about h2','.about h2','[data-bw="about_title"]'],
    about_text: ['#about p','.about p','[data-bw="about_text"]'],
    contact_email: ['a[href^="mailto:"]','.email','[data-bw="contact_email"]'],
    contact_phone: ['a[href^="tel:"]','.phone','[data-bw="contact_phone"]'],
    contact_address: ['.address','[data-bw="contact_address"]'],
    contact_hours: ['.hours','[data-bw="contact_hours"]'],
    footer_copyright: ['footer .copyright','footer p','[data-bw="footer_copyright"]'],
  }};
  var BW_IMG_SELECTORS = {{
    brand_logo: ['.logo img','.navbar-brand img','[data-bw-img="brand_logo"]'],
    hero_image: ['.hero img','section.hero img','.banner img','[data-bw-img="hero_image"]'],
    about_image: ['#about img','.about img','[data-bw-img="about_image"]'],
  }};
  function applyText(key,val){{
    (BW_SELECTORS[key]||[]).forEach(function(sel){{
      document.querySelectorAll(sel).forEach(function(el,i){{
        if(i===0) el.textContent = val;
      }});
    }});
  }}
  function applyImage(key,url){{
    (BW_IMG_SELECTORS[key]||[]).forEach(function(sel){{
      document.querySelectorAll(sel).forEach(function(el){{ el.src = url; }});
    }});
  }}
  function applyColor(primary,secondary,accent){{
    var css = ':root{{';
    if(primary){{ css += '--bs-primary:'+primary+';--primary:'+primary+';--bw-primary:'+primary+';'; }}
    if(secondary){{ css += '--bs-secondary:'+secondary+';--bw-secondary:'+secondary+';'; }}
    if(accent){{ css += '--bw-accent:'+accent+';'; }}
    css += '}}';
    if(primary){{
      css += 'a,.text-primary,.btn-primary,.bg-primary,.navbar-brand{{color:'+primary+'!important;}}';
      css += '.btn-primary,.bg-primary{{background-color:'+primary+'!important;border-color:'+primary+'!important;}}';
    }}
    var st = document.getElementById('bw-runtime-style');
    if(!st){{ st = document.createElement('style'); st.id='bw-runtime-style'; document.head.appendChild(st); }}
    st.textContent = css;
  }}
  window.BW_APPLY = function(data){{
    if(!data) return;
    Object.keys(data).forEach(function(k){{
      var v = data[k];
      if(v == null || v === '') return;
      if(k.startsWith('color_')) return;
      if(BW_IMG_SELECTORS[k]) {{ applyImage(k,v); return; }}
      if(BW_SELECTORS[k]) applyText(k,v);
    }});
    applyColor(data.color_primary, data.color_secondary, data.color_accent);
  }};
  window.addEventListener('message', function(ev){{
    if(!ev.data || ev.data.type !== 'bw:apply') return;
    window.BW_APPLY(ev.data.payload);
  }});
  // Apply initial data if present
  var initial = {json.dumps(initial_data)};
  if(initial && Object.keys(initial).length) window.BW_APPLY(initial);
  // Notify parent we're ready
  try{{ parent.postMessage({{type:'bw:ready'}},'*'); }}catch(e){{}}
}})();
"""
        body.append(runtime)

    def _replace_hero_images(self, soup: BeautifulSoup) -> None:
        """TOTAL image replacement — replace EVERY content image in the template.

        Strategy: forget CSS selectors. Instead, find ALL <img> tags that point to
        local /assets/ URLs (= original template images) and replace them with
        premium Unsplash photos. Only skip genuine icons, logos, and SVGs.

        Also replaces all CSS background-image, data-background, and inline styles.
        """
        try:
            from .content_pool import images_for
            images = images_for(self.template.category.name)
        except Exception:
            return
        if not images:
            return

        slug = getattr(self.template, 'slug', '')
        seed = sum(ord(c) for c in slug)
        img_idx = seed

        def next_img():
            nonlocal img_idx
            url = images[img_idx % len(images)]
            img_idx += 1
            return url

        asset_base = self.asset_base_url()

        # Filename patterns that indicate icons/logos (should NOT be replaced).
        # These are checked against the FILENAME only, so must be specific enough
        # not to catch content images like "check-july.png" or "instagram-1.jpg".
        SKIP_KEYWORDS = (
            'icon', 'logo', 'favicon', 'brand-',
            'arrow-', 'chevron-', 'close-btn', 'menu-icon',
            'hamburger', 'toggle-', 'spinner', 'loader',
            'play-btn', 'search-icon',
            'checkmark', 'check-icon', 'tick-icon',
            'cross-icon', 'plus-icon', 'minus-icon',
            'star-icon', 'star-rating', 'quote-icon',
            'map-marker', 'pin-icon',
            'fb-icon', 'tw-icon', 'ig-icon', 'li-icon',
            'separator', 'divider', 'ornament',
            'shape-', 'wave-', 'dot-pattern', 'line-pattern',
        )
        # Directories that indicate icon/logo collections
        SKIP_DIRS = ('/icon/', '/icons/', '/logo/', '/logos/', '/social/',
                     '/brand/', '/brands/', '/clients-logo/')
        SKIP_EXTENSIONS = ('.svg', '.gif', '.ico')

        def should_skip_img(src_str):
            """Return True if this image should NOT be replaced (icon/logo/tiny)."""
            low = src_str.lower()
            # Skip non-photo formats
            if any(low.endswith(ext) or (ext + '?') in low for ext in SKIP_EXTENSIONS):
                return True
            # Skip if in an icon/logo directory
            if any(d in low for d in SKIP_DIRS):
                return True
            # Check the filename for icon/logo markers
            fname = low.split('/')[-1].split('?')[0]
            if any(kw in fname for kw in SKIP_KEYWORDS):
                return True
            # Skip external URLs (already not from original template)
            if low.startswith(('http://', 'https://', '//', 'data:')):
                return True
            return False

        replaced_ids = set()
        _img_replace_count = 0  # [PERF] track replaced images for lazy loading

        # ── PASS 1: Replace ALL <img> tags with local asset URLs ──
        for img in soup.find_all('img'):
            img_id = id(img)
            if img_id in replaced_ids:
                continue

            src = _safe_get_attr(img, 'src') or ''
            if not isinstance(src, str) or not src.strip():
                # Also check data-src for lazy-loaded images
                src = _safe_get_attr(img, 'data-src') or ''
                if not isinstance(src, str) or not src.strip():
                    continue

            if should_skip_img(src):
                continue

            # Check parent for logo/icon context
            parent_classes = ''
            ancestor = img.parent
            depth = 0
            is_logo_context = False
            while ancestor and depth < 4:
                cls_list = [c.lower() for c in (_safe_get_attr(ancestor, 'class') or [])]
                cls = ' '.join(cls_list)
                tag_id = (_safe_get_attr(ancestor, 'id') or '').lower()
                parent_classes += ' ' + cls + ' ' + tag_id
                # Only match direct logo/brand containers, NOT partner/client logo sections
                LOGO_CLASSES = ('logo', 'brand', 'navbar-brand', 'site-title',
                                'site-logo', 'header-logo', 'footer-logo')
                EXCLUDE_LOGO = ('partner', 'client', 'sponsor', 'trust',
                                'gallery', 'carousel', 'slider', 'event')
                if any(lc in cls_list or lc == tag_id for lc in LOGO_CLASSES):
                    # But NOT if it's a partner/client logo section
                    if not any(exc in cls for exc in EXCLUDE_LOGO):
                        is_logo_context = True
                        break
                ancestor = ancestor.parent
                depth += 1

            if is_logo_context:
                continue

            # Replace the image
            try:
                new_url = next_img()
                img['src'] = new_url
                # Set meaningful alt text
                cat_name = self.template.category.name if hasattr(self.template, 'category') else ''
                img['alt'] = f'{self.template.name} — {cat_name}'
                # Clean up srcset to prevent browser using old images
                if img.has_attr('srcset'):
                    del img['srcset']
                # Update data-src for lazy loaders
                if img.has_attr('data-src'):
                    img['data-src'] = new_url
                if img.has_attr('data-lazy'):
                    img['data-lazy'] = new_url
                if img.has_attr('data-original'):
                    img['data-original'] = new_url
                # [PERF] Add lazy loading: first image is LCP (eager),
                # all others get loading="lazy" to prevent scroll jank
                _img_replace_count += 1
                if _img_replace_count == 1:
                    img['fetchpriority'] = 'high'
                    img['loading'] = 'eager'
                else:
                    img['loading'] = 'lazy'
                replaced_ids.add(img_id)
            except Exception:
                pass

        # ── PASS 2: Replace data-background / data-bg attributes on ANY element ──
        for attr_name in ('data-background', 'data-bg', 'data-bg-image',
                          'data-image', 'data-bg-img', 'data-src'):
            for el in soup.find_all(attrs={attr_name: True}):
                if el.name == 'img':
                    continue  # Already handled in PASS 1
                val = _safe_get_attr(el, attr_name) or ''
                if not isinstance(val, str):
                    continue
                low = val.lower()
                if low.startswith(('http://', 'https://', '//', 'data:')):
                    continue
                if any(low.endswith(ext) for ext in SKIP_EXTENSIONS):
                    continue
                try:
                    el[attr_name] = next_img()
                except Exception:
                    pass

        # ── PASS 3: Replace ALL inline style background-image on ANY element ──
        for el in soup.find_all(style=True):
            style = _safe_get_attr(el, 'style') or ''
            if not isinstance(style, str):
                continue
            if 'url(' not in style.lower():
                continue
            # Check if the URL is a local asset (not already external)
            url_match = re.search(r'url\([\'"]?([^\'")]+)[\'"]?\)', style)
            if not url_match:
                continue
            url_val = url_match.group(1)
            low_url = url_val.lower()
            if low_url.startswith(('http://', 'https://', '//', 'data:')):
                continue
            if any(low_url.endswith(ext) for ext in SKIP_EXTENSIONS):
                continue
            if any(kw in low_url.split('/')[-1] for kw in SKIP_KEYWORDS):
                continue
            if any(d in low_url for d in SKIP_DIRS):
                continue
            try:
                img_url = next_img()
                el['style'] = re.sub(
                    r'url\([\'"]?[^\'")]+[\'"]?\)',
                    f'url({img_url})',
                    style,
                    count=1
                )
            except Exception:
                pass

        # ── PASS 4: Replace background-image in <style> blocks ──
        for style_tag in soup.find_all('style'):
            if not style_tag.string:
                continue
            css_text = style_tag.string
            if 'url(' not in css_text:
                continue
            # Find all url() references to local assets
            def replace_css_url(match):
                url_val = match.group(1)
                low = url_val.lower()
                if low.startswith(('http://', 'https://', '//', 'data:')):
                    return match.group(0)
                if any(low.endswith(ext) for ext in SKIP_EXTENSIONS):
                    return match.group(0)
                if any(kw in low.split('/')[-1] for kw in SKIP_KEYWORDS):
                    return match.group(0)
                if any(d in low for d in SKIP_DIRS):
                    return match.group(0)
                # Only replace image URLs, not font URLs
                if re.search(r'\.(woff2?|ttf|otf|eot)(\?|$)', low):
                    return match.group(0)
                return f'url({next_img()})'

            try:
                new_css = re.sub(r'url\([\'"]?([^\'")]+)[\'"]?\)', replace_css_url, css_text)
                if new_css != css_text:
                    style_tag.string = new_css
            except Exception:
                pass

        # ── PASS 5: Replace <a href> pointing to image files (lightbox/gallery) ──
        IMG_EXTENSIONS = re.compile(r'\.(jpe?g|png|webp|bmp|tiff?)(\?|$)', re.I)
        for a_tag in soup.find_all('a', href=True):
            href = _safe_get_attr(a_tag, 'href') or ''
            if not isinstance(href, str):
                continue
            low_href = href.lower()
            # Skip external URLs
            if low_href.startswith(('http://', 'https://', '//', '#', 'mailto:', 'tel:', 'javascript:')):
                continue
            # Only replace if href points to an image file
            if not IMG_EXTENSIONS.search(low_href):
                continue
            # Skip if it's a logo/icon
            fname = low_href.split('/')[-1]
            if any(kw in fname for kw in ('icon', 'logo', 'favicon')):
                continue
            try:
                a_tag['href'] = next_img()
            except Exception:
                pass

        # ── PASS 6: Inject background-image on hero elements that have NO image ──
        # Some templates (e.g. ironquill with .ftco-blocks-cover-1) have a hero
        # section with no background-image and no <img>. Detect and inject.
        HERO_SELECTORS = [
            '[class*="blocks-cover"]', '.site-section-cover',
            '.hero-wrap', '.hero-section', 'section.hero', '#hero',
            '.banner-area', '.slider-area', '.home-slider',
            '.banner', '.jumbotron', '.main-banner',
        ]
        for sel in HERO_SELECTORS:
            for hero_el in soup.select(sel):
                # Check if this hero ITSELF already has a background-image
                existing_style = _safe_get_attr(hero_el, 'style') or ''
                if 'background-image' in existing_style.lower():
                    continue
                # Check if it has direct <img> children at first level only
                # (skip checking deep children — carousel images may not be visible)
                direct_imgs = [c for c in hero_el.children
                               if getattr(c, 'name', None) == 'img']
                if direct_imgs:
                    continue
                # Inject a premium background image on the hero itself
                try:
                    new_url = next_img()
                    hero_el['style'] = (existing_style.rstrip('; ') +
                        f'; background-image: url({new_url}) !important;'
                        ' background-size: cover !important;'
                        ' background-position: center !important;'
                    ).lstrip('; ')
                except Exception:
                    pass

    def _inject_brand_identity(self, soup: BeautifulSoup) -> None:
        """Deep brand replacement — replace the original template's logo and brand
        name EVERYWHERE with the Sitegency creative name. Generates an SVG logo
        and replaces all text occurrences of the old brand.

        This ensures zero traces of the original template brand remain.
        """
        slug = getattr(self.template, 'slug', '')
        seed = sum(ord(c) for c in slug)
        cat = self.template.category.name if hasattr(self.template, 'category') else ''
        brand = getattr(self.template, 'name', slug.replace('-', ' ').title())

        # Deterministic accent color for the SVG logo
        primary_hues = [225, 235, 248, 258, 268, 278, 290, 300, 312, 325, 338, 210]
        hue = primary_hues[seed % len(primary_hues)]
        hue2 = (hue + 137) % 360

        # Generate inline SVG logo — sophisticated monogram with gradient
        first_letter = brand[0].upper() if brand else 'S'
        second_letter = brand[1].lower() if len(brand) > 1 else ''
        # Eight logo shape variants based on seed for maximum diversity
        shape_variant = seed % 8
        gid = f'sg-lg-{seed}'
        g2id = f'sg-lg2-{seed}'

        # Gradient definitions (shared across all variants)
        gradient_defs = (
            f'<linearGradient id="{gid}" x1="0%" y1="0%" x2="100%" y2="100%">'
            f'<stop offset="0%" style="stop-color:hsl({hue},72%,55%)"/>'
            f'<stop offset="100%" style="stop-color:hsl({hue2},60%,55%)"/>'
            f'</linearGradient>'
            f'<linearGradient id="{g2id}" x1="0%" y1="100%" x2="100%" y2="0%">'
            f'<stop offset="0%" style="stop-color:hsl({hue},72%,45%)"/>'
            f'<stop offset="100%" style="stop-color:hsl({hue2},60%,65%)"/>'
            f'</linearGradient>'
        )

        if shape_variant == 0:
            # Rounded square with inner accent line
            shape = (
                f'<rect rx="10" width="40" height="40" fill="url(#{gid})"/>'
                f'<rect x="4" y="4" rx="7" width="32" height="32" fill="none" '
                f'stroke="rgba(255,255,255,0.2)" stroke-width="1"/>'
            )
        elif shape_variant == 1:
            # Circle with outer ring
            shape = (
                f'<circle cx="20" cy="20" r="20" fill="url(#{gid})"/>'
                f'<circle cx="20" cy="20" r="17" fill="none" '
                f'stroke="rgba(255,255,255,0.2)" stroke-width="0.8"/>'
            )
        elif shape_variant == 2:
            # Diamond (rotated square)
            shape = (
                f'<rect x="6" y="6" width="28" height="28" rx="6" fill="url(#{gid})" '
                f'transform="rotate(45 20 20)"/>'
            )
        elif shape_variant == 3:
            # Hexagon
            shape = (
                f'<polygon points="20,2 36,11 36,29 20,38 4,29 4,11" fill="url(#{gid})"/>'
                f'<polygon points="20,6 32,13 32,27 20,34 8,27 8,13" fill="none" '
                f'stroke="rgba(255,255,255,0.15)" stroke-width="0.8"/>'
            )
        elif shape_variant == 4:
            # Rounded square with gradient split (two-tone)
            shape = (
                f'<rect rx="12" width="40" height="40" fill="url(#{gid})"/>'
                f'<rect rx="0" x="20" width="20" height="40" fill="url(#{g2id})" opacity="0.4"/>'
            )
        elif shape_variant == 5:
            # Circle with dot accent
            shape = (
                f'<circle cx="20" cy="20" r="20" fill="url(#{gid})"/>'
                f'<circle cx="33" cy="7" r="4" fill="hsl({hue2},60%,65%)" opacity="0.9"/>'
            )
        elif shape_variant == 6:
            # Shield shape
            shape = (
                f'<path d="M20,2 L36,10 L36,26 C36,32 28,38 20,40 '
                f'C12,38 4,32 4,26 L4,10 Z" fill="url(#{gid})"/>'
            )
        else:
            # Squircle with inner glow
            shape = (
                f'<rect rx="14" width="40" height="40" fill="url(#{gid})"/>'
                f'<ellipse cx="20" cy="16" rx="14" ry="10" fill="rgba(255,255,255,0.1)"/>'
            )

        svg_logo = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" '
            f'style="width:36px;height:36px;vertical-align:middle;margin-right:10px;'
            f'display:inline-block;flex-shrink:0;filter:drop-shadow(0 2px 6px hsla({hue},72%,55%,0.3));">'
            f'<defs>{gradient_defs}</defs>'
            f'{shape}'
            f'<text x="50%" y="53%" text-anchor="middle" dominant-baseline="middle" '
            f'fill="#fff" font-family="\'Playfair Display\',Georgia,serif" font-weight="700" '
            f'font-size="19" letter-spacing="-0.5">{first_letter}</text></svg>'
        )

        # ── 1) Replace text in logo/brand elements ──
        BRAND_SELECTORS = [
            '.navbar-brand', '.site-title', '.logo-text',
            'a.navbar-brand', '.brand-name',
            '.header-logo', '.site-name', '.footer-logo',
            '.footer-brand', '.footer-logo a',
            'h1.site-logo a', 'h1.logo a',
            '.logo a', 'a.logo', '.logo-area a',
            'header .logo a', 'nav .logo a',
        ]
        logo_replaced = False
        for selector in BRAND_SELECTORS:
            for el in soup.select(selector):
                try:
                    txt = el.get_text(strip=True)
                    if not txt or len(txt) > 50:
                        continue
                    # If it has an <img>, REPLACE it with our SVG logo
                    img = el.find('img')
                    if img:
                        try:
                            svg_soup = BeautifulSoup(svg_logo, 'html.parser')
                            img.replace_with(svg_soup)
                            # Set remaining text to brand name
                            for child in list(el.children):
                                if isinstance(child, NavigableString):
                                    s = str(child).strip()
                                    if s and s != brand:
                                        child.replace_with(brand)
                            logo_replaced = True
                        except Exception:
                            pass
                    else:
                        # Clear ALL content and replace with brand name.
                        # Preserve only icon elements (i, svg with icon classes).
                        KEEP_TAGS = {'i', 'svg', 'img', 'picture'}
                        ICON_KEYWORDS = ('fa-', 'fa ', 'icon', 'flaticon', 'bi-', 'lnr-')

                        def _is_icon(elem):
                            if isinstance(elem, NavigableString):
                                return False
                            if not hasattr(elem, 'name') or not elem.name:
                                return False
                            if elem.name in KEEP_TAGS:
                                return True
                            cls = ' '.join(elem.get('class', []) or []).lower() if hasattr(elem, 'get') else ''
                            return any(kw in cls for kw in ICON_KEYWORDS)

                        # Remove everything except icons
                        for child in list(el.descendants):
                            if isinstance(child, NavigableString):
                                if not _is_icon(child.parent):
                                    child.replace_with('')
                            elif hasattr(child, 'name') and child.name not in KEEP_TAGS:
                                cls = ' '.join(child.get('class', []) or []).lower()
                                if not any(kw in cls for kw in ICON_KEYWORDS):
                                    # Decompose text-bearing children, but unwrap
                                    # containers that hold icons
                                    has_icon_child = any(_is_icon(gc) for gc in child.descendants if not isinstance(gc, NavigableString))
                                    if not has_icon_child:
                                        child.decompose()
                        # Insert brand name
                        el.append(brand)
                        logo_replaced = True
                except Exception:
                    pass

        # ── 2) For text-only brand elements, prepend SVG logo icon ──
        if not logo_replaced:
            # Find the PRIMARY brand element — try class-based selectors first
            LOGO_SELECTORS = [
                '.navbar-brand', 'a.navbar-brand', 'h1.site-logo a',
                '.logo a', '.logo-area a', 'a.logo', '.header-logo a',
                '.site-logo a', '.brand a', 'a.brand',
            ]
            for sel in LOGO_SELECTORS:
                target = soup.select_one(sel)
                if target:
                    try:
                        if not target.find('svg'):
                            svg_soup = BeautifulSoup(svg_logo, 'html.parser')
                            target.insert(0, svg_soup)
                            logo_replaced = True
                    except Exception:
                        pass
                    break

        # ── 2b) Fallback: first <a> in header/nav that has an <img> or looks like a logo ──
        if not logo_replaced:
            header = soup.find(['header', 'nav'])
            if header:
                # First try: <a> with an <img> child (logo image)
                for a_tag in header.find_all('a', recursive=True)[:5]:
                    img = a_tag.find('img')
                    if img:
                        try:
                            svg_soup = BeautifulSoup(svg_logo, 'html.parser')
                            img.replace_with(svg_soup)
                            # Set text to brand name
                            for child in list(a_tag.children):
                                if isinstance(child, NavigableString):
                                    s = str(child).strip()
                                    if s and s != brand:
                                        child.replace_with(brand)
                            logo_replaced = True
                        except Exception:
                            pass
                        break
            # Second try: first <a> in header with short text (likely brand)
            if not logo_replaced and header:
                for a_tag in header.find_all('a', recursive=True)[:3]:
                    txt = a_tag.get_text(strip=True)
                    if txt and len(txt) < 30 and not a_tag.find('svg'):
                        try:
                            # Clear all existing content (old brand text)
                            for child in list(a_tag.children):
                                if isinstance(child, NavigableString):
                                    child.replace_with('')
                                elif hasattr(child, 'name') and child.name not in ('svg',):
                                    child.decompose()
                            svg_soup = BeautifulSoup(svg_logo, 'html.parser')
                            a_tag.insert(0, svg_soup)
                            # Append brand as a styled span (avoids SVG letter + brand concatenation)
                            brand_span = soup.new_tag('span')
                            brand_span['style'] = 'margin-left:4px;'
                            brand_span.string = brand
                            a_tag.append(brand_span)
                            logo_replaced = True
                        except Exception:
                            pass
                        break

        # ── 2c) Remove ALL remaining original logo images in header/nav ──
        # After inserting our SVG, any remaining <img> in brand/logo elements is the old logo
        for header_el in soup.find_all(['header', 'nav']):
            for img in header_el.find_all('img'):
                try:
                    src = (img.get('src') or img.get('data-src') or '').lower()
                    cls = ' '.join(img.get('class', []) or []).lower()
                    alt = (img.get('alt') or '').lower()
                    # Is this a logo image?
                    is_logo = any(kw in src + cls + alt for kw in ('logo', 'brand', 'site-logo'))
                    # Or is it an img inside a brand-like parent?
                    parent_cls = ' '.join((img.parent.get('class', []) or [])).lower() if img.parent else ''
                    is_brand_parent = any(kw in parent_cls for kw in ('logo', 'brand', 'navbar-brand', 'site-title'))
                    # Or is this simply a non-Unsplash img in the logo area (first <a>)?
                    is_first_link_img = False
                    parent_a = img.find_parent('a')
                    if parent_a:
                        prev_siblings = list(parent_a.parent.children) if parent_a.parent else []
                        a_tags = [c for c in prev_siblings if hasattr(c, 'name') and c.name == 'a']
                        if a_tags and a_tags[0] == parent_a:
                            is_first_link_img = True
                    if (is_logo or is_brand_parent or is_first_link_img) and 'unsplash' not in src:
                        img.decompose()
                except Exception:
                    pass

        # ── 3) Deep text replacement: find ALL occurrences of old brand names ──
        # Build comprehensive list of old names from multiple sources
        source_dir = getattr(self.template, 'source_dir', '')
        old_names = set()

        # Source 0: scan ORIGINAL raw HTML for the folder name with actual casing
        # (must run before Sources 2/3 which use already-modified soup)
        if source_dir:
            try:
                raw_path = self.template_root / (self.template.pages.filter(is_entry=True).first() or
                                                  self.template.pages.first()).file_path
                raw_html = raw_path.read_text(encoding='utf-8', errors='ignore') if raw_path.exists() else ''
            except Exception:
                raw_html = ''
            if raw_html:
                # Extract from <title>
                import re as _re
                title_m = _re.search(r'<title[^>]*>([^<]{3,60})</title>', raw_html, _re.I)
                if title_m:
                    raw_title = title_m.group(1).strip()
                    for sep in [' - ', ' | ', ' – ', ' — ', ' : ']:
                        if sep in raw_title:
                            potential = raw_title.split(sep)[0].strip()
                            if 2 < len(potential) < 30 and potential.lower() != brand.lower():
                                old_names.add(potential)
                                old_names.add(potential.lower())
                                old_names.add(potential.upper())
                            break
                    if len(raw_title) < 30 and raw_title.lower() != brand.lower():
                        old_names.add(raw_title)
                        old_names.add(raw_title.lower())
                        # Space-collapsed variant: "Dr PRO" → "DrPRO"
                        no_space = raw_title.replace(' ', '')
                        if no_space.lower() != brand.lower():
                            old_names.add(no_space)
                            old_names.add(no_space.lower())
                            old_names.add(no_space.upper())

                # Extract subtitle/tagline from logo area in raw HTML
                # e.g. "Plastic Surgery" under "DrPRO"
                for pattern_sub in [
                    r'<(?:div|span|p|small)[^>]*class="[^"]*(?:subtitle|tagline|slogan|brand-desc)[^"]*"[^>]*>([^<]{3,40})</(?:div|span|p|small)>',
                    r'<(?:div|span|p|small)[^>]*class="[^"]*(?:logo-sub|logo-text|site-desc)[^"]*"[^>]*>([^<]{3,40})</(?:div|span|p|small)>',
                ]:
                    for sm in _re.finditer(pattern_sub, raw_html[:5000], _re.I):
                        sub_text = sm.group(1).strip()
                        if 3 < len(sub_text) < 30 and sub_text.lower() != brand.lower():
                            old_names.add(sub_text)
                            old_names.add(sub_text.lower())

                # Find ACTUAL casing of folder name in the raw HTML
                parts_dir = source_dir.replace(chr(92), '/').split('/')
                fn = parts_dir[-1] if parts_dir[-1] else (parts_dir[-2] if len(parts_dir) > 1 else '')
                if fn and len(fn) > 2:
                    pattern = _re.compile(_re.escape(fn), _re.I)
                    for m in pattern.finditer(raw_html[:10000]):
                        actual = m.group(0)
                        if actual.lower() != brand.lower():
                            old_names.add(actual)

        # Source 1: folder name and all variants
        if source_dir:
            parts = source_dir.replace(chr(92), '/').split('/')
            if parts:
                folder_name = parts[-1] if parts[-1] else (parts[-2] if len(parts) > 1 else '')
                if folder_name and len(folder_name) > 2:
                    old_names.add(folder_name)
                    old_names.add(folder_name.replace('-', ' '))
                    old_names.add(folder_name.replace('_', ' '))
                    old_names.add(folder_name.title())
                    old_names.add(folder_name.replace('-', ' ').title())
                    old_names.add(folder_name.replace('_', ' ').title())
                    old_names.add(folder_name.upper())
                    old_names.add(folder_name.lower())
                    old_names.add(folder_name.capitalize())
                    # CamelCase: "doglife" → "DogLife"
                    if len(folder_name) > 4:
                        mid = len(folder_name) // 2
                        old_names.add(folder_name[:mid].capitalize() + folder_name[mid:].capitalize())

        # Source 2: <title> tag before our replacement
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            if title_text:
                for sep in [' - ', ' | ', ' – ', ' — ', ' : ', ' — ']:
                    if sep in title_text:
                        potential_brand = title_text.split(sep)[0].strip()
                        if 2 < len(potential_brand) < 30 and potential_brand.lower() != brand.lower():
                            old_names.add(potential_brand)
                            old_names.add(potential_brand.lower())
                            old_names.add(potential_brand.upper())
                            old_names.add(potential_brand.title())
                # Also the full title if short
                if len(title_text) < 30 and title_text.lower() != brand.lower():
                    old_names.add(title_text)

        # Source 3: detect brand from the first navbar-brand or logo text
        for sel in ['.navbar-brand', '.logo a', '.site-title', 'header .logo']:
            for el in soup.select(sel):
                try:
                    txt = el.get_text(strip=True)
                    if txt and 2 < len(txt) < 30 and txt.lower() != brand.lower():
                        old_names.add(txt)
                        old_names.add(txt.lower())
                        old_names.add(txt.upper())
                        old_names.add(txt.title())
                except Exception:
                    pass

        # Source 4: detect brand from first H1 (hero headline)
        first_h1 = soup.find('h1')
        if first_h1:
            try:
                h1_txt = first_h1.get_text(strip=True)
                # Only if it looks like a brand name (short, not a sentence)
                if h1_txt and 2 < len(h1_txt) < 25 and ' ' not in h1_txt:
                    if h1_txt.lower() != brand.lower():
                        old_names.add(h1_txt)
                        old_names.add(h1_txt.lower())
                        old_names.add(h1_txt.upper())
            except Exception:
                pass

        # Clean up: remove empty strings, the new brand, common words,
        # and crucially: names that are SUBSTRINGS of the new brand (would cause
        # "Hnband Pro" → "Hnband Pro Pro" when replacing "hnband" with "Hnband Pro")
        STOP_WORDS = {'the', 'and', 'for', 'com', 'www', 'free', 'html', 'css',
                      'template', 'page', 'home', 'index', 'site', 'web',
                      'bootstrap', 'starter', 'demo', 'theme'}
        brand_low = brand.lower()
        old_names = {n for n in old_names if n and len(n) > 2
                     and n.lower() != brand_low
                     and n.lower() not in brand_low  # prevent substring corruption
                     and n.lower() not in STOP_WORDS}

        # Walk ALL text nodes and replace old brand names with new brand
        # Use word-boundary regex to avoid corrupting words that contain
        # old_name as a substring (e.g. "Lavori" when old_name is "L" or "ri")
        if old_names:
            SKIP_TAGS = {'script', 'style', 'code', 'pre', 'noscript'}
            # Pre-compile word-boundary patterns (longest first to avoid partial replacements)
            _brand_patterns = []
            for old_name in sorted(old_names, key=len, reverse=True):
                escaped = re.escape(old_name)
                _brand_patterns.append(re.compile(r'\b' + escaped + r'\b', re.IGNORECASE))

            def replace_brands_in_tree(node, depth=0):
                if depth > 30:
                    return
                try:
                    for child in list(getattr(node, 'children', [])):
                        if isinstance(child, NavigableString):
                            txt = str(child)
                            new_txt = txt
                            for pat in _brand_patterns:
                                new_txt = pat.sub(brand, new_txt)
                            if new_txt != txt:
                                try:
                                    child.replace_with(new_txt)
                                except Exception:
                                    pass
                        else:
                            name = getattr(child, 'name', None)
                            if name and name.lower() in SKIP_TAGS:
                                continue
                            replace_brands_in_tree(child, depth + 1)
                except Exception:
                    return

            body = soup.find('body')
            if body:
                replace_brands_in_tree(body)

            # Also replace in attributes (word-boundary safe)
            for tag in soup.find_all(True):
                for attr in ('alt', 'title', 'aria-label', 'placeholder'):
                    val = _safe_get_attr(tag, attr)
                    if val and isinstance(val, str):
                        new_val = val
                        for pat in _brand_patterns:
                            new_val = pat.sub(brand, new_val)
                        if new_val != val:
                            try:
                                tag[attr] = new_val
                            except Exception:
                                pass

        # ── 4) Update <title> tag ──
        title_tag = soup.find('title')
        if title_tag:
            try:
                title_tag.string = f"{brand} — {cat}"
            except Exception:
                pass

        # ── 5) Update meta description ──
        for meta in soup.find_all('meta', attrs={'name': 'description'}):
            try:
                meta['content'] = f"{brand} — Premium {cat} website template by Sitegency"
            except Exception:
                pass

    def _cleanup_placeholder_text(self, soup: BeautifulSoup) -> None:
        """Final pass: replace ANY remaining Lorem ipsum text in the DOM.

        This catches Lorem in <li>, <a>, <span>, <div>, and other elements
        that the pool content replacement skips because they're inside
        special parent structures.
        """
        try:
            from .content_pool import pool_for
            cat = self.template.category.name if hasattr(self.template, 'category') else ''
            try:
                locale = (get_language() or 'en').split('-')[0]
            except Exception:
                locale = 'en'
            pool = pool_for(cat, locale)
            short_pool = pool.get('p_short', pool.get('services', ['Professional service']))
        except Exception:
            short_pool = ['Professional service', 'Quality care', 'Expert team']

        if not short_pool:
            short_pool = ['Professional service', 'Quality care', 'Expert team']

        LOREM_MARKERS = ('lorem ipsum', 'dolor sit amet', 'consectetur adipisicing',
                         'consectetur adipiscing', 'far far away, behind the word',
                         'behind the word mountains', 'countries vokalia and consonantia',
                         'there live the blind texts', 'blind texts',
                         'officia quaerat eaque', 'possimus aut consequuntur',
                         'dolorum esse odio', 'architecto sint',
                         'separated they live in', 'even the all-powerful pointing',
                         'pityful a rethoric question', 'contenu d\'exemple')
        idx = 0

        body = soup.find('body')
        if not body:
            return

        def walk_and_clean(node, depth=0):
            nonlocal idx
            if depth > 25:
                return
            try:
                for child in list(getattr(node, 'children', [])):
                    if isinstance(child, NavigableString):
                        txt = str(child)
                        if len(txt.strip()) > 15 and any(m in txt.lower() for m in LOREM_MARKERS):
                            replacement = short_pool[idx % len(short_pool)]
                            try:
                                child.replace_with(replacement)
                                idx += 1
                            except Exception:
                                pass
                    else:
                        name = getattr(child, 'name', None)
                        if name in ('script', 'style', 'code', 'pre'):
                            continue
                        walk_and_clean(child, depth + 1)
            except Exception:
                return

        walk_and_clean(body)

    def _inject_premium_interactivity(self, soup: BeautifulSoup) -> None:
        """Inject advanced JS micro-interactions for ultra-premium feel.

        Adds: scroll progress bar, back-to-top button, counter animations,
        parallax hero, staggered card reveals, custom cursor, smooth page
        transitions, and enhanced hover effects.
        """
        body = soup.find('body')
        if not body:
            return

        slug = getattr(self.template, 'slug', '')
        seed = sum(ord(c) for c in slug)
        primary_hues = [225, 235, 248, 258, 268, 278, 290, 300, 312, 325, 338, 210]
        hue = primary_hues[seed % len(primary_hues)]

        script = soup.new_tag('script')
        script.string = f"""
(function(){{
  'use strict';
  if(typeof window.__sg_premium_init!=='undefined')return;
  window.__sg_premium_init=true;

  /* ── NAVBAR DEDUPLICATION ── */
  /* Detect and hide duplicate navigation menus (offcanvas/sidebar that leak on desktop) */
  (function(){{
    var allNavs=document.querySelectorAll('nav, [class*="navbar"], [class*="nav-menu"], [class*="main-menu"], [class*="primary-menu"]');
    if(allNavs.length<2) return;
    /* Build a signature for each nav based on link hrefs */
    var sigs={{}};
    allNavs.forEach(function(nav){{
      var links=nav.querySelectorAll('a');
      if(links.length<3) return;
      var sig=Array.from(links).map(function(a){{return a.getAttribute('href')||'';}}).slice(0,8).join('|');
      if(!sig) return;
      if(!sigs[sig]) sigs[sig]=[];
      sigs[sig].push(nav);
    }});
    /* If duplicates found, hide all but the one that's in/near a header */
    Object.values(sigs).forEach(function(navs){{
      if(navs.length<2) return;
      var primary=null;
      navs.forEach(function(n){{
        if(n.closest('header') || n.closest('[class*="header"]') || n.tagName==='NAV'){{
          if(!primary) primary=n;
        }}
      }});
      if(!primary) primary=navs[navs.length-1];
      navs.forEach(function(n){{
        if(n!==primary){{
          n.style.display='none';
          n.setAttribute('aria-hidden','true');
        }}
      }});
    }});
    /* Also hide standalone duplicate ULs that mirror the main nav */
    var header=document.querySelector('header, [class*="header"], nav.navbar');
    if(!header) return;
    var mainLinks=header.querySelectorAll('a[href]');
    if(mainLinks.length<3) return;
    var mainSig=Array.from(mainLinks).slice(0,6).map(function(a){{return a.getAttribute('href');}}).join('|');
    document.querySelectorAll('body > div > ul, body > div > div > ul').forEach(function(ul){{
      var ulLinks=ul.querySelectorAll('a[href]');
      if(ulLinks.length<3) return;
      var ulSig=Array.from(ulLinks).slice(0,6).map(function(a){{return a.getAttribute('href');}}).join('|');
      if(ulSig===mainSig){{
        var parent=ul.parentElement;
        if(parent && !parent.closest('header') && !parent.closest('[class*="header"]')){{
          parent.style.display='none';
          parent.setAttribute('aria-hidden','true');
        }}
      }}
    }});
  }})();

  /* ── 404 LINK INTERCEPTION ── */
  /* Catch clicks on links that would lead to 404 and redirect to main page */
  (function(){{
    var baseUrl=window.location.pathname;
    /* Extract the main preview URL: /[locale/]preview/<slug>/ */
    var match=baseUrl.match(/((?:\\/[a-z]{{2}})?\\/preview\\/[\\w-]+\\/)/);
    var mainPage=match?match[1]:baseUrl;
    document.addEventListener('click',function(e){{
      var a=e.target.closest('a[href]');
      if(!a) return;
      var href=a.getAttribute('href');
      if(!href || href==='#' || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) return;
      /* External links — open in new tab */
      if(href.startsWith('http://') || href.startsWith('https://') || href.startsWith('//')){{
        e.preventDefault();
        window.open(href,'_blank','noopener');
        return;
      }}
      /* Internal links that look like raw .html files — redirect to main page */
      if(href.match(/\\.html?(\\?|#|$)/i)){{
        e.preventDefault();
        window.location.href=mainPage;
        return;
      }}
    }});
  }})();

  /* ── SCROLL PROGRESS BAR ── */
  (function(){{
    var bar=document.createElement('div');
    bar.className='sg-scroll-progress';
    bar.style.cssText='position:fixed;top:0;left:0;height:3px;width:0%;z-index:2147483000;pointer-events:none;';
    document.body.appendChild(bar);
    function update(){{
      var h=document.documentElement.scrollHeight-window.innerHeight;
      if(h>0)bar.style.width=(window.pageYOffset/h*100)+'%';
    }}
    window.addEventListener('scroll',update,{{passive:true}});
    update();
  }})();

  /* ── BACK TO TOP BUTTON ── */
  (function(){{
    var btn=document.createElement('button');
    btn.className='sg-back-to-top';
    btn.setAttribute('aria-label','Back to top');
    btn.innerHTML='<svg viewBox="0 0 24 24"><polyline points="18 15 12 9 6 15"/></svg>';
    document.body.appendChild(btn);
    btn.addEventListener('click',function(){{
      window.scrollTo({{top:0,behavior:'smooth'}});
    }});
    function toggle(){{
      if(window.pageYOffset>400)btn.classList.add('visible');
      else btn.classList.remove('visible');
    }}
    window.addEventListener('scroll',toggle,{{passive:true}});
    toggle();
  }})();

  /* ── COUNTER ANIMATION ── */
  (function(){{
    if(typeof IntersectionObserver==='undefined')return;
    var counterSels=[
      '.counter','.count','.number','[class*="counter"] span',
      '.funfact .number','.fun-factor .number','.timer',
      '[data-count]','[data-counter]','[class*="count-"]'
    ];
    var animated=new Set();
    function animateNumber(el){{
      if(animated.has(el))return;
      animated.add(el);
      /* Only animate LEAF elements (no children), not containers */
      if(el.children.length>0)return;
      var text=el.textContent.trim();
      /* Skip if too long (it's a sentence, not a number) */
      if(text.length>20)return;
      var match=text.match(/^([^\\d]*)(\\d[\\d,.]*)([^\\d]*)$/);
      if(!match)return;
      var prefix=match[1];
      var raw=match[2];
      var suffix=match[3];
      var target=parseFloat(raw.replace(/,/g,''));
      if(isNaN(target)||target===0||target>999999)return;
      var hasComma=raw.indexOf(',')!==-1;
      var decimals=(raw.indexOf('.')!==-1)?raw.split('.')[1].length:0;
      var start=0;
      var duration=1800;
      var startTime=null;
      function step(ts){{
        if(!startTime)startTime=ts;
        var p=Math.min((ts-startTime)/duration,1);
        var ease=1-Math.pow(1-p,4);
        var val=start+(target-start)*ease;
        if(isNaN(val)){{ el.textContent=prefix+raw+suffix; return; }}
        var formatted=decimals?val.toFixed(decimals):Math.floor(val).toString();
        if(hasComma)formatted=parseInt(formatted).toLocaleString();
        el.textContent=prefix+formatted+suffix;
        if(p<1)requestAnimationFrame(step);
      }}
      requestAnimationFrame(step);
    }}
    var obs=new IntersectionObserver(function(entries){{
      entries.forEach(function(e){{
        if(e.isIntersecting){{animateNumber(e.target);obs.unobserve(e.target);}}
      }});
    }},{{threshold:0.3}});
    function initCounters(){{
      counterSels.forEach(function(sel){{
        try{{document.querySelectorAll(sel).forEach(function(el){{
          if(/\\d/.test(el.textContent))obs.observe(el);
        }});}}catch(e){{}}
      }});
    }}
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initCounters);
    else setTimeout(initCounters,300);
  }})();

  /* ── PARALLAX HERO ── */
  (function(){{
    var heroSels='[style*="background"],section.hero,.hero-wrap,.hero-section,#hero,.banner-area,.main-banner';
    var hero;
    try{{hero=document.querySelector(heroSels);}}catch(e){{return;}}
    if(!hero)return;
    var speed=0.3;
    function onScroll(){{
      var y=window.pageYOffset;
      if(y<hero.offsetHeight*1.5){{
        hero.style.backgroundPositionY=(-y*speed)+'px';
      }}
    }}
    window.addEventListener('scroll',onScroll,{{passive:true}});
  }})();

  /* ── CUSTOM CURSOR (desktop only) ── */
  (function(){{
    if(!window.matchMedia('(pointer:fine)').matches)return;
    var cursor=document.createElement('div');
    cursor.className='sg-cursor';
    document.body.appendChild(cursor);
    var mx=0,my=0,cx=0,cy=0;
    document.addEventListener('mousemove',function(e){{mx=e.clientX;my=e.clientY;}});
    function lerp(){{
      cx+=(mx-cx)*0.15;cy+=(my-cy)*0.15;
      cursor.style.left=cx+'px';cursor.style.top=cy+'px';
      requestAnimationFrame(lerp);
    }}
    lerp();
    /* Hover expand on interactive elements */
    var hovTags='a,button,.btn,.card,.service-box,.portfolio-item,.team-member';
    document.addEventListener('mouseover',function(e){{
      if(e.target.closest(hovTags))cursor.classList.add('sg-cursor-hover');
    }});
    document.addEventListener('mouseout',function(e){{
      if(e.target.closest(hovTags))cursor.classList.remove('sg-cursor-hover');
    }});
  }})();

  /* ── STAGGERED CARD REVEAL ── */
  (function(){{
    if(typeof IntersectionObserver==='undefined')return;
    var cardSels='.row > [class*="col-"]';
    var obs=new IntersectionObserver(function(entries){{
      entries.forEach(function(e){{
        if(e.isIntersecting){{
          var parent=e.target.parentNode;
          var children=parent?parent.querySelectorAll('[class*="col-"]'):[];
          var idx=Array.prototype.indexOf.call(children,e.target);
          e.target.style.transitionDelay=(idx*0.08)+'s';
          e.target.style.opacity='1';
          e.target.style.transform='translateY(0)';
          obs.unobserve(e.target);
        }}
      }});
    }},{{threshold:0.05,rootMargin:'0px 0px -40px 0px'}});
    function init(){{
      try{{
        document.querySelectorAll(cardSels).forEach(function(el){{
          var rect=el.getBoundingClientRect();
          if(rect.top<window.innerHeight)return;
          el.style.opacity='0';
          el.style.transform='translateY(24px)';
          el.style.transition='opacity 0.6s ease, transform 0.6s ease';
          obs.observe(el);
        }});
      }}catch(e){{}}
    }}
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){{setTimeout(init,250);}});
    else setTimeout(init,250);
  }})();

  /* ── DARK THEME RUNTIME DETECTION ── */
  (function(){{
    function detectDark(){{
      var bg=window.getComputedStyle(document.body).backgroundColor;
      var m=bg.match(/\\d+/g);
      if(!m||m.length<3)return;
      var r=parseInt(m[0]),g=parseInt(m[1]),b=parseInt(m[2]);
      var lum=(0.299*r+0.587*g+0.114*b)/255;
      if(lum>0.3)return; /* not dark */
      document.body.classList.add('sg-dark-theme');
      /* Inject dark-theme fixes */
      var s=document.createElement('style');
      s.textContent=
        '.sg-dark-theme header,.sg-dark-theme .header,.sg-dark-theme nav.navbar,.sg-dark-theme .navigation{{background:rgba(0,0,0,0.85)!important;border-bottom-color:rgba(255,255,255,0.08)!important}}'+
        '.sg-dark-theme .card,.sg-dark-theme .service-box,.sg-dark-theme .feature-box,.sg-dark-theme .pricing-box,.sg-dark-theme .testimonial,.sg-dark-theme .blog-card{{background:rgba(255,255,255,0.05)!important;border-color:rgba(255,255,255,0.08)!important}}'+
        '.sg-dark-theme section,.sg-dark-theme .section,.sg-dark-theme div{{color:rgba(255,255,255,0.85)!important}}'+
        '.sg-dark-theme h1,.sg-dark-theme h2,.sg-dark-theme h3,.sg-dark-theme h4,.sg-dark-theme h5,.sg-dark-theme h6{{color:#fff!important}}'+
        '.sg-dark-theme p{{color:rgba(255,255,255,0.7)!important}}'+
        '.sg-dark-theme .contact-area,.sg-dark-theme .contact-section,.sg-dark-theme #contact{{background:rgba(0,0,0,0.3)!important}}'+
        '.sg-dark-theme .dropdown-menu{{background:rgba(20,20,30,0.97)!important;border-color:rgba(255,255,255,0.1)!important}}'+
        '.sg-dark-theme a:not(.btn):not(.button){{color:var(--sg-accent-glow)!important}}';
      document.head.appendChild(s);
    }}
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',detectDark);
    else detectDark();
  }})();

  /* ── FIX NaN COUNTERS ── */
  /* Template counter plugins sometimes produce NaN — fix them */
  (function(){{
    function fixNaN(){{
      document.querySelectorAll('.counter, .count, .number, .timer, [class*="counter"] h2, [class*="counter"] h3, [class*="counter"] h4, [class*="counter"] span').forEach(function(el){{
        if(el.children.length===0 && el.textContent.trim()==='NaN'){{
          /* Try data attributes first */
          var val=el.getAttribute('data-count')||el.getAttribute('data-number')||el.getAttribute('data-val')||el.getAttribute('data-target');
          if(val){{ el.textContent=val; return; }}
          /* Default fallback values based on position */
          var parent=el.closest('[class*="counter"]')||el.parentElement;
          var siblings=parent?parent.parentElement.querySelectorAll('.counter, .count, .number'):[];
          var idx=Array.prototype.indexOf.call(siblings,el);
          var defaults=['2450','1830','960','450','120'];
          el.textContent=defaults[idx%defaults.length];
        }}
      }});
    }}
    /* Run multiple times to catch NaN produced by late-loading counter plugins */
    if(document.readyState==='loading'){{
      document.addEventListener('DOMContentLoaded',function(){{
        setTimeout(fixNaN,500);
        setTimeout(fixNaN,1500);
        setTimeout(fixNaN,3000);
        setTimeout(fixNaN,5000);
      }});
    }} else {{
      setTimeout(fixNaN,500);
      setTimeout(fixNaN,1500);
      setTimeout(fixNaN,3000);
      setTimeout(fixNaN,5000);
    }}
  }})();

  /* ── SMOOTH IMAGE LOADING ── */
  (function(){{
    var imgs=document.querySelectorAll('img[src*="unsplash"]');
    imgs.forEach(function(img){{
      if(img.complete)return;
      img.style.opacity='0';
      img.style.transition='opacity 0.5s ease';
      img.addEventListener('load',function(){{img.style.opacity='1';}});
      img.addEventListener('error',function(){{img.style.opacity='1';}});
    }});
  }})();

}})();
"""
        body.append(script)

    def _hide_empty_sections(self, soup: BeautifulSoup) -> None:
        """Hide sections that are visually empty — video wrappers with no source,
        gallery sections with no images, and intro/heading sections with minimal content.
        These appear as large blank blocks after template transformation."""
        VIDEO_HINTS = ('video', 'gallery', 'search-wrapper')
        body = soup.find('body')
        if not body:
            return
        for el in body.find_all(['section', 'div']):
            cls = ' '.join(el.get('class', []) or []).lower()
            # Only check elements that look like video/gallery/search sections
            if not any(hint in cls for hint in VIDEO_HINTS):
                continue
            # Check if it has meaningful visible content
            text = (el.get_text(strip=True) or '')
            imgs = el.find_all('img')
            visible_imgs = [i for i in imgs if not (i.get('width') == '1' or i.get('height') == '1')]
            iframes = el.find_all('iframe')
            videos = el.find_all('video')
            # If no text, no images, no iframe, no video → hide it
            if len(text) < 15 and not visible_imgs and not iframes and not videos:
                el['style'] = (el.get('style', '') or '') + '; display: none !important;'

    def _inject_premium_content(self, soup: BeautifulSoup) -> None:
        """Identity-preserving upgrade for agency-ironquill.

        Works WITH the existing template DOM. Applies inline styles and
        content changes to existing elements. No structural deletion.
        Preserves the warm Arcwork character (cream + indigo).
        """
        slug = getattr(self.template, 'slug', '')
        if slug != 'agency-ironquill':
            return

        try:
            locale = (get_language() or 'en').split('-')[0]
        except Exception:
            locale = 'en'

        # ── Content: Italian only for now, clean and specific ──
        C = {
            'it': dict(
                h1='Trasformiamo idee in risultati concreti.',
                sub='Strategia, design e comunicazione digitale per aziende ambiziose.',
                cta='Scopri come lavoriamo',
                s1='Strategia', s1p='Analizziamo il tuo mercato e costruiamo un piano che funziona. Niente teoria: solo azioni misurabili.',
                s2='Design', s2p="Creiamo identità visive che parlano. Loghi, interfacce e brand che restano impressi.",
                s3='Comunicazione', s3p='Campagne digitali, contenuti e social media. Portiamo il tuo messaggio dove conta.',
                s1cta='Scopri di più', s2cta='Vedi i progetti', s3cta='Come funziona',
                solutions='I nostri progetti',
                testi_q='\u201CAurea Studio ha trasformato completamente la nostra presenza digitale. Professionali, puntuali e con una visione chiara.\u201D',
                testi_a='\u2014 Marta Luciani, CEO Fonderia Creativa',
                cta_h='Parliamo del tuo prossimo progetto.',
                cta_btn='Contattaci',
                email='hello@aureastudio.it',
                team='Il team', t1='Marco Ferretti', r1='Direzione creativa',
                t2='Sara Moretti', r2='Strategia', t3='Luca Bianchi', r3='Sviluppo',
            ),
        }
        c = C.get(locale, C.get('it'))
        body = soup.find('body')
        if not body:
            return

        # ── 1. HERO: replace text + fix contrast ──
        hero = soup.find(class_=lambda x: x and 'blocks-cover' in str(x))
        if hero:
            h1 = hero.find('h1')
            if h1:
                h1.clear()
                h1.string = c['h1']
                # Force white text with shadow for readability on bright photos
                h1['style'] = (
                    'color: #fff !important; text-shadow: 0 2px 20px rgba(0,0,0,0.5) !important; '
                    'font-size: clamp(2.4rem, 5vw, 3.8rem) !important; font-weight: 700 !important; '
                    'line-height: 1.1 !important; letter-spacing: -0.02em !important; '
                    '-webkit-text-fill-color: #fff !important; background: none !important;'
                )
            p = hero.find('p')
            if p:
                a_in_p = p.find('a')
                if a_in_p:
                    a_in_p.string = c['cta']
                    # Style CTA as a clean white button
                    a_in_p['style'] = (
                        'display: inline-block !important; padding: 14px 36px !important; '
                        'background: #fff !important; color: #111 !important; '
                        'text-decoration: none !important; font-size: 13px !important; '
                        'font-weight: 600 !important; letter-spacing: 1px !important; '
                        'border-radius: 0 !important; box-shadow: none !important; '
                        'background-image: none !important; text-transform: uppercase !important;'
                    )
                else:
                    p.string = c['sub']
                    p['style'] = 'color: rgba(255,255,255,0.85) !important; font-size: 1.05rem !important; max-width: 420px !important;'

            # Add dark overlay on the half-bg child (sits above parent overlay)
            half_bg = hero.find(class_=lambda x: x and 'half-bg' in str(x))
            if half_bg:
                # Create an overlay div and prepend it
                overlay = soup.new_tag('div')
                overlay['style'] = (
                    'position: absolute; inset: 0; background: rgba(0,0,0,0.5); '
                    'z-index: 1; pointer-events: none;'
                )
                half_bg.insert(0, overlay)
                # Ensure content is above overlay
                container = half_bg.find(class_='container')
                if container:
                    container['style'] = (container.get('style', '') or '') + '; position: relative !important; z-index: 2 !important;'

        # ── 2. SERVICES: replace card content in-place ──
        cards = soup.find_all(class_=lambda x: x and 'feature-' in str(x))[:3]
        card_data = [
            (c['s1'], c['s1p'], c.get('s1cta', c['cta'])),
            (c['s2'], c['s2p'], c.get('s2cta', c['cta'])),
            (c['s3'], c['s3p'], c.get('s3cta', c['cta'])),
        ]
        for i, card in enumerate(cards):
            if i >= len(card_data):
                break
            h, p_text, cta_text = card_data[i]
            h2 = card.find('h2')
            if h2:
                h2.clear()
                h2.string = h
            for p_tag in card.find_all('p'):
                txt = (p_tag.get_text(strip=True) or '')
                if len(txt) > 15 and not p_tag.find('a'):
                    p_tag.string = p_text
                    break
            cta_a = card.find('a')
            if cta_a:
                cta_a.string = cta_text

        # ── 3. SOLUTIONS SECTION: replace heading ──
        solutions_sec = soup.find(class_=lambda x: x and 'bg-left-half' in str(x))
        if solutions_sec:
            h2 = solutions_sec.find('h2')
            if h2:
                h2.string = c['solutions']
            # Replace carousel item names with team names
            h3s = solutions_sec.find_all('h3')
            names = [c['t1'], c['t2'], c['t3']]
            for i, h3 in enumerate(h3s):
                h3.string = names[i % len(names)]

        # ── 4. SECTION HEADINGS: replace remaining pool labels ──
        # Find all h2s with pool text and replace with brand content
        pool_replacements = {
            'Testimonianze': 'Cosa dicono di noi',
            'Testimonial': 'Cosa dicono di noi',
            'I nostri lavori': 'Cosa dicono di noi',  # This section is actually testimonials
            'Blog': 'Dal nostro journal',
        }
        for h2 in soup.find_all('h2'):
            txt = h2.get_text(strip=True)
            if txt in pool_replacements:
                h2.string = pool_replacements[txt]

        # ── 5. TESTIMONIALS: replace quote ──
        for bq in soup.find_all('blockquote'):
            p = bq.find('p')
            if p:
                p.string = c['testi_q']
            author = bq.find(class_='author')
            if author:
                author.string = c['testi_a']

        # ── 5. CTA BAND ──
        cta_sec = soup.find(class_=lambda x: x and 'bg-tertiary' in str(x))
        if cta_sec:
            h2 = cta_sec.find('h2')
            if h2:
                h2.string = c['cta_h']
            cta_a = cta_sec.find('a')
            if cta_a:
                cta_a.string = c['cta_btn']
            # Force dark background inline
            cta_sec['style'] = 'background: #1a1a2e !important; background-image: none !important; padding: 96px 40px !important; text-align: center !important;'
            if h2:
                h2['style'] = 'color: #fff !important;'
            if cta_a:
                cta_a['style'] = 'background: #fff !important; color: #111 !important; padding: 16px 40px !important; display: inline-block !important; text-decoration: none !important; font-weight: 600 !important; letter-spacing: 1px !important; font-size: 14px !important; border-radius: 0 !important; box-shadow: none !important; background-image: none !important;'

        # ── 6. FOOTER: brand email + dark bg ──
        footer_el = soup.find(class_=lambda x: x and 'footer' in str(x) and 'site-section' in str(x))
        if footer_el:
            footer_el['style'] = 'background: #0f0f1a !important; background-image: none !important; color: rgba(255,255,255,0.7) !important; padding: 56px 48px 32px !important;'
        for a in soup.find_all('a'):
            if 'mydomain.com' in (a.get_text(strip=True) or ''):
                a.string = c['email']
                if a.get('href'):
                    a['href'] = f"mailto:{c['email']}"

        # ── 7. BLOG CARDS: replace pool content + hide dates ──
        blog_titles = [
            'Come abbiamo ripensato il brand Fonderia Creativa',
            'Il design che converte: tre lezioni dal campo',
            'Perché la strategia viene prima del design',
        ]
        blog_descs = [
            'Un rebranding completo in 8 settimane. Dall\'analisi alla consegna, ecco come abbiamo lavorato.',
            'Tre progetti, tre approcci diversi. Cosa abbiamo imparato sulla relazione tra estetica e risultati.',
            'Il design senza strategia è decorazione. Ecco il nostro processo in tre fasi.',
        ]
        blog_cards = soup.find_all(class_='post-entry-1')
        for i, card in enumerate(blog_cards):
            if i >= len(blog_titles):
                break
            h2 = card.find('h2')
            if h2:
                # Clear completely then set — avoids concatenation with pool text
                h2.clear()
                h2.string = blog_titles[i]
            for p_tag in card.find_all('p'):
                txt = p_tag.get_text(strip=True)
                if len(txt) > 15:
                    p_tag.string = blog_descs[i]
                    break
        # Hide date metadata
        for span in soup.find_all('span', class_='meta'):
            span['style'] = 'display:none!important'

        # ── 8. EMPTY LAST SECTION: hide ──
        site_sections = soup.find_all(class_='site-section')
        if site_sections:
            last = site_sections[-1]
            if 'footer' not in ' '.join(last.get('class', [])):
                txt = (last.get_text(strip=True) or '')
                if len(txt) < 20:
                    last['style'] = 'display:none!important'

        # ── 9. REMOVE TYPED.JS ──
        for script in soup.find_all('script'):
            src = script.get('src', '') or ''
            text = script.string or ''
            if 'typed.js' in src or 'typed.min.js' in src:
                script.decompose()
            elif 'new Typed(' in text:
                script.decompose()

    def _inject_scroll_animations(self, soup: BeautifulSoup) -> None:
        """Inject a lightweight IntersectionObserver-based scroll animation system.

        Adds smooth fade-in / slide-up animations to sections, cards, headings,
        and other content blocks as they enter the viewport. This transforms
        static templates into dynamic, premium-feeling experiences.

        Uses CSS classes (sg-reveal) defined in _inject_differentiation_layer.
        """
        body = soup.find('body')
        if not body:
            return

        script = soup.new_tag('script')
        script.string = """
(function(){
  'use strict';

  /* ── NAVBAR SCROLL EFFECT ── */
  (function(){
    var hdr = document.querySelector('header, .header, nav.navbar, .navigation, .navbar-area, .header-area, .site-header');
    if(!hdr) return;
    var scrolled = false;
    function onScroll(){
      var y = window.pageYOffset || document.documentElement.scrollTop;
      if(y > 60 && !scrolled){
        scrolled = true;
        hdr.classList.add('sg-scrolled');
      } else if(y <= 60 && scrolled){
        scrolled = false;
        hdr.classList.remove('sg-scrolled');
      }
    }
    window.addEventListener('scroll', onScroll, {passive:true});
    onScroll();
  })();

  /* ── SCROLL REVEAL ANIMATIONS ── */
  if(typeof IntersectionObserver==='undefined')return;

  var SELECTORS = [
    'section > .container',
    '.card', '.service-box', '.team-member', '.project-item',
    '.blog-post', '.feature-box', '.pricing-box', '.pricing-table',
    '.testimonial', '.testimonial-item', '.single-service',
    '.single-feature', '.portfolio-item', '.work-item',
    '.blog-card', '.news-item', '.event-item', '.course-card',
    'section h2', 'section h1', '.section-title',
    'section > .container > .row > [class*="col-"]',
  ];

  var observer = new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if(entry.isIntersecting){
        var el = entry.target;
        el.classList.add('sg-reveal');
        var parent = el.parentNode;
        if(parent){
          var siblings = parent.querySelectorAll('.sg-reveal-pending');
          var idx = Array.prototype.indexOf.call(siblings, el);
          if(idx > 0 && idx < 8){
            el.classList.add('sg-reveal-delay-' + Math.min(idx, 4));
          }
        }
        observer.unobserve(el);
      }
    });
  }, {
    threshold: 0.08,
    rootMargin: '0px 0px -60px 0px'
  });

  function init(){
    var pending = [];
    SELECTORS.forEach(function(sel){
      try{
        document.querySelectorAll(sel).forEach(function(el){
          var rect = el.getBoundingClientRect();
          if(rect.top < window.innerHeight){
            return; // Already in viewport — don't animate
          }
          el.style.opacity = '0';
          el.style.transform = 'translateY(24px)';
          el.style.transition = 'opacity 0.7s ease, transform 0.7s ease';
          el.classList.add('sg-reveal-pending');
          observer.observe(el);
          pending.push(el);
        });
      }catch(e){}
    });

    // SAFETY: force-reveal all pending after 3s (fallback if observer doesn't fire)
    setTimeout(function(){
      pending.forEach(function(el){
        if(el.style.opacity === '0'){
          el.style.opacity = '1';
          el.style.transform = 'translateY(0)';
        }
      });
    }, 3000);
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded', function(){setTimeout(init, 200);});
  } else {
    setTimeout(init, 200);
  }
})();
"""
        body.append(script)

    def _neutralize_google_maps(self, soup: BeautifulSoup) -> None:
        """Remove/neutralize Google Maps in preview mode.

        Maps can't work without an API key and the map div is usually on a
        contact page not being previewed. We:
        1) Remove the Maps API <script>
        2) Neutralize inline google.maps init code
        3) ALWAYS inject a no-op stub for google.maps so external JS files
           (like google-map.js) that reference google.maps don't crash.
        """
        found_maps = False

        # 1) Remove Maps API script tags
        for script in list(soup.find_all('script')):
            src = _safe_get_attr(script, 'src') or ''
            if not isinstance(src, str):
                continue
            if 'maps.googleapis.com' in src or 'maps.google.com' in src:
                script.decompose()
                found_maps = True
            # Detect external google-map*.js files
            elif 'google-map' in src.lower() or 'google_map' in src.lower():
                found_maps = True

        # 2) Remove external GMaps wrapper libraries (gmaps.js, google-map.js etc)
        for script in list(soup.find_all('script')):
            src = _safe_get_attr(script, 'src') or ''
            if isinstance(src, str) and ('gmaps' in src.lower() or 'gmap' in src.lower()):
                script.decompose()
                found_maps = True

        # 3) Neutralize inline google.maps / initMap / GMaps code
        for script in list(soup.find_all('script')):
            text = script.string if script.string and isinstance(script.string, str) else ''
            if 'google.maps' in text or 'initMap' in text or 'new google' in text or 'GMaps' in text or 'new Map(' in text:
                script.string = '/* Google Maps neutralized in preview mode */'
                found_maps = True

        # 3) Detect map containers in HTML (div#map, div.map, etc.)
        if not found_maps:
            for div in soup.find_all(['div', 'section']):
                div_id = _safe_get_attr(div, 'id') or ''
                div_class = ' '.join(_safe_get_attr(div, 'class') or []) if isinstance(_safe_get_attr(div, 'class'), list) else str(_safe_get_attr(div, 'class') or '')
                if 'map' in div_id.lower() or 'googlemap' in div_class.lower().replace('-', '').replace('_', ''):
                    found_maps = True
                    break

        # 4) Always inject the google.maps stub when maps are detected
        if found_maps:
            head = soup.find('head')
            if head:
                stub = soup.new_tag('script')
                stub.string = (
                    'window.google=window.google||{};'
                    'google.maps={Map:function(){return{setCenter:function(){},setZoom:function(){},panTo:function(){}}},Geocoder:function(){return{geocode:function(){}}},LatLng:function(){},Marker:function(){return{setMap:function(){}}},InfoWindow:function(){return{open:function(){},close:function(){}}},event:{addDomListener:function(){},addListener:function(){},addListenerOnce:function(){},trigger:function(){}},OverlayView:function(){},MapTypeId:{ROADMAP:"roadmap",SATELLITE:"satellite",HYBRID:"hybrid",TERRAIN:"terrain"},ControlPosition:{TOP_RIGHT:0},ZoomControlStyle:{SMALL:0},MapTypeControlStyle:{DROPDOWN_MENU:0}};'
                    'function initMap(){}'
                    'window.GMaps=window.GMaps||function(){return{addMarker:function(){},setCenter:function(){},addLayer:function(){}}};'
                )
                # Insert at the START of head so it's available before any script
                if head.contents:
                    head.contents[0].insert_before(stub)
                else:
                    head.append(stub)

    def _inject_plugin_fallbacks(self, soup: BeautifulSoup) -> None:
        """Inject CDN fallbacks for commonly missing JS plugins.

        Some templates reference plugins in their inline code but the plugin
        JS file was never included in the template source. Instead of 404,
        we inject a CDN version as a safety net. This only adds the script
        if the plugin is NOT already loaded (checked via $.fn.X).
        """
        body = soup.find('body')
        if not body:
            return

        # STEP 0: Ensure jQuery is available. Some template sources reference
        # jQuery but the .js file was never included in the ZIP. We check if
        # the jQuery file exists on disk; if not, replace the broken <script>
        # tag with a CDN version.
        try:
            from pathlib import Path
            tmpl_root = Path(settings.TEMPLATE_SOURCE_DIR) / self.template.source_dir
            for script in soup.find_all('script', src=True):
                src = _safe_get_attr(script, 'src') or ''
                if not isinstance(src, str):
                    continue
                fname = src.split('/')[-1].split('?')[0].lower()
                # Only match the MAIN jQuery library (jquery.min.js, jquery-X.X.X.min.js)
                # NOT jQuery plugins like jquery.stellar.min.js, jquery.easing.min.js, etc.
                import re as _re
                is_main_jquery = bool(_re.match(r'^jquery[\-.]?([\d.]+\.)?min\.js$|^jquery[\-.]?([\d.]+\.)?js$', fname))
                if is_main_jquery:
                    # Check if this file exists on disk
                    local_exists = False
                    for p in tmpl_root.rglob('*'):
                        if p.name.lower() == fname and p.is_file() and p.stat().st_size > 1000:
                            local_exists = True
                            break
                    if not local_exists:
                        # Replace with CDN version
                        script['src'] = 'https://cdn.jsdelivr.net/npm/jquery@1.12.4/dist/jquery.min.js'
                        break  # only fix the first/main jQuery
        except Exception:
            pass

        # Map of plugin name → (jQuery check, CDN URL)
        FALLBACKS = {
            'select2': (
                '$.fn.select2',
                'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',
                'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
            ),
            'slick': (
                '$.fn.slick',
                'https://cdn.jsdelivr.net/npm/slick-carousel@1.8.1/slick/slick.min.js',
                'https://cdn.jsdelivr.net/npm/slick-carousel@1.8.1/slick/slick.css',
            ),
            'magnificPopup': (
                '$.fn.magnificPopup',
                'https://cdn.jsdelivr.net/npm/magnific-popup@1.1.0/dist/jquery.magnific-popup.min.js',
                'https://cdn.jsdelivr.net/npm/magnific-popup@1.1.0/dist/magnific-popup.css',
            ),
            'owlCarousel': (
                '$.fn.owlCarousel',
                'https://cdn.jsdelivr.net/npm/owl.carousel@2.3.4/dist/owl.carousel.min.js',
                'https://cdn.jsdelivr.net/npm/owl.carousel@2.3.4/dist/assets/owl.carousel.min.css',
            ),
            'niceSelect': (
                '$.fn.niceSelect',
                'https://cdn.jsdelivr.net/npm/jquery-nice-select@1.1.0/js/jquery.nice-select.min.js',
                None,
            ),
            'counterUp': (
                '$.fn.counterUp',
                'https://cdn.jsdelivr.net/npm/counterup2@2.0.0/dist/index.min.js',
                None,
            ),
            'datepicker': (
                '$.fn.datepicker',
                'https://cdn.jsdelivr.net/npm/bootstrap-datepicker@1.10.0/dist/js/bootstrap-datepicker.min.js',
                'https://cdn.jsdelivr.net/npm/bootstrap-datepicker@1.10.0/dist/css/bootstrap-datepicker.min.css',
            ),
            'stellar': (
                '$.fn.stellar',
                'https://cdn.jsdelivr.net/npm/jquery.stellar@0.6.2/jquery.stellar.min.js',
                None,
            ),
            'timepicker': (
                '$.fn.timepicker',
                'https://cdn.jsdelivr.net/npm/jquery-timepicker@1.3.3/jquery.timepicker.min.js',
                None,
            ),
        }

        # Check which plugins are referenced in the template's HTML code
        all_text = str(soup)

        # Also check external JS files on disk for plugin references
        try:
            from pathlib import Path
            root = Path(settings.TEMPLATE_SOURCE_DIR) / self.template.source_dir
            external_js_text = ''
            for js_file in root.rglob('*.js'):
                if js_file.stat().st_size < 500000:  # skip huge bundles
                    try:
                        external_js_text += js_file.read_text(encoding='utf-8', errors='ignore')
                    except Exception:
                        pass
        except Exception:
            external_js_text = ''

        combined_text = all_text + external_js_text
        needed = []
        for name, (check, js_url, css_url) in FALLBACKS.items():
            # Only inject if the plugin is used somewhere (HTML or external JS)
            if f'.{name}(' in combined_text or f'"{name}"' in combined_text:
                needed.append((name, check, js_url, css_url))

        if not needed:
            return

        # FIRST: check if the plugin JS file exists locally on disk but isn't
        # referenced in the HTML. If so, inject a <script> tag for the LOCAL
        # file rather than the CDN — preserves version compatibility.
        try:
            from pathlib import Path
            tmpl_root = Path(settings.TEMPLATE_SOURCE_DIR) / self.template.source_dir
            asset_base_url = self.asset_base_url()
            html_scripts = set()
            for s in soup.find_all('script', src=True):
                src = (_safe_get_attr(s, 'src') or '').lower()
                html_scripts.add(src.split('/')[-1] if '/' in src else src)

            # Map plugin names to common filenames on disk
            PLUGIN_FILES = {
                'select2': ['select2.min.js', 'select2.js'],
                'slick': ['slick.min.js', 'slick.js'],
                'magnificPopup': ['jquery.magnific-popup.min.js', 'jquery.magnific-popup.js'],
                'owlCarousel': ['owl.carousel.min.js', 'owl.carousel.js'],
                'niceSelect': ['jquery.nice-select.min.js', 'jquery.nice-select.js', 'nice-select.min.js'],
                'counterUp': ['jquery.counterup.min.js', 'jquery.counterup.js', 'counterup.min.js'],
                'datepicker': ['bootstrap-datepicker.min.js', 'bootstrap-datepicker.js'],
                'stellar': ['jquery.stellar.min.js', 'jquery.stellar.js'],
                'timepicker': ['jquery.timepicker.min.js', 'jquery.timepicker.js', 'timepicker.min.js'],
            }

            locally_fixed = set()
            for name, check, js_url, css_url in needed:
                for fname in PLUGIN_FILES.get(name, []):
                    if fname.lower() in html_scripts:
                        locally_fixed.add(name)
                        break
                    # Search on disk
                    for p in tmpl_root.rglob(fname):
                        # File exists on disk — inject a local <script> tag
                        rel = str(p.relative_to(tmpl_root)).replace('\\', '/')
                        local_url = asset_base_url + rel
                        # Find the custom.js or main.js to insert before
                        main_script = None
                        for s in soup.find_all('script', src=True):
                            src_lower = (_safe_get_attr(s, 'src') or '').lower()
                            if any(k in src_lower for k in ['custom', 'main', 'script', 'app']):
                                main_script = s
                                break
                        js_tag = soup.new_tag('script', src=local_url)
                        if main_script:
                            main_script.insert_before(js_tag)
                        else:
                            body.append(js_tag)
                        locally_fixed.add(name)
                        break

            # Remove locally-fixed plugins from needed list
            needed = [(n, c, j, css) for n, c, j, css in needed if n not in locally_fixed]
        except Exception:
            pass

        if not needed:
            return

        # Strategy: inject CDN <script> tags right BEFORE the first inline
        # script that initializes the plugin. This ensures the plugin is
        # available synchronously when the init code runs.
        # Also inject CSS <link> in <head>.
        head = soup.find('head')
        for name, check, js_url, css_url in needed:
            # 1) Inject CSS in head
            if css_url and head:
                css_tag = soup.new_tag('link', rel='stylesheet', href=css_url)
                head.append(css_tag)

            # 2) Find the first inline script that references this plugin
            target_script = None
            for script in soup.find_all('script'):
                if not script.get('src') and script.string:
                    if f'.{name}(' in script.string:
                        target_script = script
                        break

            # 3) Inject the CDN script RIGHT BEFORE the init script
            js_tag = soup.new_tag('script', src=js_url)
            if target_script:
                target_script.insert_before(js_tag)
            else:
                body.append(js_tag)

        # STEP 3: Inject jQuery UI datepicker locale for non-EN
        try:
            locale = (get_language() or 'en').split('-')[0]
        except Exception:
            locale = 'en'
        if locale != 'en' and body:
            # Check if datepicker or jQuery UI is used
            has_datepicker = any(
                'datepicker' in (_safe_get_attr(s, 'src') or '').lower()
                or 'jquery-ui' in (_safe_get_attr(s, 'src') or '').lower()
                or 'jquery.ui' in (_safe_get_attr(s, 'src') or '').lower()
                for s in soup.find_all('script', src=True)
            )
            if has_datepicker:
                locale_script = soup.new_tag('script',
                    src=f'https://cdn.jsdelivr.net/npm/jquery-ui-dist@1.13.2/ui/i18n/datepicker-{locale}.min.js')
                body.append(locale_script)
                # Also inject a small script to set the locale as default
                init = soup.new_tag('script')
                init.string = f'try{{$.datepicker.setDefaults($.datepicker.regional["{locale}"])}}catch(e){{}}'
                body.append(init)

        # STEP 4: Fix jQuery UI icons sprite 404 — inject CDN CSS for jQuery UI theme
        if body:
            has_ui = any(
                'jquery-ui' in (_safe_get_attr(s, 'src') or '').lower()
                or 'jquery.ui' in (_safe_get_attr(s, 'src') or '').lower()
                for s in soup.find_all(['script', 'link'], src=True)
            ) or any(
                'jquery-ui' in (_safe_get_attr(l, 'href') or '').lower()
                for l in soup.find_all('link', href=True)
            )
            if has_ui:
                head = soup.find('head')
                if head:
                    # Add CDN fallback for jQuery UI theme CSS (includes icon sprites)
                    ui_css = soup.new_tag('link', rel='stylesheet',
                        href='https://cdn.jsdelivr.net/npm/jquery-ui-dist@1.13.2/jquery-ui.min.css')
                    head.append(ui_css)


# ----------------------------------------------------------------------
# Asset serving
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# CDN REDIRECT MAP — DISABLED
#
# The CDN redirect was causing version-mismatch issues with plugins like
# magnific-popup: templates load a specific jQuery version and expect the
# plugin to attach to THAT instance. When we served a different CDN
# version, plugin load order / API differed, leaving `$().magnificPopup`
# undefined.
#
# All library files remain on local disk — they are served directly
# through /assets/<slug>/<path>. This guarantees byte-for-byte
# compatibility with the original template expectations.
# ----------------------------------------------------------------------
CDN_LIBRARY_MAP = {}


def _cdn_redirect_for(url_path: str):
    """CDN redirect disabled — always returns None (serve locally)."""
    return None


def _safe_get_attr(tag, attr, default=None):
    """Safely get an attribute from a BS4 tag. Some tags (doctype, comments,
    processing instructions) have attrs=None and .get() crashes."""
    try:
        attrs = getattr(tag, 'attrs', None)
        if not attrs:
            return default
        return attrs.get(attr, default)
    except Exception:
        return default


def serve_template_asset(template: TemplateItem, asset_path: str) -> HttpResponse:
    """Serve a file from the template source directory with MIME detection.

    Prevents path traversal by resolving and verifying the path stays within
    the template root. URL-decodes the incoming path.
    """
    from urllib.parse import unquote
    asset_path = unquote(asset_path)
    root = (Path(settings.TEMPLATE_SOURCE_DIR) / template.source_dir).resolve()
    target = (root / asset_path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise Http404("Invalid path")
    if not target.exists() or not target.is_file():
        raise Http404("Asset not found")
    mime, _ = mimetypes.guess_type(str(target))
    return FileResponse(open(target, 'rb'), content_type=mime or 'application/octet-stream')
