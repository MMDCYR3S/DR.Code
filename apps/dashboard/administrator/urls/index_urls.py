from django.urls import path
from ..views import admin_dashboard_view

app_name = 'index'

urlpatterns = [
    path('', admin_dashboard_view, name='index'),
]
