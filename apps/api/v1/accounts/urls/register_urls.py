from django.urls import path
from .. import views

urlpatterns = [
    # ثبت‌نام و احراز هویت
    path('register/', views.RegisterView.as_view(), name='register'),
    path('authentication/', views.AuthenticationView.as_view(), name='authentication'),
    path('resend-authentication/', views.ResendAuthenticationView.as_view(), name='resend_authentication'),
    # خروج
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
