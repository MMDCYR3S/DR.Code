from django.urls import path, include
from ..views import *

app_name = 'prescriptions'

urlpatterns = [
    path('prescriptions/', PrescriptionListView.as_view(), name='prescription_list'),
    path('prescriptions/detail/<int:pk>/', PrescriptionDetailView.as_view(), name='prescription_detail'),
    path('prescriptions/create/', PrescriptionCreateView.as_view(), name='prescription_create'),
    path('prescriptions/update/<int:pk>/', PrescriptionUpdateView.as_view(), name='prescription_update'),
    path('prescriptions/delete/<int:pk>/', PrescriptionDeleteView.as_view(), name='prescription_delete'),
    # path('', include('apps.dashboard.administrator.urls.drugs_urls')),
]