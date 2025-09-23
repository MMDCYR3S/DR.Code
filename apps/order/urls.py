from django.urls import path
from .views import PlanOrderView

app_name = "order"

urlpatterns = [
    path("checkout/", PlanOrderView.as_view(), name="checkout")
]
