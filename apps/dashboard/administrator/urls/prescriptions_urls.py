from django.urls import path
from ..views import *

app_name = 'prescriptions'

urlpatterns = [
    path('', PrescriptionListView.as_view(), name='prescription_list'),
    path('detail/<int:pk>/', PrescriptionDetailView.as_view(), name='prescription_detail'),
    path('create/', PrescriptionCreateView.as_view(), name='prescription_create'),
    path('<int:pk>/update/', PrescriptionUpdateView.as_view(), name='prescription_update'),
    path('<int:pk>/delete/', PrescriptionDeleteView.as_view(), name='prescription_delete'),
]