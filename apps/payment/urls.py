from django.urls import path, include
from .views import RequestView

urlpatterns = [
    path("request/", RequestView.as_view(), name="payment-request")
]

