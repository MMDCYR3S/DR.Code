from django.urls import path
from ..views import AdminUsersListView

app_name = 'users'

urlpatterns = [
    path('users/', AdminUsersListView.as_view(), name='users'),
]