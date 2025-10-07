from django.urls import path
from .views import (
    RegisterView, LoginView, AuthenticationView,
    ProfileView, ProfileMessagesView,
    ProfileSavedPrescriptionsView,
    CheckAuthStatusView,
    ProfileNotificationsView
)
app_name = 'accounts'

urlpatterns = [
    path('authentication/', AuthenticationView.as_view(), name='authentication'),
    
    # صفحات کاربری (نیاز به احراز هویت)
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/saved/', ProfileSavedPrescriptionsView.as_view(), name='profile_saved_prescriptions'),
    path('profile/messages/', ProfileMessagesView.as_view(), name='profile_messages'),
    path('profile/notifications/', ProfileNotificationsView.as_view(), name='profile_notifications'),
    path('check-auth-status/', CheckAuthStatusView.as_view(), name='check_auth_status'),
]