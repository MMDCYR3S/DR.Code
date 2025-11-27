from django.urls import path
from ..views import analysis_views

app_name = 'analysis'

urlpatterns = [
    path('analysis/', analysis_views.AnalysisDashboardView.as_view(), name='analysis'),
    path('analysis/user-stats/', analysis_views.UserStatsDetailView.as_view(), name='user_stats'),
    path('analysis/payment-stats/', analysis_views.PaymentStatsDetailView.as_view(), name='payment_stats'),
    path('analysis/subscription-stats/', analysis_views.SubscriptionStatsDetailView.as_view(), name='subscription_stats'),
    path('analysis/chart-data/', analysis_views.ChartDataView.as_view(), name='chart_data'),
    path('api/analytics-data/', analysis_views.AnalyticsDataJsonView.as_view(), name='analytics_json_data'),
]