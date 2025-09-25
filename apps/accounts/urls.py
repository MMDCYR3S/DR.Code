from django.urls import path
from .views import (
    RegisterView, LoginView, AuthenticationView,
    ProfileView, ProfileMessagesView,
    ProfileSavedPrescriptionsView,
    CheckAuthStatusView
)
app_name = 'accounts'

urlpatterns = [
    # احراز هویت
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('authentication/', AuthenticationView.as_view(), name='authentication'),
    
    # صفحات کاربری (نیاز به احراز هویت)
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/saved/', ProfileSavedPrescriptionsView.as_view(), name='profile'),
    path('profile/messages/', ProfileMessagesView.as_view(), name='profile'),
    path('check-auth-status/', CheckAuthStatusView.as_view(), name='check_auth_status'),
]