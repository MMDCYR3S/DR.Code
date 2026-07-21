from django.urls import path
from ..views import *

app_name = 'plans'

urlpatterns = [
    # ===== Membership ===== #
    path('memberships/', PlanListView.as_view(), name='plan_list'),
    path('memberships/<int:pk>/', MembershipDetailView.as_view(), name='membership_detail'),
    path('memberships/create/', MembershipCreateView.as_view(), name='membership_create'),
    path('memberships/<int:pk>/update/', MembershipUpdateView.as_view(), name='membership_update'),
    path('memberships/<int:pk>/delete/', MembershipDeleteView.as_view(), name='membership_delete'),

    # ===== Plan ===== #
    path('plan/create/', PlanCreateView.as_view(), name='plan_create'),
    path('plan/<int:pk>/detail/', PlanDetailView.as_view(), name='plan_detail'),
    path('plan/<int:pk>/update/', PlanUpdateView.as_view(), name='plan_update'),
    path('plan/<int:pk>/delete/', PlanDeleteView.as_view(), name='plan_delete'),

    # ===== Feature ===== #
    path('features/create/', FeatureCreateView.as_view(), name='feature_create'),
    path('features/<int:pk>/detail/', FeatureDetailView.as_view(), name='feature_detail'),
    path('features/<int:pk>/update/', FeatureUpdateView.as_view(), name='feature_update'),
    path('features/<int:pk>/delete/', FeatureDeleteView.as_view(), name='feature_delete'),
]