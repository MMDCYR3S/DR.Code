from django.urls import path, include
from .views import RequestView, AfterPayView

app_name = "payment"

urlpatterns = [
    path("request/", RequestView.as_view(), name="payment-request"),
    path("status/", AfterPayView.as_view(), name="payment-callback"),
]

