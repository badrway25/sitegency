"""
Orders models — customers, orders, line items, licenses.
Payment is mocked but the structure is production-ready for Stripe/PayPal integration.
"""
import uuid
import secrets
from django.db import models
from django.conf import settings


class Customer(models.Model):
    """Extended customer profile linked to auth user OR guest-identified by email."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                null=True, blank=True, related_name='customer_profile')
    email = models.EmailField(db_index=True)
    full_name = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('delivered', 'Delivered'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')

    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=200, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = 'BW-' + secrets.token_hex(5).upper()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    template = models.ForeignKey('catalog.TemplateItem', on_delete=models.PROTECT,
                                 related_name='order_items')
    demo_session = models.ForeignKey('customizer.DemoSession', on_delete=models.SET_NULL,
                                     null=True, blank=True)
    template_name = models.CharField(max_length=200, help_text="Snapshot of template name")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.order.order_number} :: {self.template_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class License(models.Model):
    """A delivered license for a purchased template."""
    LICENSE_TYPES = [
        ('single', 'Single Project'),
        ('extended', 'Extended / Commercial'),
        ('unlimited', 'Unlimited'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license_key = models.CharField(max_length=64, unique=True, db_index=True)
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name='license')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='licenses')
    template = models.ForeignKey('catalog.TemplateItem', on_delete=models.PROTECT,
                                 related_name='licenses')
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPES, default='single')
    download_count = models.PositiveIntegerField(default=0)
    max_downloads = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.license_key

    def save(self, *args, **kwargs):
        if not self.license_key:
            self.license_key = 'BW-LIC-' + secrets.token_urlsafe(16)
        super().save(*args, **kwargs)
