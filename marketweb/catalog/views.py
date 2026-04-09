"""
Catalog views — categories, template listing, template detail, live preview.
"""
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count

from .models import Category, TemplateItem
from customizer.services import PreviewEngine, serve_template_asset


class CategoryListView(ListView):
    model = Category
    template_name = 'catalog/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(is_active=True).annotate(
            tpl_count=Count('templates', filter=Q(templates__is_active=True))
        ).order_by('order')


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'catalog/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.object.templates.filter(is_active=True).select_related('category')

        sort = self.request.GET.get('sort', 'featured')
        if sort == 'price_asc':
            qs = qs.order_by('price')
        elif sort == 'price_desc':
            qs = qs.order_by('-price')
        elif sort == 'newest':
            qs = qs.order_by('-created_at')
        elif sort == 'rating':
            qs = qs.order_by('-rating')
        else:
            qs = qs.order_by('-is_featured', '-is_bestseller', '-created_at')

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(tagline__icontains=q) | Q(tags__icontains=q))

        ctx['templates'] = qs
        ctx['sort'] = sort
        ctx['query'] = q or ''
        return ctx


class TemplateListView(ListView):
    model = TemplateItem
    template_name = 'catalog/template_list.html'
    context_object_name = 'templates'
    paginate_by = 24

    def get_queryset(self):
        qs = TemplateItem.objects.filter(is_active=True).select_related('category')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(tagline__icontains=q) |
                           Q(tags__icontains=q) | Q(category__name__icontains=q))
        cat = self.request.GET.get('category')
        if cat:
            qs = qs.filter(category__slug=cat)
        tier = self.request.GET.get('tier')
        if tier:
            qs = qs.filter(pricing_tier=tier)
        sort = self.request.GET.get('sort', 'featured')
        if sort == 'price_asc':
            qs = qs.order_by('price')
        elif sort == 'price_desc':
            qs = qs.order_by('-price')
        elif sort == 'newest':
            qs = qs.order_by('-created_at')
        else:
            qs = qs.order_by('-is_featured', '-is_bestseller', '-created_at')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.filter(is_active=True).order_by('order')
        ctx['query'] = self.request.GET.get('q', '')
        ctx['current_category'] = self.request.GET.get('category', '')
        ctx['sort'] = self.request.GET.get('sort', 'featured')
        return ctx


class TemplateDetailView(DetailView):
    model = TemplateItem
    template_name = 'catalog/template_detail.html'
    context_object_name = 'template'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return TemplateItem.objects.filter(is_active=True).select_related('category')\
            .prefetch_related('pages', 'sections', 'custom_fields')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        TemplateItem.objects.filter(pk=self.object.pk).update(
            views_count=self.object.views_count + 1
        )
        ctx['public_pages'] = self.object.pages.filter(is_public=True).order_by('order')
        ctx['related'] = TemplateItem.objects.filter(
            category=self.object.category, is_active=True
        ).exclude(pk=self.object.pk)[:4]
        return ctx


# ----------------------------------------------------------------------
# Live preview & asset serving
# ----------------------------------------------------------------------
def template_preview(request, slug, page=None):
    template = get_object_or_404(TemplateItem, slug=slug, is_active=True)
    engine = PreviewEngine(template=template, page_slug=page, is_customizer=False)
    try:
        return engine.render()
    except Http404:
        # If a subpage doesn't exist, redirect to the template's main page
        # instead of showing a Django 404 — the user should never see a 404 in preview
        from django.urls import reverse
        main_url = reverse('catalog:template_preview', kwargs={'slug': slug})
        return redirect(main_url)


def template_asset(request, slug, asset_path):
    template = get_object_or_404(TemplateItem, slug=slug, is_active=True)
    return serve_template_asset(template, asset_path)
