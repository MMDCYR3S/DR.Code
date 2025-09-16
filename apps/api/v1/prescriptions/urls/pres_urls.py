from django.urls import path
from .. import views

app_name = 'prescriptions_api'

urlpatterns = [
    path('', views.PrescriptionListView.as_view(), name='prescription-list'),
    path('<slug:slug>/', views.PrescriptionDetailView.as_view(), name='prescription-detail'),
    path('<slug:slug>/description/', views.PrescriptionDescriptionView.as_view(), name='prescription-description'),
]
