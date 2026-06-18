from django.urls import path
from . import views

app_name = 'ordering_api'

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order-list'),
    path('<slug:slug>/base/', views.OrderBaseView.as_view(), name='order-base'),
    path('<slug:slug>/sections/', views.OrderSectionsView.as_view(), name='order-sections'),
    path('<slug:slug>/disposition/', views.OrderDispositionView.as_view(), name='order-disposition'),
    path('<slug:slug>/dynamic-fields/', views.OrderDynamicFieldsView.as_view(), name='order-dynamic-fields'),
    path('<slug:slug>/media/', views.OrderMediaView.as_view(), name='order-media'),
]
