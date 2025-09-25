from django.urls import path, include

app_name = "accounts"

urlpatterns = [
    path('', include('apps.api.v1.accounts.urls.register_urls')),
    path('', include('apps.api.v1.accounts.urls.login_urls')),
    path('profile/', include('apps.api.v1.accounts.urls.profile_urls')),
]