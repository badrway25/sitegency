from django.contrib import admin
from .models import SiteConfig, FAQ, Testimonial


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Brand', {'fields': ('brand_name', 'brand_tagline')}),
        ('Hero', {'fields': ('hero_title', 'hero_subtitle')}),
        ('Stats', {'fields': ('stat_templates', 'stat_customers', 'stat_countries', 'stat_satisfaction')}),
        ('Support', {'fields': ('support_email', 'support_phone')}),
    )

    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_published']
    list_editable = ['order', 'is_published']
    list_filter = ['category', 'is_published']
    search_fields = ['question', 'answer']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'author_company', 'rating', 'is_featured', 'order']
    list_editable = ['is_featured', 'order']
    list_filter = ['is_featured', 'rating']
