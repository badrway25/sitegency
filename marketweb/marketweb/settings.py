"""
Django settings for marketweb project — Sitegency Marketplace.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent  # /c/tmp/sitoBadr

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-^xw&qc!s^kd$1b59qle!-veeqpwcx$=bdj*id(m+do=z8p41l3'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*'] if DEBUG else os.environ.get('ALLOWED_HOSTS', '').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Third party
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    # Project apps
    'core.apps.CoreConfig',
    'catalog.apps.CatalogConfig',
    'customizer.apps.CustomizerConfig',
    'orders.apps.OrdersConfig',
    'importer.apps.ImporterConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # i18n — after session, before common
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'marketweb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.marketplace_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'marketweb.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

from django.utils.translation import gettext_lazy as _
LANGUAGES = [
    ('en', _('English')),
    ('it', _('Italiano')),
    ('fr', _('Français')),
    ('ar', _('العربية')),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Template source directory (raw HTML templates to import)
TEMPLATE_SOURCE_DIR = PROJECT_ROOT / 'Templates'

# Template preview — served via Django for live navigation
TEMPLATE_PREVIEW_URL = '/preview/'

# Adapted templates — these have their own visual system (CSS, fonts, palette)
# and opt out of the PreviewEngine's aggressive differentiation layer.
# Only structural/safety rules are injected for these templates.
# To add a new template: add its DB slug here after completing its visual system.
# To rollback: remove the slug — the full engine layer will be re-applied.
ADAPTED_TEMPLATE_SLUGS = [
    'medical-medilux',    # Medilux — Medical/drpro
    'agency-blueprint',   # Nova Creative — Agency/avo
    'animal-vetaura-2',   # ZampaCura — Animal/petvet
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Security headers for preview iframes
X_FRAME_OPTIONS = 'SAMEORIGIN'

# File upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Brand settings
BRAND_NAME = 'Sitegency'
BRAND_TAGLINE = 'Premium Website Templates, Instantly Yours'
BRAND_DESCRIPTION = 'The world\'s most advanced marketplace for premium, fully customizable website templates.'
