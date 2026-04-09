from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/<slug:slug>/', views.checkout, name='checkout'),
    path('confirmation/<str:order_number>/', views.confirmation, name='confirmation'),
]
