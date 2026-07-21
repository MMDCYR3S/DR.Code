from django.urls import path
from ..views import (
    AdminUsersListView,
    UserDetailView,
    UserCreateView,
    UserDeleteView,
    PendingVerificationListView,
    ExportUsersToExcelView,
)

app_name = 'users'

urlpatterns = [
    path('users/', AdminUsersListView.as_view(), name='admin_users_list'),
    path('users/add/', UserCreateView.as_view(), name='admin_user_create'),
    path('users/export/', ExportUsersToExcelView.as_view(), name='admin_export_users'),

    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='admin_user_delete'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='admin_user_detail'),

    path('verification-queue/', PendingVerificationListView.as_view(), name='admin_verification_queue'),
]
