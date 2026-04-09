from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('templates/<slug:slug>/', views.TemplateDetailView.as_view(), name='template_detail'),
    # Live preview (template home page)
    path('preview/<slug:slug>/', views.template_preview, name='template_preview'),
    # Live preview of a specific inner page
    path('preview/<slug:slug>/page/<slug:page>/', views.template_preview,
         name='template_preview_page'),
]
