from django.urls import path
from .views.zarinpal_views import PaymentCreateView, PaymentVerifyView
from .views.parspal_views import ParspalPaymentRequestView, ParspalInquiryView, ParspalVerifyView, ParspalCallbackView

app_name = 'payments'

urlpatterns = [
    path('zarinpal/create/', PaymentCreateView.as_view(), name='create'),
    path('zarinpal/verify/', PaymentVerifyView.as_view(), name='verify'),
    
    path('parspal/request/', ParspalPaymentRequestView.as_view(), name='parspal-request'),
    path('parspal/verify/', ParspalVerifyView.as_view(), name='parspal-verify'),
    path('parspal/callback/', ParspalCallbackView.as_view(), name='parspal-callback'),
    path('parspal/inquiry/', ParspalInquiryView.as_view(), name='parspal-inquiry')
]