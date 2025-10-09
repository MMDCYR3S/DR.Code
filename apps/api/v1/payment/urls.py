from django.urls import path
from .views.zarinpal_views import PaymentCreateView, PaymentVerifyView
from .views.parspal_views import ParspalPaymentRequestView

app_name = 'payments'

urlpatterns = [
    path('zarinpal/create/', PaymentCreateView.as_view(), name='create'),
    path('zarinpal/verify/', PaymentVerifyView.as_view(), name='verify'),
    
    path('parspal/request/', ParspalPaymentRequestView.as_view(), name='parspal-request'),
    # path('parspal/verify/', ParspalPaymentVerifyView.as_view(), name='parspal-verify'),
    # path('parspal/inquiry/', ParspalPaymentInquiryView.as_view(), name='parspal-inquiry')
]