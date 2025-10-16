from django.urls import path, include
from .views import RequestView, AfterPayView

urlpatterns = [
    path("request/", RequestView.as_view(), name="payment-request"),
    path("status/", RequestView.as_view(), name="payment-status"),
]

