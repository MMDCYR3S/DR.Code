from django.urls import path
from .views import PaymentCreateView, PaymentVerifyView

app_name = 'payments'

urlpatterns = [
    path('create/', PaymentCreateView.as_view(), name='create'),
    path('verify/', PaymentVerifyView.as_view(), name='verify'),
]