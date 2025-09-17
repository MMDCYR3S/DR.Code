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
    path('detail/', PrescriptionDetailView.as_view(), name='about'),
    path('detail/content/', PrescriptionContentView.as_view(), name='index'),
]