"""
Template scanner — walks the Templates/ source tree, identifies template directories,
and extracts pages, assets, sections and metadata.

Design goals:
- Zero manual wiring: point at TEMPLATE_SOURCE_DIR and run.
- Filter out demo / element / typography / bootstrap-component pages that must
  never be shown to customers.
- Detect entry page (index.html / home.html / default.html).
- Classify assets (css / js / img / font).
- Provide a normalized dataclass (`ScannedTemplate`) consumed by the importer.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Iterator, Optional


# Pages that are technical/demo/style-guide showcases — never shown to customers.
# These names are compared case-insensitively as substrings of the filename.
BLOCKED_PAGE_KEYWORDS = {
    'elements', 'element', 'typography', 'typo', 'shortcode', 'shortcodes',
    'components', 'component', 'buttons', 'button', 'tables', 'table',
    'forms-demo', 'form-elements', 'form-element', 'ui-elements', 'ui-kit',
    'bootstrap', 'styleguide', 'style-guide', 'demo', 'accordions', 'accordion-demo',
    'tabs-demo', 'alerts', 'modals-demo', 'icons', 'icon-demo', 'progress-bars',
    'pricing-table-demo', 'col-', '404', 'coming-soon', 'maintenance', 'login',
    'signup', 'register', 'reset-password',
}

# Friendly names for common pages
PAGE_NAME_MAP = {
    'index': 'Home',
    'home': 'Home',
    'default': 'Home',
    'about': 'About Us',
    'about-us': 'About Us',
    'services': 'Services',
    'service': 'Services',
    'contact': 'Contact',
    'contact-us': 'Contact',
    'team': 'Our Team',
    'blog': 'Blog',
    'blog-home': 'Blog',
    'blog-single': 'Blog Post',
    'single': 'Blog Post',
    'portfolio': 'Portfolio',
    'gallery': 'Gallery',
    'faq': 'FAQ',
    'pricing': 'Pricing',
    'shop': 'Shop',
    'product': 'Products',
    'menu': 'Menu',
    'rooms': 'Rooms',
    'projects': 'Projects',
    'project': 'Projects',
    'events': 'Events',
    'event': 'Events',
    'cases': 'Case Studies',
    'volunteer': 'Volunteer',
    'cats': 'Cats',
    'dogs': 'Dogs',
    'appointment': 'Book Appointment',
    'booking': 'Book Now',
    'reservation': 'Reservations',
    'testimonials': 'Testimonials',
    'reviews': 'Reviews',
}


@dataclass
class ScannedPage:
    filename: str           # e.g. "about.html"
    rel_path: str           # relative to template root
    slug: str               # e.g. "about"
    display_name: str       # e.g. "About Us"
    is_entry: bool = False
    is_public: bool = True  # whether to show in customer navigation


@dataclass
class ScannedAsset:
    rel_path: str
    asset_type: str   # css|js|img|font|other
    size: int = 0


@dataclass
class ScannedTemplate:
    slug: str                              # derived from directory name
    source_dir: str                        # "Animal/doglife"
    abs_path: Path
    category_name: str
    folder_name: str
    entry_file: str = 'index.html'
    pages: List[ScannedPage] = field(default_factory=list)
    assets: List[ScannedAsset] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        # Will be overridden by a creative name map in the importer
        return self.folder_name.replace('-', ' ').replace('_', ' ').title()


def _classify_asset(path: Path) -> Optional[str]:
    ext = path.suffix.lower()
    if ext == '.css':
        return 'css'
    if ext == '.js':
        return 'js'
    if ext in {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'}:
        return 'img'
    if ext in {'.woff', '.woff2', '.ttf', '.otf', '.eot'}:
        return 'font'
    return None


def _is_blocked_page(filename: str) -> bool:
    """Return True if this HTML file is a demo/technical showcase page."""
    stem = Path(filename).stem.lower()
    # Normalize separators
    normalized = re.sub(r'[_\s]+', '-', stem)
    for kw in BLOCKED_PAGE_KEYWORDS:
        if kw == normalized or normalized.startswith(kw + '-') or normalized.endswith('-' + kw) or f'-{kw}-' in normalized:
            return True
        # Also catch raw substring for "elements", "typography", etc.
        if kw in normalized and len(kw) >= 5:
            return True
    return False


def _friendly_name(slug: str) -> str:
    if slug in PAGE_NAME_MAP:
        return PAGE_NAME_MAP[slug]
    return slug.replace('-', ' ').replace('_', ' ').title()


def _is_template_dir(path: Path) -> bool:
    """A directory is a template if it contains at least one HTML file at top level."""
    if not path.is_dir():
        return False
    if path.name.startswith('.') or path.name.startswith('__'):
        return False
    try:
        for entry in path.iterdir():
            if entry.is_file() and entry.suffix.lower() in {'.html', '.htm'}:
                return True
    except (PermissionError, OSError):
        return False
    return False


def _find_entry_file(path: Path) -> str:
    candidates = ['index.html', 'home.html', 'default.html', 'index.htm']
    for c in candidates:
        if (path / c).exists():
            return c
    # Fallback: first html file
    for entry in sorted(path.iterdir()):
        if entry.is_file() and entry.suffix.lower() in {'.html', '.htm'}:
            return entry.name
    return 'index.html'


class TemplateScanner:
    """Scans a source directory tree and yields ScannedTemplate instances."""

    def __init__(self, source_dir: Path, max_depth: int = 3):
        self.source_dir = Path(source_dir)
        self.max_depth = max_depth

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def scan(self, category_filter: Optional[List[str]] = None) -> Iterator[ScannedTemplate]:
        """Walk the source dir, yielding ScannedTemplates."""
        if not self.source_dir.exists():
            return

        for category_dir in sorted(self.source_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            if category_dir.name.startswith('.') or category_dir.name.startswith('__'):
                continue
            if category_filter and category_dir.name not in category_filter:
                continue

            for template_dir in sorted(category_dir.iterdir()):
                if not _is_template_dir(template_dir):
                    continue
                if template_dir.name.startswith('__'):
                    continue
                try:
                    yield self._scan_template(category_dir.name, template_dir)
                except Exception as e:  # pragma: no cover — defensive
                    print(f"[scanner] skip {template_dir}: {e}")
                    continue

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _scan_template(self, category_name: str, template_dir: Path) -> ScannedTemplate:
        rel = template_dir.relative_to(self.source_dir).as_posix()
        tpl = ScannedTemplate(
            slug=f"{category_name.lower()}-{template_dir.name.lower()}".replace(' ', '-').replace('&', 'and'),
            source_dir=rel,
            abs_path=template_dir,
            category_name=category_name,
            folder_name=template_dir.name,
            entry_file=_find_entry_file(template_dir),
        )

        self._collect_pages(tpl)
        self._collect_assets(tpl)
        self._infer_sections(tpl)
        return tpl

    def _collect_pages(self, tpl: ScannedTemplate) -> None:
        root = tpl.abs_path
        pages: List[ScannedPage] = []
        for entry in sorted(root.iterdir()):
            if not entry.is_file():
                continue
            if entry.suffix.lower() not in {'.html', '.htm'}:
                continue
            filename = entry.name
            slug = Path(filename).stem.lower()
            is_blocked = _is_blocked_page(filename)
            is_entry = filename == tpl.entry_file
            pages.append(ScannedPage(
                filename=filename,
                rel_path=filename,
                slug=slug,
                display_name=_friendly_name(slug),
                is_entry=is_entry,
                is_public=not is_blocked or is_entry,  # entry page is always public
            ))
        # Move entry page to first position
        pages.sort(key=lambda p: (0 if p.is_entry else 1, p.slug))
        tpl.pages = pages

    def _collect_assets(self, tpl: ScannedTemplate) -> None:
        assets: List[ScannedAsset] = []
        for root, dirs, files in os.walk(tpl.abs_path):
            # skip macos junk and scss sources (not served)
            dirs[:] = [d for d in dirs if not d.startswith('__') and not d.startswith('.') and d.lower() != 'scss']
            for f in files:
                p = Path(root) / f
                asset_type = _classify_asset(p)
                if not asset_type:
                    continue
                try:
                    rel = p.relative_to(tpl.abs_path).as_posix()
                    size = p.stat().st_size
                except (ValueError, OSError):
                    continue
                assets.append(ScannedAsset(rel_path=rel, asset_type=asset_type, size=size))
        tpl.assets = assets

    def _infer_sections(self, tpl: ScannedTemplate) -> None:
        """Parse entry page quickly to extract <section id="..."> names."""
        entry = tpl.abs_path / tpl.entry_file
        if not entry.exists():
            return
        try:
            content = entry.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            return
        # Simple regex pass (lightweight, no BS4 dependency here)
        ids = re.findall(r'<section[^>]*\bid="([^"]+)"', content, re.IGNORECASE)
        tpl.sections = list(dict.fromkeys(ids))[:12]  # dedupe, cap at 12
