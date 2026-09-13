from datetime import timedelta
from django.db.models.aggregates import Max
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema

from django.views import View
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

import logging

logger = logging.getLogger("zarinpal")

User = get_user_model()

from apps.payment.models import Payment, PaymentStatus
from apps.payment.services import ZarinpalService
from ..serializers import PaymentCreateSerializer
from apps.subscriptions.models import Subscription, SubscriptionStatusChoicesModel, Plan

# ====== Payment Create View ====== #
@extend_schema_view(
    get=extend_schema(tags=['Payment'], summary='درگاه پرداخت و عملیات آن'),
    post=extend_schema(tags=["Payment"]),
)
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
        callback_url = settings.ZARINPAL_CONFIG.get(
            'CALLBACK_URL', 
            'https://drcode-med.ir/payment/status/'
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

@extend_schema_view(
    get=extend_schema(tags=['Payment'], summary='درگاه پرداخت و عملیات آن'),
    post=extend_schema(tags=["Payment"]),
)
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
                        membership_id = sub.plan.membership_id
                        now = timezone.now()

                        # ⬅️ قفل کردن اشتراک فعال هم‌نوع برای جلوگیری از race condition
                        active_subscription = (
                            Subscription.objects
                            .select_for_update()
                            .filter(
                                user=payment.user,
                                status=SubscriptionStatusChoicesModel.active.value,
                                end_date__gt=now,
                                plan__membership_id=membership_id,
                            )
                            .exclude(id=sub.id)
                            .order_by('-end_date')
                            .first()
                        )

                        if active_subscription:
                            self._extend_subscription(active_subscription, sub)
                        else:
                            self._activate_subscription(sub)

                        self._update_user_profile(payment.user)
                        
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
            logger.error(f"Payment Verify Error: {str(e)}", exc_info=True)
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

    def _get_active_subscription_for_membership(self, user, membership_id):
        """
        اشتراک فعال کاربر مخصوص یک membership مشخص.
        این کلید اصلی حل مشکل است.
        """
        now = timezone.now()
        return Subscription.objects.filter(
            user=user,
            status=SubscriptionStatusChoicesModel.active,
            end_date__gt=now,
            plan__membership_id=membership_id,
        ).order_by('-end_date').first()
    
    def _extend_subscription(self, active_subscription, new_subscription):
        """
        فقط اشتراک فعال همون membership رو تمدید می‌کنه.
        اشتراک جدید (placeholder) رو به حالت expired می‌بره چون فقط برای ثبت تراکنش ساخته شده.
        """
        additional_days = new_subscription.plan.duration_days
        new_end = active_subscription.end_date + timedelta(days=additional_days)

        active_subscription.end_date = new_end
        active_subscription.save(update_fields=['end_date'])

        # placeholder جدید رو می‌بندیم، ولی به عنوان رکورد تراکنش باقی می‌مونه
        new_subscription.status = SubscriptionStatusChoicesModel.expired
        new_subscription.start_date = active_subscription.start_date
        new_subscription.end_date = new_end
        new_subscription.save(update_fields=['status', 'start_date', 'end_date'])
        
    def _activate_subscription(self, subscription):
        now = timezone.now()
        subscription.status = SubscriptionStatusChoicesModel.active
        subscription.start_date = now
        subscription.end_date = now + timedelta(days=subscription.plan.duration_days)
        subscription.save(update_fields=['status', 'start_date', 'end_date'])

    def _update_user_profile(self, user):
        """
        پروفایل باید بر اساس «دورترین» انقضای اشتراک‌های فعال آپدیت بشه.
        - اگر حداقل یک اشتراک فعال هست → premium
        - اگر هیچ اشتراک فعالی نیست → regular و پاک کردن تاریخ انقضا
        """
        try:
            profile = user.profile

            # ادمین همیشه ادمین می‌مونه
            if profile.role == 'admin':
                return

            now = timezone.now()
            max_end = Subscription.objects.filter(
                user=user,
                status=SubscriptionStatusChoicesModel.active.value,
                end_date__gt=now,
            ).aggregate(m=Max('end_date'))['m']

            if max_end:
                profile.role = 'premium'
                profile.subscription_end_date = max_end
            else:
                profile.role = 'regular'
                profile.subscription_end_date = None

            profile.save(update_fields=['role', 'subscription_end_date'])
            logger.info(
                f"Profile synced for user {user.id}: "
                f"role={profile.role}, end={profile.subscription_end_date}"
            )
        except Exception as e:
            # ⚠️ exc_info=True تا traceback کامل لاگ بشه — دفعه بعد راحت‌تر پیداش می‌کنی
            logger.error(f"Error updating profile for user {user.id}: {e}", exc_info=True)