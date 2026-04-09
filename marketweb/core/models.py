"""
Core models — site-wide configuration and content (FAQ, testimonials, stats).
"""
from django.db import models


class SiteConfig(models.Model):
    """Singleton site configuration (hero copy, stats, meta)."""
    brand_name = models.CharField(max_length=100, default='Sitegency')
    brand_tagline = models.CharField(max_length=300,
                                     default='Premium website templates, instantly yours')
    hero_title = models.CharField(max_length=300,
                                  default='Launch a stunning website in minutes, not months')
    hero_subtitle = models.TextField(
        default='Browse thousands of premium templates, customize every pixel '
                'with your own data, and preview the final result live — before you pay.'
    )
    stat_templates = models.PositiveIntegerField(default=850)
    stat_customers = models.PositiveIntegerField(default=12400)
    stat_countries = models.PositiveIntegerField(default=92)
    stat_satisfaction = models.PositiveIntegerField(default=99)

    support_email = models.EmailField(default='support@sitegency.com')
    support_phone = models.CharField(max_length=50, blank=True, default='+1 (555) 010-0420')

    class Meta:
        verbose_name = 'Site Configuration'
        verbose_name_plural = 'Site Configuration'

    def __str__(self):
        return 'Sitegency site configuration'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class FAQ(models.Model):
    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True, default='general')
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    author_name = models.CharField(max_length=200)
    author_role = models.CharField(max_length=200, blank=True)
    author_company = models.CharField(max_length=200, blank=True)
    avatar_url = models.CharField(max_length=500, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    content = models.TextField()
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return f"{self.author_name} — {self.author_company}"
