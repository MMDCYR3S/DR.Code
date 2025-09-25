from django.urls import path, include

urlpatterns = [
    path("", include("apps.dashboard.administrator.urls.users_urls")),
    path("", include("apps.dashboard.administrator.urls.categories_urls")),
    path("", include("apps.dashboard.administrator.urls.prescriptions_urls")),
    path("", include("apps.dashboard.administrator.urls.contacts_urls")),
    path("", include("apps.dashboard.administrator.urls.messages_urls")),
    path("", include("apps.dashboard.administrator.urls.discounts_urls")),
    path("", include("apps.dashboard.administrator.urls.tutorials_urls")),
    path("", include("apps.dashboard.administrator.urls.drugs_urls")),
]
