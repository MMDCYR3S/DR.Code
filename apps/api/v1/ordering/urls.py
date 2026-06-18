from django.urls import path
from . import views

app_name = 'ordering_api'

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order-list'),
    path('<int:pk>/base/', views.OrderBaseView.as_view(), name='order-base'),
    path('<int:pk>/sections/', views.OrderSectionsView.as_view(), name='order-sections'),
    path('<int:pk>/disposition/', views.OrderDispositionView.as_view(), name='order-disposition'),
    path('<int:pk>/dynamic-fields/', views.OrderDynamicFieldsView.as_view(), name='order-dynamic-fields'),
    path('<int:pk>/media/', views.OrderMediaView.as_view(), name='order-media'),
]
