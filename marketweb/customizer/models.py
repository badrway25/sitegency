"""
Customizer models — live demo sessions and user customization data.
"""
import uuid
from django.db import models
from django.conf import settings


class DemoSession(models.Model):
    """A customer-driven demo session for a specific template.

    Stores all the customization data (logo, colors, texts, images, etc.)
    the user enters so the customizer preview can be rebuilt and shared.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey('catalog.TemplateItem', on_delete=models.CASCADE,
                                 related_name='demo_sessions')
    # Identify session — either by auth user or by a session token saved in cookies
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='demo_sessions')
    session_token = models.CharField(max_length=64, blank=True, db_index=True)

    # All customization fields stored as JSON: { field_key: value, ... }
    data = models.JSONField(default=dict, blank=True)

    # Uploaded media references (logo, hero image, team photos, gallery ...)
    uploaded_media = models.JSONField(default=dict, blank=True,
                                      help_text="Map field_key -> media file URL")

    # Optional live color theme override
    primary_color = models.CharField(max_length=20, blank=True)
    secondary_color = models.CharField(max_length=20, blank=True)

    # Lifecycle
    is_completed = models.BooleanField(default=False,
                                       help_text="User has finalized their demo session")
    converted_to_order = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['template', 'session_token']),
        ]

    def __str__(self):
        return f"DemoSession<{self.template.name}> {self.id}"


class CustomizerMediaUpload(models.Model):
    """Media file uploaded during a demo session (logos, hero images, team photos)."""
    session = models.ForeignKey(DemoSession, on_delete=models.CASCADE, related_name='media')
    field_key = models.CharField(max_length=100)
    file = models.ImageField(upload_to='customizer/%Y/%m/')
    original_name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session_id} :: {self.field_key}"
