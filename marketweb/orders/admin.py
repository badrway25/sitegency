from django.contrib import admin
from .models import Customer, Order, OrderItem, License


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['template_name', 'unit_price', 'quantity', 'line_total']

    def line_total(self, obj):
        return obj.line_total if obj.pk else ''


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'company', 'country', 'created_at']
    search_fields = ['email', 'full_name', 'company']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'status', 'total', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'customer__email']
    readonly_fields = ['id', 'order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ['license_key', 'customer', 'template', 'license_type',
                    'is_active', 'issued_at']
    list_filter = ['license_type', 'is_active']
    search_fields = ['license_key', 'customer__email', 'template__name']
    readonly_fields = ['id', 'license_key', 'issued_at']
