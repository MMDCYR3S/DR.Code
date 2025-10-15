from django.urls import path
from .views import PlanOrderView

app_name = "order"

urlpatterns = [
    path("checkout/<int:plan_id>/", PlanOrderView.as_view(), name="checkout")
]
