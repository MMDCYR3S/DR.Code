from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
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
from apps.order.models import DiscountCode
from ..serializers import PaymentCreateSerializer, PaymentSerializer
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


# ====== Payment Verify View ====== #
class PaymentVerifyView(APIView):
    """
    تایید پرداخت از زرین‌پال (Callback)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        دریافت داده‌ها از URL (Query Params) و تایید پرداخت
        """
        authority = request.query_params.get('Authority') or request.query_params.get('authority')
        status_param = request.query_params.get('Status') or request.query_params.get('status')
        
        if not authority:
            return Response({
                'success': False,
                'error': 'کد رهگیری (Authority) در آدرس بازگشتی یافت نشد.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # ===== تنظیمات یکپارچه ===== #
            with transaction.atomic():
                
                # ===== دریافت رکورد پرداخت ===== #
                payment = get_object_or_404(
                    Payment.objects.select_for_update(), 
                    authority=authority
                )
                
                # ===== بررسی کاربر ===== #
                if payment.user != request.user:
                    logger.warning(f"Unauthorized verify attempt: payment={payment.id}, user={request.user.id}")
                    return Response({
                        'success': False,
                        'error': 'دسترسی غیرمجاز به این تراکنش'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                
                if payment.status == PaymentStatus.COMPLETED:
                    logger.info(f"Payment already completed: payment={payment.id}")
                    return Response({
                        'success': True,
                        'message': 'این پرداخت قبلاً تایید شده است',
                        'payment_id': payment.id,
                        'ref_id': payment.ref_id,
                        'already_verified': True
                    }, status=status.HTTP_200_OK)
                
                # ===== بررسی وضعیت پرداخت ===== #
                if status_param != 'OK':
                    payment.status = PaymentStatus.CANCELLED
                    payment.save()
                    
                    if payment.subscription:
                        payment.subscription.status = SubscriptionStatusChoicesModel.canceled
                        payment.subscription.save()
                
                    logger.info(f"Payment cancelled by user: payment={payment.id}")
                    return Response({
                        'success': False,
                        'error': 'پرداخت توسط کاربر لغو شد',
                        'payment_id': payment.id
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                zarinpal = ZarinpalService()
                verify_result = zarinpal.verify_payment(
                    authority=authority,
                    amount=int(payment.final_amount)
                )
                
                if verify_result['success']:
                    
                    payment.status = PaymentStatus.COMPLETED
                    payment.ref_id = verify_result['ref_id']
                    payment.paid_at = timezone.now()
                    payment.save()
                    
                    # ===== اگر اشتراک بود ===== #
                    if payment.subscription:
                        sub = payment.subscription
                        
                        # ===== اشتراک ها فعال مربوط به کاربر ===== #
                        active_subscription = self._get_active_subscription(request.user)
                        
                        # ===== اشتراک فعال ===== #
                        if active_subscription and active_subscription.id != sub.id:
                            self._extend_subscription(active_subscription, sub, payment)
                        else:
                            self._activate_subscription(sub)
                        # ===== به روز کردن پروفایل کاربر ===== #
                        self._update_user_profile(request.user, active_subscription or sub, payment)
                
                    logger.info(f"Payment verified successfully: RefID={verify_result['ref_id']}")
                                      
                    return Response({
                        'success': True,
                        'message': 'پرداخت با موفقیت انجام شد',
                        'payment_id': payment.id,
                        'ref_id': verify_result['ref_id'],
                        'already_verified': False
                    }, status=status.HTTP_200_OK)
                
                else:
                    # ===== پرداخت ناموفق ===== #
                    payment.status = PaymentStatus.FAILED
                    payment.save()
                    
                    # ===== بازگشت اشتراک ===== #
                    if payment.subscription:
                        payment.subscription.status = SubscriptionStatusChoicesModel.canceled
                        payment.subscription.save()
                
                    logger.error(f"Payment verification failed: payment={payment.id}, error={verify_result.get('error')}")
                    
                    return Response({
                        'success': False,
                        'error': verify_result.get('error', 'خطای نامشخص در تایید پرداخت'),
                        'payment_id': payment.id
                    }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.exception(f"Exception in PaymentVerifyView: {e}")
            return Response({
                'success': False,
                'error': 'خطای داخلی سرور هنگام تایید پرداخت'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ====== Helper Methods (بدون تغییر) ====== #
    
    def _get_active_subscription(self, user):
        """پیدا کردن اشتراک فعال کاربر"""
        now = timezone.now()
        return Subscription.objects.filter(
            user=user,
            status=SubscriptionStatusChoicesModel.active,
            end_date__gt=now
        ).order_by('-end_date').first()
    
    def _extend_subscription(self, active_subscription, new_subscription, payment):
        """تمدید اشتراک فعال"""
        additional_days = new_subscription.plan.duration_days
        active_subscription.end_date = active_subscription.end_date + timedelta(days=additional_days)
        active_subscription.save()
        
        new_subscription.status = SubscriptionStatusChoicesModel.expired
        new_subscription.start_date = timezone.now()
        new_subscription.end_date = active_subscription.end_date
        new_subscription.save()
        
        logger.info(f"Subscription extended: user={active_subscription.user.id}, "
                    f"added_days={additional_days}, new_end={active_subscription.end_date}")
    
    def _activate_subscription(self, subscription):
        """فعال‌سازی اشتراک جدید"""
        now = timezone.now()
        subscription.status = SubscriptionStatusChoicesModel.active
        subscription.start_date = now
        subscription.end_date = now + timedelta(days=subscription.plan.duration_days)
        subscription.save()
        
        logger.info(f"Subscription activated: user={subscription.user.id}, "
                    f"end_date={subscription.end_date}")
    
    def _update_user_profile(self, user, subscription, payment):
        """به‌روزرسانی پروفایل کاربر"""
        profile = user.profile
        if profile.role != "admin":
            profile.role = 'premium'
        profile.subscription_end_date = subscription.end_date
        
        profile.save()
        