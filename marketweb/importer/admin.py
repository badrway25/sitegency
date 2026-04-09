from django.contrib import admin
from .models import ImportRun


@admin.register(ImportRun)
class ImportRunAdmin(admin.ModelAdmin):
    list_display = ['started_at', 'status', 'templates_scanned',
                    'templates_imported', 'templates_skipped']
    list_filter = ['status']
    readonly_fields = ['started_at', 'finished_at', 'templates_scanned',
                       'templates_imported', 'templates_skipped', 'log', 'errors']
    ordering = ['-started_at']
