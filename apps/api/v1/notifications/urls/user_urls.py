from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views import UserNotificationListView, UserNotificationMarkAsReadView

urlpatterns = [
    path('', UserNotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', UserNotificationMarkAsReadView.as_view(), name='notification-read-as-mark'),
]
