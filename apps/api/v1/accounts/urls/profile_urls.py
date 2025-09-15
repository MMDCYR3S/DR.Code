from django.urls import path
from .. import views

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('update-profile/', views.UpdateProfileView.as_view(), name='update_profile'),
]
