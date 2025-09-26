from django.urls import path, include

urlpatterns = [
    path('admin/', include("apps.api.v1.notifications.urls.admin_urls")),
    path('user/', include("apps.api.v1.notifications.urls.user_urls")),
]
