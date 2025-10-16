from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

from apps.payment.models import Payment, PaymentStatus
from apps.payment.services import ZarinpalService
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
        
        # === تغییر کلیدی: خواندن اطلاعات از کش === #
        cache_key = f"purchase_summary:{request.user.id}:{plan_id}"
        purchase_data = cache.get(cache_key)
        
        
        if not purchase_data:
            return Response({
                'success': False,
                'error': 'جلسه خرید شما منقضی شده است. لطفاً مراحل را از ابتدا طی کنید.'
            }, status=status.HTTP_400_BAD_REQUEST)

        plan = get_object_or_404(Plan, id=plan_id)
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
            reverse('payment:payment-callback')
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
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        دریافت داده‌ها از body و تایید پرداخت
        """
        authority = request.data.get('authority')
        status_param = request.data.get('status')
        
        if not authority:
            return Response({
                'success': False,
                'error': 'کد رهگیری دریافت نشد'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            payment = get_object_or_404(Payment, authority=authority)
            
            # بررسی مالکیت
            if payment.user != request.user:
                return Response({
                    'success': False,
                    'error': 'دسترسی غیرمجاز'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # جلوگیری از تایید مکرر
            if payment.status == PaymentStatus.COMPLETED:
                return Response({
                    'success': True,
                    'message': 'این پرداخت قبلاً تایید شده است',
                    'payment_id': payment.id,
                    'ref_id': payment.ref_id
                }, status=status.HTTP_200_OK)
            
            # بررسی لغو شدن
            if status_param != 'OK':
                with transaction.atomic():
                    payment.status = PaymentStatus.CANCELLED
                    payment.save()
                    
                    if payment.subscription:
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
                amount=int(payment.final_amount)
            )
            
            if verify_result['success']:
                with transaction.atomic():
                    # پرداخت موفق
                    payment.status = PaymentStatus.COMPLETED
                    payment.ref_id = verify_result['ref_id']
                    payment.paid_at = timezone.now()
                    payment.save()
                    
                    # ✅ فعال‌سازی یا تمدید اشتراک
                    if payment.subscription:
                        sub = payment.subscription
                        
                        # 🔍 بررسی اشتراک فعال قبلی
                        active_subscription = self._get_active_subscription(request.user)
                        
                        if active_subscription and active_subscription.id != sub.id:
                            # ✅ کاربر اشتراک فعال دیگری دارد - تمدید می‌کنیم
                            self._extend_subscription(
                                active_subscription=active_subscription,
                                new_subscription=sub,
                                payment=payment
                            )
                        else:
                            # ✅ اولین اشتراک یا فعال‌سازی همین اشتراک
                            self._activate_subscription(sub)
                        
                        # به‌روزرسانی پروفایل
                        self._update_user_profile(
                            user=request.user,
                            subscription=active_subscription or sub,
                            payment=payment
                        )
                                    
                return Response({
                    'success': True,
                    'message': 'پرداخت با موفقیت انجام شد',
                    'payment_id': payment.id,
                    'ref_id': verify_result['ref_id']
                }, status=status.HTTP_200_OK)
            else:
                with transaction.atomic():
                    payment.status = PaymentStatus.FAILED
                    payment.save()
                    
                    if payment.subscription:
                        payment.subscription.status = SubscriptionStatusChoicesModel.canceled
                        payment.subscription.save()
                
                return Response({
                    'success': False,
                    'error': verify_result.get('error', 'خطای نامشخص در تایید پرداخت'),
                    'payment_id': payment.id
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'خطا در تایید پرداخت: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ====== Helper Methods ====== #
    
    def _get_active_subscription(self, user):
        """
        پیدا کردن اشتراک فعال کاربر
        """
        now = timezone.now()
        
        # اشتراکی که فعال است و تاریخ انقضایش نگذشته
        return Subscription.objects.filter(
            user=user,
            status=SubscriptionStatusChoicesModel.active,
            end_date__gt=now  # تاریخ انقضا در آینده است
        ).order_by('-end_date').first()
    
    def _extend_subscription(self, active_subscription, new_subscription, payment):
        """
        تمدید اشتراک فعال با اضافه کردن زمان اشتراک جدید
        
        Args:
            active_subscription: اشتراک فعلی فعال
            new_subscription: اشتراک جدید خریداری شده
            payment: پرداخت جدید
        """
        # محاسبه روزهای جدید
        additional_days = new_subscription.plan.duration_days
        
        # اضافه کردن به تاریخ انقضای فعلی
        active_subscription.end_date = active_subscription.end_date + timedelta(days=additional_days)
        active_subscription.save()
        
        # ✅ اشتراک جدید را به عنوان "merged" علامت‌گذاری می‌کنیم
        new_subscription.status = SubscriptionStatusChoicesModel.expired  # یا یک status جدید مثل MERGED
        new_subscription.start_date = timezone.now()
        new_subscription.end_date = active_subscription.end_date  # همان تاریخ نهایی
        new_subscription.save()
        
        # ثبت log
        print(f"✅ Subscription extended: User {active_subscription.user.id} | "
              f"Added {additional_days} days | New end date: {active_subscription.end_date}")
    
    def _activate_subscription(self, subscription):
        """
        فعال‌سازی اشتراک جدید
        
        Args:
            subscription: اشتراک جدید
        """
        now = timezone.now()
        
        subscription.status = SubscriptionStatusChoicesModel.active
        subscription.start_date = now
        subscription.end_date = now + timedelta(days=subscription.plan.duration_days)
        subscription.save()
        
        print(f"✅ Subscription activated: User {subscription.user.id} | "
              f"End date: {subscription.end_date}")
    
    def _update_user_profile(self, user, subscription, payment):
        """
        به‌روزرسانی پروفایل کاربر
        
        Args:
            user: کاربر
            subscription: اشتراک فعال
            payment: پرداخت
        """
        profile = user.profile
        profile.role = 'premium'
        profile.subscription_end_date = subscription.end_date
        
        # بررسی کد معرف از کش
        ref_cache_key = f"payment_referral:{payment.id}"
        referral_code = cache.get(ref_cache_key)
        
        if referral_code and not profile.referred_by:  # فقط اگر قبلاً معرف نداشته
            try:
                referrer_user = User.objects.get(profile__referral_code=referral_code)
                profile.referred_by = referrer_user
                cache.delete(ref_cache_key)
                
                print(f"✅ Referral applied: User {user.id} referred by {referrer_user.id}")
            except User.DoesNotExist:
                pass
        
        profile.save()
        
        print(f"✅ Profile updated: User {user.id} | Role: {profile.role} | "
              f"End date: {profile.subscription_end_date}")
