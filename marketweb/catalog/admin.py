from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, TemplateItem, TemplatePage, TemplateAsset,
    TemplateSection, TemplateCustomizationField,
)


class TemplatePageInline(admin.TabularInline):
    model = TemplatePage
    extra = 0
    fields = ['name', 'slug', 'file_path', 'order', 'is_entry', 'is_public']


class TemplateSectionInline(admin.TabularInline):
    model = TemplateSection
    extra = 0


class TemplateCustomFieldInline(admin.TabularInline):
    model = TemplateCustomizationField
    extra = 0
    fields = ['group', 'order', 'field_key', 'field_label', 'field_type', 'default_value']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'template_count', 'accent_color_swatch',
                    'order', 'is_active', 'is_featured']
    list_filter = ['is_active', 'is_featured']
    list_editable = ['order', 'is_active', 'is_featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='Color')
    def accent_color_swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:24px;height:24px;border-radius:50%;'
            'background:{};border:1px solid #ccc;"></span> <code>{}</code>',
            obj.accent_color, obj.accent_color,
        )


@admin.register(TemplateItem)
class TemplateItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'pricing_tier',
                    'is_featured', 'is_new', 'is_bestseller', 'is_active',
                    'downloads', 'rating']
    list_filter = ['category', 'pricing_tier', 'is_featured', 'is_new',
                   'is_bestseller', 'is_active']
    list_editable = ['price', 'is_featured', 'is_new', 'is_bestseller', 'is_active']
    search_fields = ['name', 'tagline', 'description', 'tags']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['id', 'views_count', 'created_at', 'updated_at']
    inlines = [TemplatePageInline, TemplateSectionInline, TemplateCustomFieldInline]
    actions = ['make_featured', 'make_unfeatured', 'activate', 'deactivate']
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'tagline', 'short_description', 'description'),
        }),
        ('Pricing', {
            'fields': ('price', 'original_price', 'pricing_tier'),
        }),
        ('Source', {
            'fields': ('source_dir', 'entry_file'),
        }),
        ('Display', {
            'fields': ('thumbnail', 'preview_color_1', 'preview_color_2',
                       'tags', 'technologies', 'pages_count'),
        }),
        ('Flags', {
            'fields': ('is_active', 'is_featured', 'is_new', 'is_bestseller', 'responsive'),
        }),
        ('Stats', {
            'fields': ('downloads', 'views_count', 'rating', 'reviews_count'),
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.action(description='Mark as featured')
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description='Remove from featured')
    def make_unfeatured(self, request, queryset):
        queryset.update(is_featured=False)

    @admin.action(description='Activate')
    def activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Deactivate')
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(TemplatePage)
class TemplatePageAdmin(admin.ModelAdmin):
    list_display = ['template', 'name', 'slug', 'is_entry', 'is_public', 'order']
    list_filter = ['is_public', 'is_entry']
    search_fields = ['name', 'template__name']


@admin.register(TemplateAsset)
class TemplateAssetAdmin(admin.ModelAdmin):
    list_display = ['template', 'asset_type', 'file_path', 'file_size']
    list_filter = ['asset_type']
    search_fields = ['file_path', 'template__name']


@admin.register(TemplateCustomizationField)
class TemplateCustomizationFieldAdmin(admin.ModelAdmin):
    list_display = ['template', 'group', 'field_label', 'field_key', 'field_type', 'order']
    list_filter = ['group', 'field_type']
