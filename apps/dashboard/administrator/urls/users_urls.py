from django.urls import path
from ..views import (
    AdminUsersListView,
    UserUpdateView,
    UserDeleteView,
    UserVerificationDetailView,
    PendingVerificationListView,
    AddUserView,
    ExportUsersToExcelView
)

app_name = 'users'

urlpatterns = [
    path('users/', AdminUsersListView.as_view(), name='admin_users_list'),
    path('users/add/', AddUserView.as_view(), name='admin_add_user'),
    path('users/export/', ExportUsersToExcelView.as_view(), name='admin_export_users'),
    
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='admin_user_update'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='admin_user_delete'),
    
    path('verification-queue/', PendingVerificationListView.as_view(), name='admin_verification_queue'),
    
    path('users/<int:pk>/', UserVerificationDetailView.as_view(), name='admin_user_detail'),
]