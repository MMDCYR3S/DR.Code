from django.urls import path
from ..views import (
    # ===== Ordering ===== #
    OrderManageView,
    DrugSearchAjaxView
)

app_name = 'ordering'

urlpatterns = [
    # ===== Ordering ===== #
    path('orders/create/', OrderManageView.as_view(), name='order_create'),
    path('orders/<int:pk>/edit/', OrderManageView.as_view(), name='order_edit'),
    path('orders/drugs/search/', DrugSearchAjaxView.as_view(), name='drug_search_ajax'),
]