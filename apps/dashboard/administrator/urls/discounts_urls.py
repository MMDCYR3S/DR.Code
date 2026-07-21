from django.urls import path
from ..views import (
    DiscountListView,
    DiscountCreateView,
    DiscountUpdateView,
    DiscountDeleteView,
)

app_name = 'orders'

urlpatterns = [
    path('discounts/', DiscountListView.as_view(), name='discount_list'),
    path('discounts/create/', DiscountCreateView.as_view(), name='discount_create'),
    path('discounts/<int:pk>/update/', DiscountUpdateView.as_view(), name='discount_update'),
    path('discounts/<int:pk>/delete/', DiscountDeleteView.as_view(), name='discount_delete'),
]