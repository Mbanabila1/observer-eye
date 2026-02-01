from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    # Configuration categories
    path('categories/', views.get_categories, name='get_categories'),
    
    # Configuration settings
    path('settings/', views.get_settings, name='get_settings'),
    path('settings/<uuid:setting_id>/update/', views.update_setting, name='update_setting'),
    path('settings/validate/', views.validate_settings, name='validate_settings'),
    
    # Configuration profiles
    path('profiles/', views.get_profiles, name='get_profiles'),
    path('profiles/create/', views.create_profile, name='create_profile'),
    path('profiles/<uuid:profile_id>/deploy/', views.deploy_profile, name='deploy_profile'),
    
    # Change history
    path('history/', views.get_change_history, name='get_change_history'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
]