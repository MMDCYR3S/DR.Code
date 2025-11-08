from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from rest_framework import generics, filters, permissions
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from django_filters.rest_framework import DjangoFilterBackend

from apps.subscriptions.models import Plan
from .sub_serializers import PlanPublicSerializer

# ========== PUBLIC PLAN LIST VIEW ========== #
class PublicPlanListView(generics.ListAPIView):
    """
    API برای نمایش لیست پلن‌های فعال در صفحات عمومی
    
    Features:
    - فقط پلن‌های فعال نمایش داده می‌شود
    - کش کامل صفحه برای 15 دقیقه
    - Throttling برای محدودیت درخواست
    - فیلتر و جستجو
    - مرتب‌سازی بر اساس مدت زمان
    """
    serializer_class = PlanPublicSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['membership__slug']
    ordering_fields = ['duration_days', 'price']
    ordering = ['duration_days'] 
    
    def get_queryset(self):
        """فقط پلن‌های فعال از اشتراک‌های فعال"""
        return Plan.objects.filter(
            is_active=True,
            membership__is_active=True
        ).select_related('membership')

    @method_decorator(vary_on_headers('User-Agent'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        """Override برای اضافه کردن metadata مفید"""
        response = super().list(request, *args, **kwargs)
        
        response.data = {
            'results': response.data,
            'meta': {
                'total_plans': len(response.data),
                'price_range': self.get_price_range(),
            }
        }
        return response
    
    def get_price_range(self):
        """محدوده قیمت پلن‌ها (برای نمایش در UI)"""
        queryset = self.get_queryset()
        if queryset.exists():
            prices = queryset.values_list('price', flat=True)
            return {
                'min_price': f"{min(prices):,}",
                'max_price': f"{max(prices):,}",
            }
        return None
    
    
    