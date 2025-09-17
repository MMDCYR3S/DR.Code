from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.payment.models import Payment, PaymentStatus
from apps.payment.services import ZarinpalService
from .serializers import PaymentCreateSerializer, PaymentSerializer
from apps.subscriptions.models import Subscription, SubscriptionStatusChoicesModel, Plan

# ====== Payment Create View ====== #
class PaymentCreateView(APIView):
    """
    ایجاد درخواست پرداخت نهایی بر اساس اطلاعات خلاصه خرید.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
            
        plan_id = serializer.validated_data['plan_id']
        
        # === تغییر کلیدی: خواندن اطلاعات از کش === #
        cache_key = f"purchase_summary:{request.user.id}:{plan_id}"
        purchase_data = cache.get(cache_key)
        
        if not purchase_data:
            return Response({
                'success': False,
                'error': 'جلسه خرید شما منقضی شده است. لطفاً مراحل را از ابتدا طی کنید.'
            }, status=status.HTTP_400_BAD_REQUEST)

        plan = get_object_or_404(Plan, id=plan_id)

        # مقادیر را از داده‌های کش‌شده و اعتبارسنجی شده می‌خوانیم
        amount = purchase_data['original_price']
        discount_amount = purchase_data['discount_amount']
        final_amount = purchase_data['final_price']
        
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            payment_amount=final_amount,
            status=SubscriptionStatusChoicesModel.pending,
            start_date=timezone.now(),
            end_date=timezone.now()
        )

        payment = Payment.objects.create(
            user=request.user,
            subscription=subscription, # اتصال به اشتراک موقت
            amount=amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            user_ip=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        zarinpal = ZarinpalService()
        callback_url = request.build_absolute_uri(
            reverse('api:v1:payments:verify')
        )
        
        result = zarinpal.create_payment_request(
            amount=int(final_amount),
            description=f"خرید اشتراک {plan.name}",
            callback_url=callback_url,
            metadata={'mobile': request.user.phone_number, 'email': request.user.email}
        )
        
        if result['success']:
            payment.authority = result['authority']
            payment.save()

            cache.delete(cache_key)
            
            return Response({
                'success': True,
                'payment_id': payment.id,
                'payment_url': result['payment_url'],
            }, status=status.HTTP_201_CREATED)
        else:
            payment.delete()
            subscription.delete()
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    def get_client_ip(self, request):
        """دریافت IP کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
# ====== Payment Verify View ====== #
class PaymentVerifyView(APIView):
    """
    تایید پرداخت از زرین‌پال (Callback)
    """
    
    permission_classes = []
    
    def get(self, request):
        authority = request.GET.get('Authority')
        status_param = request.GET.get('Status')
        
        if not authority:
            return Response({
                'success': False,
                'error': 'کد رهگیری دریافت نشد'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            payment = get_object_or_404(Payment, authority=authority)
            
            if status_param != 'OK':
                # کاربر پرداخت را لغو کرده
                payment.status = PaymentStatus.CANCELLED
                payment.save()
                
                payment.subscription.status = SubscriptionStatusChoicesModel.canceled
                payment.subscription.save()
                
                return Response({
                    'success': False,
                    'error': 'پرداخت توسط کاربر لغو شد',
                    'payment_id': payment.id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # تایید پرداخت در زرین‌پال
            zarinpal = ZarinpalService()
            verify_result = zarinpal.verify_payment(
                authority=authority,
                amount=payment.final_amount
            )
            
            if verify_result['success']:
                # پرداخت موفق
                payment.status = PaymentStatus.COMPLETED
                payment.ref_id = verify_result['ref_id']
                payment.paid_at = timezone.now()
                payment.save()
                
                # فعال‌سازی اشتراک
                if payment.subscription:
                    sub=  payment.subscription
                    sub.status = SubscriptionStatusChoicesModel.active.value
                    sub.start_date = timezone.now()
                    sub.end_date = timezone.now() + timezone.timedelta(days=sub.plan.duration_days)
                    sub.save()
                
                return Response({
                    'success': True,
                    'message': 'پرداخت با موفقیت انجام شد',
                    'payment_id': payment.id,
                    'ref_id': verify_result['ref_id']
                }, status=status.HTTP_200_OK)
            else:
                # پرداخت ناموفق
                payment.status = PaymentStatus.FAILED
                payment.save()
                
                if payment.subscription:
                    payment.subscription.status = SubscriptionStatusChoicesModel.canceled
                    payment.subscription.save()
                
                return Response({
                    'success': False,
                    'error': verify_result['error'],
                    'payment_id': payment.id
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'خطا در تایید پرداخت: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            