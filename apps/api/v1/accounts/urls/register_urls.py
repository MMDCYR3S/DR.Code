from django.urls import path
from .. import views

urlpatterns = [
    # ثبت‌نام و احراز هویت
    path('register/', views.RegisterView.as_view(), name='register'),
    path('authentication/', views.AuthenticationView.as_view(), name='authentication'),
    path('resend-authentication/', views.ResendAuthenticationView.as_view(), name='resend_authentication'),
    
    # بررسی وضعیت احراز هویت
    path('check-auth-status/', views.CheckAuthStatusView.as_view(), name='check_auth_status'),
    
    # خروج
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
