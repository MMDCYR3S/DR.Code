from django.urls import path, include

app_name = "dashboard"

urlpatterns = [
    path("admin/", include("apps.dashboard.administrator.urls")),
]
