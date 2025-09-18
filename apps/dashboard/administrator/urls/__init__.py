from django.urls import path, include

urlpatterns = [
    path("", include("apps.dashboard.administrator.urls.users_urls")),
]
