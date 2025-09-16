from django.urls import path, include

urlpatterns = [
    path("", include("apps.api.v1.prescriptions.urls.pres_urls")),
]
