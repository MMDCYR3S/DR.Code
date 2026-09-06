from django.urls import path
from ..views import RecentPrescriptionsAPIView, RecentTutorialAPIView, RecentOrdersAPIView

urlpatterns = [
    path('prescriptions/recent/', RecentPrescriptionsAPIView.as_view(), name='recent-prescriptions'),
    path('tutorials/recent/', RecentTutorialAPIView.as_view(), name='recent-tutorials'),
    path('orders/recent/', RecentOrdersAPIView.as_view(), name='recent-orders'),
]