from django.contrib import admin
from .models import DemoSession, CustomizerMediaUpload


class MediaInline(admin.TabularInline):
    model = CustomizerMediaUpload
    extra = 0
    readonly_fields = ['file', 'field_key', 'original_name', 'uploaded_at']


@admin.register(DemoSession)
class DemoSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'template', 'user', 'is_completed',
                    'converted_to_order', 'created_at', 'updated_at']
    list_filter = ['is_completed', 'converted_to_order', 'template__category']
    search_fields = ['template__name', 'user__email', 'session_token']
    readonly_fields = ['id', 'session_token', 'created_at', 'updated_at']
    inlines = [MediaInline]


@admin.register(CustomizerMediaUpload)
class CustomizerMediaUploadAdmin(admin.ModelAdmin):
    list_display = ['session', 'field_key', 'file', 'uploaded_at']
