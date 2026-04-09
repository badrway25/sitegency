"""
Template tags / filters for Sitegency.
(Module kept under legacy `badrway_tags` name to preserve `{% load %}` imports
across existing templates — all user-visible content has been rebranded.)
"""
from decimal import Decimal
from django import template
from django.utils.translation import get_language
from django.utils.safestring import mark_safe

from customizer.content_pool import images_for
from customizer.dynamic_content import (
    get_category_content,
    get_template_tagline,
    get_template_about,
    get_category_name,
    get_localized_faqs,
    get_localized_testimonials,
)

register = template.Library()


def _active_locale():
    try:
        loc = (get_language() or 'en').split('-')[0]
        return loc if loc in ('en', 'it', 'fr', 'ar') else 'en'
    except Exception:
        return 'en'


@register.filter
def local_tagline(obj):
    """Return a locale-native tagline for a Category or TemplateItem."""
    if obj is None:
        return ''
    loc = _active_locale()
    if hasattr(obj, 'templates'):  # Category
        return get_category_content(obj, loc).get('tagline', '') or (obj.tagline or '')
    if hasattr(obj, 'category'):   # TemplateItem
        return get_template_tagline(obj, loc) or (obj.tagline or '')
    return ''


@register.filter
def local_description(obj):
    """Return a locale-native description for a Category or TemplateItem."""
    if obj is None:
        return ''
    loc = _active_locale()
    if hasattr(obj, 'templates'):  # Category
        return get_category_content(obj, loc).get('description', '') or (obj.description or '')
    if hasattr(obj, 'category'):   # TemplateItem: use smart per-template about
        return get_template_about(obj, loc)
    return ''


@register.filter
def local_about(template_obj):
    """Return the smart 'About this template' copy for a TemplateItem."""
    if template_obj is None:
        return ''
    return get_template_about(template_obj, _active_locale())


@register.filter
def local_name(category):
    """Return the locale-aware display name for a Category."""
    if category is None:
        return ''
    return get_category_name(category, _active_locale())


@register.simple_tag
def localized_faqs():
    """Return the locale-native FAQ list for rendering on homepage/FAQ page."""
    return get_localized_faqs(_active_locale())


@register.simple_tag
def localized_testimonials():
    """Return locale-native testimonials for the homepage reviews section."""
    return get_localized_testimonials(_active_locale())


@register.filter
def category_image(category, index=0):
    """Return a hotlink-friendly Unsplash image URL for a category."""
    try:
        name = category.name if hasattr(category, 'name') else str(category)
        imgs = images_for(name)
        if imgs:
            return imgs[int(index) % len(imgs)]
    except Exception:
        pass
    return 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=1200&q=80'


@register.filter
def strip_locale_prefix(url):
    """Strip the /it/, /fr/, /ar/ locale prefix from a URL.

    Used by the language switcher: when the user is on /it/templates/ and
    clicks "Français", we submit next='/templates/' instead of '/it/templates/'
    so Django's set_language + translate_url can cleanly add the new /fr/
    prefix. Without this strip, translate_url fails because resolve('/it/...')
    raises Resolver404 when the new language is already active.
    """
    if not url or not isinstance(url, str):
        return url or '/'
    from django.conf import settings
    for code, _name in settings.LANGUAGES:
        prefix = f'/{code}/'
        if url == f'/{code}' or url == prefix:
            return '/'
        if url.startswith(prefix):
            return '/' + url[len(prefix):]
    return url


@register.simple_tag
def unsplash_image(category_name, index=0):
    """Same as category_image but as a simple tag."""
    try:
        imgs = images_for(category_name)
        if imgs:
            return imgs[int(index) % len(imgs)]
    except Exception:
        pass
    return 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=1200&q=80'


@register.filter
def eur(value):
    """Format a numeric value as an elegant Euro price, locale-aware.

    - en: €49
    - it: 49 €
    - fr: 49 €
    - ar: ‎49 €‎
    """
    if value is None or value == '':
        return ''
    try:
        amount = Decimal(str(value))
    except Exception:
        return str(value)

    # Quantize: strip trailing .00
    if amount == amount.to_integral_value():
        formatted = f"{int(amount)}"
    else:
        formatted = f"{amount:.2f}"

    lang = (get_language() or 'en').split('-')[0]
    if lang == 'en':
        return mark_safe(f"€{formatted}")
    elif lang == 'ar':
        return mark_safe(f"{formatted} €")
    else:
        # it, fr: "49 €" (space + euro after)
        return mark_safe(f"{formatted} €")
