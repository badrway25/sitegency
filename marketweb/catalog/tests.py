"""
Integration & smoke tests for the Sitegency marketplace.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse

from catalog.models import Category, TemplateItem, TemplatePage
from customizer.models import DemoSession
from core.models import SiteConfig, FAQ


class SmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteConfig.get_solo()
        FAQ.objects.create(question='Test?', answer='Yes.', is_published=True)
        cls.category = Category.objects.create(
            name='Medical', slug='medical', tagline='Medical tpl',
            icon_class='bi-heart', accent_color='#06b6d4', is_active=True, is_featured=True,
        )
        cls.template = TemplateItem.objects.create(
            name='MediTest', slug='medical-meditest', category=cls.category,
            tagline='Test medical template', price=59, source_dir='test/test',
            entry_file='index.html', is_active=True, is_featured=True,
        )
        TemplatePage.objects.create(
            template=cls.template, name='Home', slug='home',
            file_path='index.html', is_entry=True, is_public=True, order=0,
        )

    def test_homepage_renders(self):
        r = self.client.get(reverse('core:home'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Sitegency')
        self.assertContains(r, 'Medical')

    def test_about_page(self):
        self.assertEqual(self.client.get(reverse('core:about')).status_code, 200)

    def test_faq_page(self):
        r = self.client.get(reverse('core:faq'))
        self.assertEqual(r.status_code, 200)
        # FAQ page now uses categorized pool (FAQ_CATEGORIZED) — assert against
        # the first category and a known question from the new EN pool.
        self.assertContains(r, 'Getting started')
        self.assertContains(r, 'How exactly does Sitegency work')

    def test_contact_page(self):
        self.assertEqual(self.client.get(reverse('core:contact')).status_code, 200)

    def test_category_list(self):
        r = self.client.get(reverse('catalog:category_list'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Medical')

    def test_category_detail(self):
        r = self.client.get(reverse('catalog:category_detail', kwargs={'slug': 'medical'}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'MediTest')

    def test_template_list(self):
        r = self.client.get(reverse('catalog:template_list'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'MediTest')

    def test_template_list_filter_by_category(self):
        r = self.client.get(reverse('catalog:template_list') + '?category=medical')
        self.assertEqual(r.status_code, 200)

    def test_template_list_search(self):
        r = self.client.get(reverse('catalog:template_list') + '?q=MediTest')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'MediTest')

    def test_template_detail(self):
        r = self.client.get(reverse('catalog:template_detail', kwargs={'slug': self.template.slug}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'MediTest')
        self.assertContains(r, reverse('catalog:template_preview', kwargs={'slug': self.template.slug}))
        self.assertContains(r, reverse('customizer:customize', kwargs={'slug': self.template.slug}))
        self.assertContains(r, reverse('orders:checkout', kwargs={'slug': self.template.slug}))

    def test_customizer_renders(self):
        r = self.client.get(reverse('customizer:customize', kwargs={'slug': self.template.slug}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Live Preview')
        self.assertContains(r, 'bw-customize-form')

    def test_checkout_get(self):
        r = self.client.get(reverse('orders:checkout', kwargs={'slug': self.template.slug}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Checkout')

    def test_checkout_post_creates_order(self):
        r = self.client.post(
            reverse('orders:checkout', kwargs={'slug': self.template.slug}),
            {'email': 'buyer@test.com', 'full_name': 'Test Buyer',
             'country': 'Italy', 'city': 'Rome'},
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn('confirmation', r.url)

    def test_customizer_save_session(self):
        url = reverse('customizer:save_session', kwargs={'slug': self.template.slug})
        r = self.client.post(url,
            data=json.dumps({'data': {'brand_name': 'MyBrand', 'hero_title': 'Hello'}}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['ok'])
        session = DemoSession.objects.get(template=self.template)
        self.assertEqual(session.data.get('brand_name'), 'MyBrand')


class ScannerTests(TestCase):
    def test_blocked_page_detection(self):
        from importer.services.scanner import _is_blocked_page
        self.assertTrue(_is_blocked_page('elements.html'))
        self.assertTrue(_is_blocked_page('typography.html'))
        self.assertTrue(_is_blocked_page('bootstrap-components.html'))
        self.assertTrue(_is_blocked_page('ui-elements.html'))
        self.assertFalse(_is_blocked_page('index.html'))
        self.assertFalse(_is_blocked_page('about.html'))
        self.assertFalse(_is_blocked_page('contact.html'))
        self.assertFalse(_is_blocked_page('services.html'))


class ModelTests(TestCase):
    def test_category_slug_autogenerated(self):
        c = Category.objects.create(name='Dental Wellness')
        self.assertEqual(c.slug, 'dental-wellness')

    def test_template_discount_percent(self):
        c = Category.objects.create(name='Test', slug='test-cat')
        t = TemplateItem.objects.create(
            name='T1', slug='t1', category=c, price=60, original_price=100,
        )
        self.assertEqual(t.discount_percent, 40)
