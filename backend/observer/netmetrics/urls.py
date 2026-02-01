from django.urls import path
from . import views

app_name = 'netmetrics'

urlpatterns = [
    path('interfaces/', views.interfaces_list, name='interfaces_list'),
    path('summary/', views.network_summary, name='network_summary'),
]