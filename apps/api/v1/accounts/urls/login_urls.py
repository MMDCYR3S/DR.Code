from django.urls import path
from .. import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', views.RefreshAccessTokenView.as_view(), name='token_refresh'),
    path("login-status/", views.LoginStatusView.as_view(), name="login-status")
]
