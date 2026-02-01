from django.urls import path
from . import views

app_name = 'template_dashboards'

urlpatterns = [
    # Dashboard Template endpoints
    path('templates/', views.list_templates, name='list_templates'),
    path('templates/<uuid:template_id>/', views.get_template, name='get_template'),
    path('templates/create/', views.create_template, name='create_template'),
    path('templates/<uuid:template_id>/update/', views.update_template, name='update_template'),
    path('templates/<uuid:template_id>/delete/', views.delete_template, name='delete_template'),
    path('templates/<uuid:template_id>/version/', views.create_template_version, name='create_template_version'),
    path('templates/<uuid:template_id>/share/', views.share_template, name='share_template'),
    
    # Dashboard Instance endpoints
    path('dashboards/', views.list_dashboards, name='list_dashboards'),
    path('dashboards/<uuid:dashboard_id>/', views.get_dashboard, name='get_dashboard'),
    path('dashboards/create/', views.create_dashboard, name='create_dashboard'),
    path('dashboards/<uuid:dashboard_id>/update/', views.update_dashboard, name='update_dashboard'),
    path('dashboards/<uuid:dashboard_id>/delete/', views.delete_dashboard, name='delete_dashboard'),
    path('dashboards/<uuid:dashboard_id>/share/', views.share_dashboard, name='share_dashboard'),
    
    # Statistics and Analytics endpoints
    path('categories/', views.get_template_categories, name='get_template_categories'),
    path('stats/', views.get_dashboard_stats, name='get_dashboard_stats'),
]