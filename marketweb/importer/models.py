"""
Importer models — track import runs and per-template import status.
"""
from django.db import models


class ImportRun(models.Model):
    STATUS = [
        ('running', 'Running'),
        ('success', 'Success'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
    ]
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='running')
    templates_scanned = models.PositiveIntegerField(default=0)
    templates_imported = models.PositiveIntegerField(default=0)
    templates_skipped = models.PositiveIntegerField(default=0)
    errors = models.TextField(blank=True)
    log = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"ImportRun {self.started_at:%Y-%m-%d %H:%M} — {self.status}"
