from django.urls import path, include

app_name = "home"

urlpatterns = [
    path("", include("apps.api.v1.home.urls.contact_urls")),
    path("", include("apps.api.v1.home.urls.tutorial_vid_urls")),
]
