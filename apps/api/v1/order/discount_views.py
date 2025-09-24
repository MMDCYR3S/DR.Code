from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from apps.subscriptions.models import Plan
from apps.accounts.permissions import IsTokenJtiActive
from .discount_serializer import PurchaseDetailSerializer, PurchaseSummarySerializer

# ========== PURCHASE DETAIL VIEW ========== #
class PurchaseDetailView(generics.RetrieveUpdateAPIView):
    """
    نمایش جزئیات خرید پلن با امکان اعمال کدهای تخفیف
    GET: دریافت اطلاعات اولیه پلن
    POST: محاسبه قیمت با اعمال کدهای تخفیف
    """
    permission_classes = [IsAuthenticated, IsTokenJtiActive]
    throttle_classes = [UserRateThrottle]
    serializer_class = PurchaseDetailSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'plan_id'
    
    def get_queryset(self):
        """دریافت پلن‌های فعال"""
        return Plan.objects.select_related('membership').filter(is_active=True)
    
    @method_decorator(cache_page(60 * 5))
    def get(self, request, plan_id):
        """
        دریافت اطلاعات اولیه پلن برای خرید
        """
        plan = get_object_or_404(
            self.get_queryset(),
            id=plan_id
        )
        
        # آماده‌سازی داده‌های اولیه
        initial_data = {
            'plan_id': plan.id,
            'plan_name': plan.name,
            'plan_duration_days': plan.duration_days,
            'membership_name': plan.membership.title,
            'original_price': plan.price,
            'discount_amount': 0,
            'discount_percent': 0,
            'final_price': plan.price,
            'savings': 0,
            'is_discounted': False,
            'discount_code': '',
            'referral_code': ''
        }
        
        # سریالایز کردن داده‌ها
        summary_serializer = PurchaseSummarySerializer(initial_data)
        
        return Response({
            'success': True,
            'data': summary_serializer.data,
            'message': 'اطلاعات پلن با موفقیت دریافت شد.'
        }, status=status.HTTP_200_OK)

    def post(self, request, plan_id):
        """
        محاسبه قیمت نهایی با اعمال کدهای تخفیف
        """
        # بررسی وجود پلن
        plan = self.get_object()
        
        # آماده‌سازی داده‌ها
        data = request.data.copy()
        data['plan_id'] = plan_id
        
        # اعتبارسنجی
        serializer = self.get_serializer(
            data=data,
            context={'request': request}
        )
        
        serializer.is_valid(raise_exception=True)
        
        # آماده‌سازی داده‌ها برای پاسخ
        validated_data = serializer.validated_data
        summary_serializer = PurchaseSummarySerializer(validated_data)
        
        cache_key = f"purchase_summary:{request.user.id}:{plan_id}"
        cache.set(cache_key, validated_data, timeout=60 * 15)
        
        return Response({
            'success': True,
            'data': summary_serializer.data,
            'cache_key': cache_key,
            'message': 'محاسبات با موفقیت انجام شد.'
        }, status=status.HTTP_200_OK)