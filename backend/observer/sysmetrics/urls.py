from django.urls import path
from . import views

app_name = 'sysmetrics'

urlpatterns = [
    # System metrics endpoints will be implemented later
    path('', views.placeholder_view, name='placeholder'),
]