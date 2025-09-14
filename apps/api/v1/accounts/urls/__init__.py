from django.urls import path, include

urlpatterns = [
    path('', include('apps.api.v1.accounts.urls.register_urls')),
]