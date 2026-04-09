"""
Management command: import_templates

Scans TEMPLATE_SOURCE_DIR, imports templates into the catalog, and logs an
ImportRun record with stats.

Usage:
    python manage.py import_templates
    python manage.py import_templates --limit 8
    python manage.py import_templates --reset
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from importer.models import ImportRun
from importer.services import TemplateScanner, TemplateImporter
from catalog.models import (
    Category, TemplateItem, TemplatePage, TemplateAsset,
    TemplateSection, TemplateCustomizationField,
)


class Command(BaseCommand):
    help = "Scan the template source directory and import templates into the catalog."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=10,
                            help='Max templates per category (default 10)')
        parser.add_argument('--reset', action='store_true',
                            help='Wipe catalog before importing')
        parser.add_argument('--verbosity-level', type=int, default=1)

    def handle(self, *args, **options):
        source_dir = settings.TEMPLATE_SOURCE_DIR
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Importing templates from: {source_dir}"
        ))

        if options['reset']:
            self.stdout.write(self.style.WARNING("Resetting catalog..."))
            TemplateCustomizationField.objects.all().delete()
            TemplateSection.objects.all().delete()
            TemplateAsset.objects.all().delete()
            TemplatePage.objects.all().delete()
            TemplateItem.objects.all().delete()
            Category.objects.all().delete()

        run = ImportRun.objects.create(status='running')

        try:
            scanner = TemplateScanner(source_dir)
            importer = TemplateImporter(scanner, verbosity=options['verbosity_level'])
            stats = importer.run(limit_per_category=options['limit'])
        except Exception as e:
            run.status = 'failed'
            run.errors = str(e)
            run.finished_at = timezone.now()
            run.save()
            self.stdout.write(self.style.ERROR(f"Import failed: {e}"))
            raise

        run.status = 'success'
        run.templates_scanned = stats['scanned']
        run.templates_imported = stats['imported'] + stats['updated']
        run.templates_skipped = stats['skipped']
        run.finished_at = timezone.now()
        run.log = (
            f"scanned={stats['scanned']} imported={stats['imported']} "
            f"updated={stats['updated']} skipped={stats['skipped']} "
            f"categories_created={stats['categories_created']}"
        )
        run.save()

        self.stdout.write(self.style.SUCCESS("✔ Import complete"))
        self.stdout.write(f"  scanned    : {stats['scanned']}")
        self.stdout.write(f"  imported   : {stats['imported']}")
        self.stdout.write(f"  updated    : {stats['updated']}")
        self.stdout.write(f"  skipped    : {stats['skipped']}")
        self.stdout.write(f"  categories : {Category.objects.count()}")
        self.stdout.write(f"  templates  : {TemplateItem.objects.count()}")
