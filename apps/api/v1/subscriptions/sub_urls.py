from django.urls import path
from .sub_views import PublicPlanListView

urlpatterns = [
    path("plan/", PublicPlanListView.as_view(), name="api-plan-list")
]

