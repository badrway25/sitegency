"""
Template importer — consumes ScannedTemplate objects and writes Category /
TemplateItem / TemplatePage / TemplateAsset / TemplateSection /
TemplateCustomizationField records.

The importer is idempotent: running it multiple times updates existing
records in-place rather than duplicating them.
"""
from __future__ import annotations

import random
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from django.db import transaction
from django.utils.text import slugify

from catalog.models import (
    Category, TemplateItem, TemplatePage, TemplateAsset,
    TemplateSection, TemplateCustomizationField,
)
from .scanner import ScannedTemplate, TemplateScanner
from .branding import (
    CATEGORY_META, CREATIVE_NAMES, TEMPLATE_TAGLINES,
    DEFAULT_CUSTOM_FIELDS, CATEGORY_ALIAS,
)


class TemplateImporter:
    """Imports scanned templates into the Django DB."""

    def __init__(self, scanner: TemplateScanner, verbosity: int = 1):
        self.scanner = scanner
        self.verbosity = verbosity
        self.stats = {
            'scanned': 0,
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'categories_created': 0,
        }
        self._name_pool: Dict[str, List[str]] = {}
        self._used_names: set = set()

    def log(self, msg: str) -> None:
        if self.verbosity >= 1:
            print(f"[importer] {msg}")

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------
    @transaction.atomic
    def run(self, limit_per_category: int = 10) -> Dict:
        category_counts: Dict[str, int] = {}

        for tpl in self.scanner.scan():
            self.stats['scanned'] += 1
            category = self._resolve_category(tpl.category_name)
            if not category:
                self.stats['skipped'] += 1
                continue

            # Cap number of templates per category for a tight, premium catalog
            if category_counts.get(category.slug, 0) >= limit_per_category:
                self.stats['skipped'] += 1
                continue

            # Need at least one real HTML page to be useful
            if not tpl.pages:
                self.stats['skipped'] += 1
                continue

            item, created = self._upsert_template(category, tpl)
            self._upsert_pages(item, tpl)
            self._upsert_assets(item, tpl)
            self._upsert_sections(item, tpl)
            self._upsert_custom_fields(item)

            category_counts[category.slug] = category_counts.get(category.slug, 0) + 1
            if created:
                self.stats['imported'] += 1
                self.log(f"+ {category.name} :: {item.name}")
            else:
                self.stats['updated'] += 1
        return self.stats

    # ------------------------------------------------------------------
    # Category resolution
    # ------------------------------------------------------------------
    def _resolve_category(self, raw_name: str) -> Category | None:
        # Normalize common aliases (Healt-Fitness -> Fitness, etc.)
        friendly = CATEGORY_ALIAS.get(raw_name, raw_name)
        meta = CATEGORY_META.get(friendly)
        if not meta:
            # Unknown category → skip (we want a curated set only)
            return None
        cat, created = Category.objects.get_or_create(
            slug=slugify(friendly),
            defaults={
                'name': friendly,
                'tagline': meta['tagline'],
                'description': meta['description'],
                'icon_class': meta['icon'],
                'accent_color': meta['color'],
                'order': meta.get('order', 50),
                'is_active': True,
                'is_featured': meta.get('featured', False),
            },
        )
        if not created:
            # Refresh meta in case it changed
            cat.tagline = meta['tagline']
            cat.description = meta['description']
            cat.icon_class = meta['icon']
            cat.accent_color = meta['color']
            cat.order = meta.get('order', 50)
            cat.is_featured = meta.get('featured', False)
            cat.save(update_fields=['tagline', 'description', 'icon_class',
                                    'accent_color', 'order', 'is_featured'])
        else:
            self.stats['categories_created'] += 1
        return cat

    # ------------------------------------------------------------------
    # Template upsert
    # ------------------------------------------------------------------
    def _pick_creative_name(self, category_slug: str, folder: str) -> str:
        pool = self._name_pool.get(category_slug)
        if pool is None:
            pool = list(CREATIVE_NAMES.get(category_slug, []))
            random.Random(hash(category_slug)).shuffle(pool)
            self._name_pool[category_slug] = pool
        for candidate in pool:
            if candidate not in self._used_names:
                self._used_names.add(candidate)
                pool.remove(candidate)
                return candidate
        # Fallback: synthesize from folder
        fallback = folder.replace('-', ' ').replace('_', ' ').title() + ' Pro'
        self._used_names.add(fallback)
        return fallback

    def _upsert_template(self, category: Category, tpl: ScannedTemplate) -> Tuple[TemplateItem, bool]:
        existing = TemplateItem.objects.filter(source_dir=tpl.source_dir).first()
        if existing:
            name = existing.name
            created = False
        else:
            name = self._pick_creative_name(category.slug, tpl.folder_name)
            created = True

        slug_base = slugify(f"{category.slug}-{name}")
        slug = slug_base
        i = 2
        while TemplateItem.objects.filter(slug=slug).exclude(pk=existing.pk if existing else None).exists():
            slug = f"{slug_base}-{i}"
            i += 1

        tagline = random.Random(hash(slug)).choice(
            TEMPLATE_TAGLINES.get(category.slug, TEMPLATE_TAGLINES['default'])
        )

        # Deterministic pseudo-random pricing for feel of variety
        rng = random.Random(hash(slug))
        price = Decimal(rng.choice([39, 49, 59, 69, 79, 89]))
        original = price + Decimal(rng.choice([20, 30, 40, 50]))

        defaults = dict(
            name=name,
            slug=slug,
            category=category,
            tagline=tagline,
            short_description=tagline,
            description=self._build_description(name, category, tpl),
            price=price,
            original_price=original,
            pricing_tier=rng.choice(['standard', 'premium', 'premium', 'elite']),
            source_dir=tpl.source_dir,
            entry_file=tpl.entry_file,
            preview_color_1=category.accent_color,
            preview_color_2=rng.choice(['#ec4899', '#f59e0b', '#10b981', '#8b5cf6', '#06b6d4']),
            is_featured=rng.random() < 0.25,
            is_new=rng.random() < 0.35,
            is_bestseller=rng.random() < 0.20,
            is_active=True,
            tags=', '.join(rng.sample(
                ['responsive', 'modern', 'premium', 'clean', 'bootstrap5', 'dark-ready',
                 'animated', 'retina', 'seo-friendly', 'fast', 'creative', 'elegant'], 5)),
            technologies='HTML5, CSS3, Bootstrap 5, JavaScript, Sass',
            responsive=True,
            pages_count=len([p for p in tpl.pages if p.is_public]),
            downloads=rng.randint(120, 4800),
            views_count=rng.randint(500, 18000),
            rating=Decimal(str(round(rng.uniform(4.5, 5.0), 2))),
            reviews_count=rng.randint(15, 340),
        )
        if existing:
            for k, v in defaults.items():
                # Don't overwrite the creative name once assigned
                if k == 'name':
                    continue
                setattr(existing, k, v)
            existing.save()
            return existing, False
        item = TemplateItem.objects.create(**defaults)
        return item, True

    def _build_description(self, name: str, category: Category, tpl: ScannedTemplate) -> str:
        return (
            f"{name} is a premium {category.name.lower()} website template crafted by the "
            f"Sitegency studio. Every section is fully customizable — swap logo, colors, text, "
            f"images, services and contact details through our live customizer, preview the "
            f"result in real-time, and publish in minutes. Built on a modern, responsive "
            f"framework with accessibility and performance baked in."
        )

    # ------------------------------------------------------------------
    # Pages / assets / sections / fields
    # ------------------------------------------------------------------
    def _upsert_pages(self, item: TemplateItem, tpl: ScannedTemplate) -> None:
        item.pages.all().delete()
        for order, page in enumerate(tpl.pages):
            TemplatePage.objects.create(
                template=item,
                name=page.display_name,
                slug=page.slug,
                file_path=page.rel_path,
                order=order,
                is_entry=page.is_entry,
                is_public=page.is_public,
            )

    def _upsert_assets(self, item: TemplateItem, tpl: ScannedTemplate) -> None:
        item.assets.all().delete()
        bulk = [
            TemplateAsset(
                template=item,
                asset_type=a.asset_type,
                file_path=a.rel_path,
                file_size=a.size,
            ) for a in tpl.assets
        ]
        TemplateAsset.objects.bulk_create(bulk, batch_size=500)

    def _upsert_sections(self, item: TemplateItem, tpl: ScannedTemplate) -> None:
        item.sections.all().delete()
        # Use scanned sections if present, else synthesize standard set
        section_names = tpl.sections or ['hero', 'about', 'services', 'team',
                                         'portfolio', 'testimonials', 'contact']
        for order, name in enumerate(section_names):
            TemplateSection.objects.create(
                template=item,
                name=name.title().replace('-', ' '),
                section_id=name,
                order=order,
            )

    def _upsert_custom_fields(self, item: TemplateItem) -> None:
        item.custom_fields.all().delete()
        bulk = [
            TemplateCustomizationField(
                template=item,
                field_key=f['key'],
                field_label=f['label'],
                field_type=f['type'],
                placeholder=f.get('placeholder', ''),
                default_value=f.get('default', ''),
                group=f['group'],
                order=order,
                is_required=f.get('required', False),
            )
            for order, f in enumerate(DEFAULT_CUSTOM_FIELDS)
        ]
        TemplateCustomizationField.objects.bulk_create(bulk)
