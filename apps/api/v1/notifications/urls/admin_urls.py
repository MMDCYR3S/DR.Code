from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views import NotificationListView, NotificationMarkAsReadView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', NotificationMarkAsReadView.as_view(), name='notification-read-as-mark'),
]
