from django.urls import path
from ..views import (
    PasswordResetByPhoneRequestAPIView,
    PasswordResetByPhoneConfirmAPIView,
)

urlpatterns = [
    path('reset/sms/',         PasswordResetByPhoneRequestAPIView.as_view(),  name='password-reset-sms'),
    path('reset/sms/confirm/', PasswordResetByPhoneConfirmAPIView.as_view(),  name='password-reset-sms-confirm'),
]