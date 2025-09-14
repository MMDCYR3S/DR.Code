from django.urls import path
from .. import views

app_name = "accounts"

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='user-register'),
    path('verify-profile/', views.UserProfileVerificationView.as_view(), name='profile-verification'),
]