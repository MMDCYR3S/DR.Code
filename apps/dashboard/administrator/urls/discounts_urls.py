from django.urls import path
from ..views import(
    DiscountUpdateView,
    DiscountCreateView,
    DiscountDeleteView,
    DiscountListView
)

app_name = 'orders'

urlpatterns = [
    path('discounts/', DiscountListView.as_view(), name='discount_list'),
    path('discounts/create/', DiscountCreateView.as_view(), name='discount_create'),
    path('discounts/<int:discount_id>/update/', DiscountUpdateView.as_view(), name='discount_update'),
    path('discounts/<int:discount_id>/delete/', DiscountDeleteView.as_view(), name='discount_delete'),
]
