"""
Catalog models — Categories, Templates, Pages, Assets, Sections, Customization Fields.
The catalog is the heart of the marketplace.
"""
import uuid
from django.db import models
from django.utils.text import slugify
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    tagline = models.CharField(max_length=200, blank=True,
                               help_text="Short persuasive tagline for category hero")
    description = models.TextField(blank=True)
    icon_class = models.CharField(max_length=80, blank=True,
                                  help_text="Bootstrap icon class e.g. bi-heart-pulse")
    accent_color = models.CharField(max_length=20, default="#6366f1",
                                    help_text="Hex color for category accents")
    cover_image = models.CharField(max_length=500, blank=True,
                                   help_text="URL or path for hero cover")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:category_detail', kwargs={'slug': self.slug})

    @property
    def template_count(self):
        return self.templates.filter(is_active=True).count()


class TemplateItem(models.Model):
    PRICING_TIERS = [
        ('starter', 'Starter'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('elite', 'Elite'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='templates')

    tagline = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=300, blank=True)

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=49.00)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pricing_tier = models.CharField(max_length=20, choices=PRICING_TIERS, default='standard')

    # Source metadata (link to raw template dir in Templates/)
    source_dir = models.CharField(max_length=500, blank=True,
                                  help_text="Path relative to TEMPLATE_SOURCE_DIR, e.g. 'Animal/animal'")
    entry_file = models.CharField(max_length=200, default='index.html')

    # Media (optional — preview engine generates live previews from source_dir)
    thumbnail = models.ImageField(upload_to='templates/thumbnails/', blank=True, null=True)
    preview_color_1 = models.CharField(max_length=20, default="#6366f1")
    preview_color_2 = models.CharField(max_length=20, default="#ec4899")

    # Flags
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Metadata
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    technologies = models.CharField(max_length=300, blank=True,
                                    default="HTML5, CSS3, Bootstrap 5, JavaScript")
    responsive = models.BooleanField(default=True)
    pages_count = models.PositiveIntegerField(default=1)

    # Stats
    downloads = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=4.80)
    reviews_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:template_detail', kwargs={'slug': self.slug})

    def get_preview_url(self):
        return reverse('catalog:template_preview', kwargs={'slug': self.slug})

    def get_customizer_url(self):
        return reverse('customizer:customize', kwargs={'slug': self.slug})

    def get_checkout_url(self):
        return reverse('orders:checkout', kwargs={'slug': self.slug})

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]


class TemplatePage(models.Model):
    """A navigable HTML page within a template (home, about, contact, ...)."""
    template = models.ForeignKey(TemplateItem, on_delete=models.CASCADE, related_name='pages')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120)
    file_path = models.CharField(max_length=500,
                                 help_text="Relative path within template source dir")
    order = models.PositiveIntegerField(default=0)
    is_entry = models.BooleanField(default=False)
    # Whether this page should be shown in navigation (filters out demo/element pages)
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        unique_together = ['template', 'slug']

    def __str__(self):
        return f"{self.template.name} — {self.name}"


class TemplateAsset(models.Model):
    ASSET_TYPES = [
        ('css', 'CSS'),
        ('js', 'JavaScript'),
        ('img', 'Image'),
        ('font', 'Font'),
        ('other', 'Other'),
    ]
    template = models.ForeignKey(TemplateItem, on_delete=models.CASCADE, related_name='assets')
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    file_path = models.CharField(max_length=500)
    file_size = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=['template', 'asset_type'])]

    def __str__(self):
        return f"{self.asset_type}: {self.file_path}"


class TemplateSection(models.Model):
    """Logical section within a template (hero, about, services, contact, ...)."""
    template = models.ForeignKey(TemplateItem, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=100)
    section_id = models.CharField(max_length=150, blank=True,
                                  help_text="HTML id, class, or selector")
    order = models.PositiveIntegerField(default=0)
    is_customizable = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.template.name} — {self.name}"


class TemplateCustomizationField(models.Model):
    """Declares which elements of a template can be customized by the buyer."""
    FIELD_TYPES = [
        ('text', 'Short Text'),
        ('textarea', 'Long Text'),
        ('image', 'Image Upload'),
        ('color', 'Color'),
        ('url', 'URL'),
        ('email', 'Email'),
        ('phone', 'Phone'),
    ]

    template = models.ForeignKey(TemplateItem, on_delete=models.CASCADE, related_name='custom_fields')
    field_key = models.CharField(max_length=100)
    field_label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text')
    placeholder = models.CharField(max_length=300, blank=True)
    default_value = models.TextField(blank=True)
    group = models.CharField(max_length=100, default='branding',
                             help_text="UI group: branding, hero, contact, colors, content")
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=False)

    class Meta:
        ordering = ['group', 'order']
        unique_together = ['template', 'field_key']

    def __str__(self):
        return f"{self.template.name} — {self.field_label}"
