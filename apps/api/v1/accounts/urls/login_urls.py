from django.urls import path
from .. import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('force-logout/', views.ForceLogoutView.as_view(), name='force_logout'),
    path('login-status/', views.LoginStatusView.as_view(), name='login_status'),
    
    path('token/refresh/', views.RefreshAccessTokenView.as_view(), name='token_refresh'),
]
