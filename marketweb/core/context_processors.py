from django.conf import settings
from catalog.models import Category


def marketplace_context(request):
    """Global template context: brand, categories (for menu), site config."""
    try:
        nav_categories = list(
            Category.objects.filter(is_active=True).order_by('order', 'name')[:15]
        )
    except Exception:
        nav_categories = []
    return {
        'BRAND_NAME': getattr(settings, 'BRAND_NAME', 'Sitegency'),
        'BRAND_TAGLINE': getattr(settings, 'BRAND_TAGLINE', ''),
        'BRAND_DESCRIPTION': getattr(settings, 'BRAND_DESCRIPTION', ''),
        'NAV_CATEGORIES': nav_categories,
    }
