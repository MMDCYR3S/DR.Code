from django.urls import path
from ..views import *

app_name = 'plans'

urlpatterns = [
    path('plan/', PlanListView.as_view(), name='plan_list'),
    path('plan/create/', PlanCreateView.as_view(), name='plan_create'),
    path('plan/<int:pk>/', PlanDetailView.as_view(), name='plan_detail'),
    path('plan/<int:pk>/update/', PlanUpdateView.as_view(), name='plan_update'),
    path('plan/<int:pk>/delete/', PlanDeleteView.as_view(), name='plan_delete'),
    
    # Membership URLs
    path('membership/create/', MembershipCreateView.as_view(), name='membership_create'),
    path('membership/<int:pk>/update/', MembershipUpdateView.as_view(), name='membership_update'),
    path('membership/<int:pk>/delete/', MembershipDeleteView.as_view(), name='membership_delete'),
]