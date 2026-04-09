"""
Core views — homepage, institutional pages, FAQ.
"""
from django.views.generic import TemplateView
from django.utils.translation import get_language

from catalog.models import Category, TemplateItem
from customizer.dynamic_content import (
    get_localized_faqs, get_localized_testimonials, get_categorized_faqs,
)
from .models import SiteConfig, FAQ, Testimonial


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['config'] = SiteConfig.get_solo()
        ctx['featured_categories'] = Category.objects.filter(
            is_active=True, is_featured=True
        ).order_by('order')[:8]
        ctx['all_categories'] = Category.objects.filter(is_active=True).order_by('order')
        ctx['featured_templates'] = TemplateItem.objects.filter(
            is_active=True, is_featured=True
        ).select_related('category')[:8]
        ctx['new_templates'] = TemplateItem.objects.filter(
            is_active=True, is_new=True
        ).select_related('category')[:8]
        ctx['bestseller_templates'] = TemplateItem.objects.filter(
            is_active=True, is_bestseller=True
        ).select_related('category')[:4]
        ctx['stats'] = {
            'templates': TemplateItem.objects.filter(is_active=True).count() or ctx['config'].stat_templates,
            'categories': Category.objects.filter(is_active=True).count(),
            'customers': ctx['config'].stat_customers,
            'countries': ctx['config'].stat_countries,
            'satisfaction': ctx['config'].stat_satisfaction,
        }
        loc = (get_language() or 'en').split('-')[0]
        ctx['faqs'] = get_localized_faqs(loc)[:8]
        # Localized testimonials replace the DB-stored Testimonial model
        ctx['reviews'] = get_localized_testimonials(loc)
        # Legacy alias kept empty for any leftover references
        ctx['testimonials'] = []
        return ctx


class AboutView(TemplateView):
    template_name = 'core/about.html'


class FAQView(TemplateView):
    template_name = 'core/faq.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        loc = (get_language() or 'en').split('-')[0]
        # Rich categorized FAQ for the dedicated page
        categories, faqs = get_categorized_faqs(loc)
        ctx['faq_categories'] = categories
        ctx['faqs'] = faqs
        # Popular FAQs shown at the top
        ctx['popular_faqs'] = [f for f in faqs if f.get('popular')][:4]
        return ctx


class ContactView(TemplateView):
    template_name = 'core/contact.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['config'] = SiteConfig.get_solo()
        return ctx
