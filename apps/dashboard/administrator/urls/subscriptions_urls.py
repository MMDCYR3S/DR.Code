from django.urls import path
from ..views import (
    SubscriptionCreateView,
    SubscriptionUpdateView,
    SubscriptionDeleteView,
    SubscriptionExtendView,
    UserSubscriptionDetailView,
    GetAvailablePlansView
) 

app_name = 'subscriptions'

urlpatterns = [
    path('subscriptions/create/', 
         SubscriptionCreateView.as_view(), 
         name='subscription_create'),
    path('subscriptions/<int:pk>/edit/', 
         SubscriptionUpdateView.as_view(), 
         name='subscription_update'),
    path('subscriptions/<int:pk>/delete/', 
         SubscriptionDeleteView.as_view(), 
         name='subscription_delete'),
    path('subscriptions/<int:pk>/extend/', 
         SubscriptionExtendView.as_view(), 
         name='subscription_extend'),
    path('subscriptions/user/<int:user_id>/', 
         UserSubscriptionDetailView.as_view(), 
         name='user_subscriptions'),
    path('subscriptions/plans/', 
         GetAvailablePlansView.as_view(), 
         name='available_plans'),
]
