"""
Orders views — checkout flow (mocked payment, production-ready structure).
"""
from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone

from catalog.models import TemplateItem
from customizer.models import DemoSession
from .models import Customer, Order, OrderItem, License


@require_http_methods(["GET", "POST"])
def checkout(request, slug):
    template = get_object_or_404(TemplateItem, slug=slug, is_active=True)
    demo_session = None
    token = request.session.get('bw_token')
    if token:
        demo_session = DemoSession.objects.filter(
            template=template, session_token=token
        ).first()

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        full_name = request.POST.get('full_name', '').strip()
        company = request.POST.get('company', '').strip()
        phone = request.POST.get('phone', '').strip()
        country = request.POST.get('country', '').strip()
        city = request.POST.get('city', '').strip()

        if not email or not full_name:
            messages.error(request, 'Please provide your name and email.')
        else:
            customer, _ = Customer.objects.get_or_create(
                email=email,
                defaults={'full_name': full_name, 'company': company,
                          'phone': phone, 'country': country, 'city': city},
            )
            customer.full_name = full_name or customer.full_name
            customer.company = company or customer.company
            customer.phone = phone or customer.phone
            customer.country = country or customer.country
            customer.city = city or customer.city
            customer.save()

            subtotal = template.price
            tax = Decimal('0.00')
            total = subtotal + tax

            order = Order.objects.create(
                customer=customer,
                subtotal=subtotal, tax=tax, total=total,
                status='paid',
                payment_method='demo',
                payment_reference='DEMO-' + str(int(timezone.now().timestamp())),
                paid_at=timezone.now(),
            )
            item = OrderItem.objects.create(
                order=order, template=template,
                demo_session=demo_session,
                template_name=template.name,
                unit_price=template.price, quantity=1,
            )
            License.objects.create(
                order_item=item, customer=customer, template=template,
                license_type='single',
            )
            if demo_session:
                demo_session.converted_to_order = True
                demo_session.save(update_fields=['converted_to_order'])

            return redirect('orders:confirmation', order_number=order.order_number)

    return render(request, 'orders/checkout.html', {
        'template': template,
        'demo_session': demo_session,
    })


def confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'orders/confirmation.html', {'order': order})
