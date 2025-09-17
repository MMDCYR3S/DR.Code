from django.urls import path
from .discount_views import (
    PurchaseDetailView,
)

app_name = 'order'

urlpatterns = [
    path('purchase/<int:plan_id>/', PurchaseDetailView.as_view(), name='purchase-detail'),
]
