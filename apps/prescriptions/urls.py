# home/urls.py

from django.urls import path
from .views import (
    PrescriptionContentView,
    PrescriptionDetailView,
    PrescriptionListView
)

app_name = 'prescriptions'

urlpatterns = [
    path('', PrescriptionListView.as_view(), name='contact'),
    path('<slug:slug>/', PrescriptionDetailView.as_view(), name='about'),
    path('content/<slug:slug>/', PrescriptionContentView.as_view(), name='index'),
]