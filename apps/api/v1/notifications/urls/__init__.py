from django.urls import path, include

urlpatterns = [
    path('', include("apps.api.v1.notifications.urls.admin_urls")),
]
