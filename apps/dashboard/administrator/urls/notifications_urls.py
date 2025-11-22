from django.urls import path
from ..views import (
    AnnouncementCreateView,
    AnnouncementDeleteView,
    AnnouncementDetailView,
    AnnouncementUpdateView,
    NotificationCreateView,
    NotificationDeleteView,
    NotificationDashboardView,
    UserSearchJsonView,
)

app_name = 'notifications'

urlpatterns = [
    path('notifications/', NotificationDashboardView.as_view(), name='notifications_list'),
    path('single/create/', NotificationCreateView.as_view(), name='single_create'),
    path('single/<int:pk>/delete/', NotificationDeleteView.as_view(), name='single_delete'),
    path('announcements/create/', AnnouncementCreateView.as_view(), name='announcement_create'),
    path('announcements/<int:pk>/delete/', AnnouncementDeleteView.as_view(), name='announcement_delete'),
    path('announcements/<int:pk>/', AnnouncementDetailView.as_view(), name='announcement_detail'),
    path('announcements/<int:pk>/update/', AnnouncementUpdateView.as_view(), name='announcement_update'),
    path('api/search-users/', UserSearchJsonView.as_view(), name='user_search_json'),
]
