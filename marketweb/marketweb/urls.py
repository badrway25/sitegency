"""
URL configuration for marketweb (Sitegency marketplace).

All customer-facing URLs are language-aware via i18n_patterns (no prefix for
English, /it/, /fr/, /ar/ for the others). Static asset serving and admin are
language-independent.
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from catalog.views import template_asset

# Language-independent endpoints
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    # Assets served raw, no language prefix (browsers cache these independently)
    re_path(r'^assets/(?P<slug>[\w-]+)/(?P<asset_path>.+)$', template_asset,
            name='template_asset'),
]

# Language-aware marketplace
urlpatterns += i18n_patterns(
    path('', include('core.urls', namespace='core')),
    path('', include('catalog.urls', namespace='catalog')),
    path('', include('customizer.urls', namespace='customizer')),
    path('', include('orders.urls', namespace='orders')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
