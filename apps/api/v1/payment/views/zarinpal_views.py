from datetime import timedelta
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.views import View
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

import logging

logger = logging.getLogger(__name__)

User = get_user_model()

from apps.payment.models import Payment, PaymentStatus
from apps.payment.services import ZarinpalService
from ..serializers import PaymentCreateSerializer
from apps.subscriptions.models import Subscription, SubscriptionStatusChoicesModel, Plan

# ====== Payment Create View ====== #
class PaymentCreateView(CreateAPIView):
    """
    ایجاد درخواست پرداخت نهایی بر اساس اطلاعات خلاصه خرید.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentCreateSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_id = serializer.validated_data['plan_id']
        
        cache_key = f"purchase_summary:{request.user.id}:{plan_id}"
        purchase_data = cache.get(cache_key)
        
        if not purchase_data:
            return Response({
                'success': False,
                'error': 'جلسه خرید شما منقضی شده است. لطفاً مراحل را از ابتدا طی کنید.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        plan = get_object_or_404(Plan, id=plan_id)
        amount = purchase_data['original_price'] * 10
        discount_amount = purchase_data['discount_amount'] * 10
        final_amount = purchase_data['final_price'] * 10
            
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
            subscription=subscription,
            amount=amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            user_ip=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        zarinpal = ZarinpalService()
        callback_url = request.build_absolute_uri(
            reverse('payment:payment-callback')
        )
        
        result = zarinpal.create_payment_request(
            amount=int(final_amount),
            description=f"خرید اشتراک {plan.name}",
            callback_url=callback_url,
            metadata={'mobile': request.user.phone_number, 'email': request.user.email}
        )
        # ===== ایجاد درخواست پرداخت ===== #
        if result['success']:
            payment.authority = result['authority']
            payment.save()
            cache.delete(cache_key)
            logger.info(f"Payment created successfully: payment_id={payment.id}, user={request.user.id}")
            
            return Response({
                'success': True,
                'payment_id': payment.id,
                'payment_url': result['payment_url'],
            }, status=status.HTTP_201_CREATED)
        else:
            payment.delete()
            subscription.delete()
            logger.error(f"Payment creation failed: user={request.user.id}, error={result['error']}")
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

 
class PaymentVerifyView(APIView):
    authentication_classes = [] 
    permission_classes = []

    def get(self, request):
        authority = request.GET.get('Authority') or request.query_params.get('Authority')
        status_param = request.GET.get('Status') or request.query_params.get('Status')
        
        # تشخیص نوع درخواست
        is_api_request = 'application/json' in request.headers.get('Accept', '') or \
                         'application/json' in request.headers.get('Content-Type', '')

        # دیتای پیش‌فرض برای ارسال به فرانت (CamelCase برای هماهنگی با JS)
        context_data = {
            'loading': False,
            'success': False,
            'errorMessage': 'اطلاعات پرداخت یافت نشد.',
            'refId': '',       # اصلاح شد: refId برای نمایش در فرانت
            'paymentDate': '',
            'gateway': 'zarinpal'
        }

        try:
            if not authority:
                # اگر پارامتری نبود، فقط صفحه را رندر کن (حالت انتظار)
                return self._response(request, is_api_request, context_data)

            # 1. پیدا کردن پرداخت
            try:
                payment = Payment.objects.get(authority=authority)
            except Payment.DoesNotExist:
                raise ValueError('رکورد پرداخت یافت نشد.')

            # 2. اگر قبلاً تکمیل شده
            if payment.status == PaymentStatus.COMPLETED:
                context_data.update({
                    'success': True,
                    'refId': payment.ref_id,
                    'paymentDate': payment.paid_at.strftime('%Y-%m-%d %H:%M') if payment.paid_at else '',
                    'errorMessage': '',
                    'already_verified': True
                })
                return self._response(request, is_api_request, context_data)

            # 3. اگر کاربر لغو کرده
            if status_param != 'OK':
                payment.status = PaymentStatus.CANCELLED
                payment.save()
                raise ValueError('پرداخت توسط کاربر لغو شد.')

            # 4. درخواست به زرین‌پال
            zarinpal = ZarinpalService()
            verify_result = zarinpal.verify_payment(
                authority=authority,
                amount=int(payment.final_amount)
            )
            
            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(id=payment.id)
                
                if verify_result['success']:
                    payment.status = PaymentStatus.COMPLETED
                    payment.ref_id = verify_result['ref_id']
                    payment.paid_at = timezone.now()
                    payment.save()

                    # فعال‌سازی اشتراک
                    if payment.subscription:
                        sub = payment.subscription
                        # اینجا چون request.user ممکن است به خاطر سشن ست نشده باشد از payment.user استفاده میکنیم
                        active_subscription = self._get_active_subscription(payment.user)
                        
                        if active_subscription and active_subscription.id != sub.id:
                            self._extend_subscription(active_subscription, sub, payment)
                        else:
                            self._activate_subscription(sub)
                        
                        self._update_user_profile(payment.user, active_subscription or sub, payment)

                    context_data.update({
                        'success': True,
                        'refId': str(verify_result['ref_id']), # تبدیل به رشته برای اطمینان
                        'paymentDate': payment.paid_at.strftime('%Y-%m-%d %H:%M'),
                        'errorMessage': ''
                    })
                else:
                    payment.status = PaymentStatus.FAILED
                    payment.save()
                    if payment.subscription:
                        payment.subscription.status = SubscriptionStatusChoicesModel.canceled
                        payment.subscription.save()
                    raise ValueError(verify_result.get('error', 'تراکنش ناموفق بود'))

        except Exception as e:
            logger.error(f"Payment Verify Error: {str(e)}")
            context_data['errorMessage'] = str(e)
            
            if is_api_request:
                return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return self._response(request, is_api_request, context_data)

    def _response(self, request, is_api_request, data):
        if is_api_request:
            return Response({
                'success': data['success'],
                'data': {
                    'ref_id': data['refId'],
                    'created_at': data['paymentDate']
                },
                'message': 'عملیات موفق' if data['success'] else data['errorMessage']
            }, status=status.HTTP_200_OK if data['success'] else status.HTTP_400_BAD_REQUEST)
        else:
            # ارسال initial_data به تمپلیت HTML
            return render(request, 'payment/verify_payment.html', {'initial_data': data})

    # ================= Helper Methods =================
    def _get_active_subscription(self, user):
        now = timezone.now()
        return Subscription.objects.filter(
            user=user,
            status=SubscriptionStatusChoicesModel.active,
            end_date__gt=now
        ).order_by('-end_date').first()
    
    def _extend_subscription(self, active_subscription, new_subscription, payment):
        additional_days = new_subscription.plan.duration_days
        active_subscription.end_date = active_subscription.end_date + timedelta(days=additional_days)
        active_subscription.save()
        
        new_subscription.status = SubscriptionStatusChoicesModel.expired
        new_subscription.start_date = timezone.now()
        new_subscription.end_date = active_subscription.end_date
        new_subscription.save()
        
    def _activate_subscription(self, subscription):
        now = timezone.now()
        subscription.status = SubscriptionStatusChoicesModel.active
        subscription.start_date = now
        subscription.end_date = now + timedelta(days=subscription.plan.duration_days)
        subscription.save()

    def _update_user_profile(self, user, subscription, payment):
        try:
            profile = user.profile
            if profile.role != "admin":
                profile.role = 'premium'
            profile.subscription_end_date = subscription.end_date
            profile.save()
        except Exception as e:
            logger.error(f"Error updating profile for user {user.id}: {e}")
