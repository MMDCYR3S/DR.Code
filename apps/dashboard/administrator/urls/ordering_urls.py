from django.urls import path
from ..views import (
    # ===== Ordering ===== #
    OrderListView,
    OrderDetailView,
    OrderManageView,
    OrderDeleteView,
    DrugSearchAjaxView,

    # ===== Dynamic ===== #
    PreClinicalManageView,
    
    # ===== Emergency ===== #
    EmergencyDispositionManageView,

    # ===== Media ===== #
    OrderMediaManageView
)

app_name = 'ordering'

urlpatterns = [
    # ===== Read & Delete ===== #
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('order/<int:pk>', OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/delete/', OrderDeleteView.as_view(), name='order_delete'),

    # ===== Ordering ===== #
    path('orders/create/', OrderManageView.as_view(), name='order_create'),
    path('orders/<int:pk>/edit/', OrderManageView.as_view(), name='order_edit'),
    path('orders/drugs/search/', DrugSearchAjaxView.as_view(), name='drug_search_ajax'),

    # ===== Dynamic ===== #
    path('orders/<int:order_pk>/preclinical/', PreClinicalManageView.as_view(), name='preclinical'),

    # ===== Emergency ===== #
    path('orders/<int:order_pk>/emergency-disposition/', EmergencyDispositionManageView.as_view(),
         name='emergency_disposition'),

    # ===== Media ===== #
    path('orders/<int:order_pk>/media/', OrderMediaManageView.as_view(), name='order_media'),
]