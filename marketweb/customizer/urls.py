from django.urls import path
from . import views

app_name = 'customizer'

urlpatterns = [
    path('customize/<slug:slug>/', views.customize, name='customize'),
    path('customize/<slug:slug>/preview/', views.customize_preview, name='customize_preview'),
    path('customize/<slug:slug>/preview/<slug:page>/', views.customize_preview,
         name='customize_page'),
    path('customize/<slug:slug>/save/', views.save_session, name='save_session'),
    path('customize/<slug:slug>/upload/', views.upload_media, name='upload_media'),
]
