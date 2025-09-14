from django.urls import path, include

app_name = "v1"

urlpatterns = [
    path('accounts/', include('apps.api.v1.accounts.urls')),
]
