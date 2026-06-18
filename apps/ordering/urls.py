from django.urls import path
from .views import (
    OrderDetailView,
    OrderListView
)

app_name = 'ordering'

urlpatterns = [
    path('', OrderListView.as_view(), name='order_list'),
    path('<slug:slug>/', OrderDetailView.as_view(), name='order_detail'),
]
