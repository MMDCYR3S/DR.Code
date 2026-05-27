from django.urls import path
from ..views import (
    # ===== Ordering ===== #
    OrderManageView,
    DrugSearchAjaxView,

    # ===== Dynamic ===== #
    PreClinicalManageView,
    
    # ===== Emergency ===== #
    EmergencyDispositionManageView
)

app_name = 'ordering'

urlpatterns = [
    # ===== Ordering ===== #
    path('orders/create/', OrderManageView.as_view(), name='order_create'),
    path('orders/<int:pk>/edit/', OrderManageView.as_view(), name='order_edit'),
    path('orders/drugs/search/', DrugSearchAjaxView.as_view(), name='drug_search_ajax'),

    # ===== Dynamic ===== #
    path('orders/<int:order_pk>/preclinical/', PreClinicalManageView.as_view(), name='preclinical'),

    # ===== Emergency ===== #
    path('orders/<int:order_pk>/emergency-disposition/',EmergencyDispositionManageView.as_view(),
     name='emergency_disposition'),
]