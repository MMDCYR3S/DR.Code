from django.urls import path
from ..views import (
    PasswordResetRequestAPIView, 
    PasswordResetConfirmAPIView,
    PasswordResetByPhoneRequestAPIView
)

urlpatterns = [
    path('reset/', PasswordResetRequestAPIView.as_view(), name='password-reset-request'),
    path('reset/confirm/', PasswordResetConfirmAPIView.as_view(), name='password-reset-confirm'),
    path('reset/sms/', PasswordResetByPhoneRequestAPIView.as_view(), name='password-reset-request-sms'),
]
