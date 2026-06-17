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
    path('membership/<int:pk>/', MembershipDetailView.as_view(), name='membership_detail'),
    path('membership/<int:pk>/update/', MembershipUpdateView.as_view(), name='membership_update'),
    path('membership/<int:pk>/delete/', MembershipDeleteView.as_view(), name='membership_delete'),
    
    # Feature URLs  ← این‌ها رو اضافه کن
    path('features/create/', FeatureCreateView.as_view(), name='feature_create'),
    path('features/<int:pk>/detail/', FeatureDetailView.as_view(), name='feature_detail'),
    path('features/<int:pk>/update/', FeatureUpdateView.as_view(), name='feature_update'),
    path('features/<int:pk>/delete/', FeatureDeleteView.as_view(), name='feature_delete'),
]