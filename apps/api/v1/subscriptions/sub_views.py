from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.db.models import Prefetch

from rest_framework import generics, filters, permissions
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from drf_spectacular.utils import extend_schema_view, extend_schema
from django_filters.rest_framework import DjangoFilterBackend

from apps.subscriptions.models import Plan, Feature
from .sub_serializers import PlanPublicSerializer

# ========== PUBLIC PLAN LIST VIEW ========== #
@extend_schema_view(
    get=extend_schema(tags=['Order'], summary='دریافت لیست پلن‌های اشتراک'),
)
class PublicPlanListView(generics.ListAPIView):
    """
    API برای نمایش لیست پلن‌های فعال در صفحات عمومی
    """
    serializer_class = PlanPublicSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['membership__slug', 'tag']
    ordering_fields = ['duration_days', 'price']
    ordering = ['duration_days'] 
    
    def get_queryset(self):
        """
        دریافت پلن‌های فعال با بهینه‌سازی کوئری‌ها
        select_related برای Membership و prefetch_related برای Features
        """
        active_features_prefetch = Prefetch(
            'membership__features',
            queryset=Feature.objects.filter(is_active=True)
        )
        
        return Plan.objects.filter(
            is_active=True,
            membership__is_active=True
        ).select_related(
            'membership'
        ).prefetch_related(
            active_features_prefetch
        )

    @method_decorator(vary_on_headers('User-Agent'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        """اضافه کردن اطلاعات Meta به پاسخ"""
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
