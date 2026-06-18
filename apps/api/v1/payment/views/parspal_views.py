import uuid
import json
import logging
import requests
import random

from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.payment.models import Payment, PaymentStatus, PaymentGateway
from apps.subscriptions.models import Subscription, SubscriptionStatusChoicesModel, Plan
from ..serializers import PaymentCreateSerializer

logger = logging.getLogger(__name__)

# ======= PARSPAL SETTINGS ======= #
PARSPAL_API_KEY = settings.PARSPAL_CONFIG['API_KEY']
PARSPAL_CALLBACK_URL = settings.PARSPAL_CONFIG['CALLBACK_URL']
PARSPAL_SANDBOX = settings.PARSPAL_CONFIG['SANDBOX']
BASE_URL = "https://sandbox.api.parspal.com/v1/payment" if PARSPAL_SANDBOX else "https://api.parspal.com/v1/payment"

# ========= GENERATE ORDER ID ========= #
def generate_order_id(plan_id, user_id):
    """ساخت order_id بر اساس plan_id، user.id و کد تصادفی"""
    rand_code = random.randint(1000, 9999)
    return f"{plan_id}-{user_id}-{rand_code}"

# ======= تابع کمکی تبدیل کش به JSON آماده ارسال ======= #
def prepare_cached_payment_data(cached_data, plan_id, user):
    """ساخت payload نهایی پارس‌پال از داده‌های کش‌شده"""
    if not isinstance(cached_data, dict):
        cached_data = {}

    pricing_info = cached_data.get("pricing_info", {})
    final_price = pricing_info.get("final_price") or cached_data.get("final_price") or 0

    try:
        final_price = int(final_price)
    except Exception:
        final_price = 0

    order_id = generate_order_id(plan_id, user.id)

    return {
        "amount": int(final_price) * 10,
        "return_url": PARSPAL_CALLBACK_URL,
        "reserve_id": str(uuid.uuid4()),
        "order_id": order_id,
        "payer": {
            "name": cached_data.get("payer_name", user.get_full_name() or user.username),
            "mobile": cached_data.get("payer_mobile", ""),
            "email": cached_data.get("payer_email", ""),
        },
        "description": cached_data.get("description", f"پرداخت اشتراک پلن {plan_id} توسط {user.username}"),
        "default_psp": None
    }


# ======= PARSPAL PAYMENT REQUEST VIEW ======= #
@extend_schema_view(
    get=extend_schema(tags=['Payment'], summary='درگاه پرداخت و عملیات آن'),
    post=extend_schema(tags=["Payment"]),
)
class ParspalPaymentRequestView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentCreateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        plan_id = serializer.validated_data['plan_id']
        plan = get_object_or_404(Plan, id=plan_id)

        cache_key = f"purchase_summary:{request.user.id}:{plan_id}"
        cached_data = cache.get(cache_key)

        if not cached_data:
            return Response({
                "success": False,
                "message": "داده‌ای برای این پلن در کش یافت نشد."
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = prepare_cached_payment_data(cached_data, plan_id, request.user)
        logger.info(f"Payload نهایی پارس‌پال: {json.dumps(payload, ensure_ascii=False)}")

        headers = {
            "ApiKey": PARSPAL_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            # ایجاد اشتراک اولیه
            subscription = Subscription.objects.create(
                user=request.user,
                plan=plan,
                payment_amount=payload["amount"],
                status=SubscriptionStatusChoicesModel.pending,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=plan.duration_days)
            )

            # ایجاد رکورد پرداخت
            payment = Payment.objects.create(
                user=request.user,
                subscription=subscription,
                amount=payload["amount"],
                discount_amount=cached_data.get("discount_amount", 0),
                final_amount=payload["amount"],
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                authority=payload["order_id"],
                gateway=PaymentGateway.PARSPAL
            )

            response = requests.post(f"{BASE_URL}/request", json=payload, headers=headers, timeout=10)
            logger.info(f"Parspal Response [{response.status_code}]: {response.text}")

            if response.status_code in [200, 201]:
                data = response.json()
                cache.set(f"parspal_payment:{payload['order_id']}", data, timeout=900)

                return Response({
                    "success": True,
                    "message": "درخواست پرداخت با موفقیت ثبت شد.",
                    "data": {
                        "order_id": payload["order_id"],
                        "amount": payload["amount"],
                        "redirect_url": "http://localhost:8000/payment/status/",
                        "payment_info": data
                    }
                }, status=status.HTTP_200_OK)

            return Response({
                "success": False,
                "message": "درخواست پرداخت ناموفق بود.",
                "status_code": response.status_code,
                "response": response.text
            }, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.Timeout:
            return Response({
                "success": False,
                "message": "درخواست به پارس‌پال بیش از حد طول کشید."
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)

        except requests.exceptions.RequestException as e:
            logger.error(f"خطای ارتباط با پارس‌پال: {str(e)}")
            return Response({
                "success": False,
                "message": "خطا در اتصال به درگاه پارس‌پال.",
                "error": str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)


# ======= PARSPAL CALLBACK VIEW (دریافت POST از پارس‌پال) ======= #
@extend_schema_view(
    get=extend_schema(tags=['Payment'], summary='درگاه پرداخت و عملیات آن'),
    post=extend_schema(tags=["Payment"]),
)
@method_decorator(csrf_exempt, name='dispatch')
class ParspalCallbackView(APIView):
    """
    این view داده‌های POST شده از پارس‌پال را دریافت می‌کند
    و کاربر را به صفحه verify هدایت می‌کند
    """
    permission_classes = []

    def post(self, request):
        status_code = request.POST.get('status') or request.data.get('status')
        receipt_number = request.POST.get('receipt_number') or request.data.get('receipt_number')
        payment_id = request.POST.get('payment_id') or request.data.get('payment_id')
        reserve_id = request.POST.get('reserve_id') or request.data.get('reserve_id')
        order_id = request.POST.get('order_id') or request.data.get('order_id')

        logger.info(f"[PARSPAL_CALLBACK] Received: status={status_code}, receipt={receipt_number}, order_id={order_id}")

        # ذخیره موقت در کش
        if order_id:
            cache_key = f"parspal_callback:{order_id}"
            cache.set(cache_key, {
                'status': status_code,
                'receipt_number': receipt_number,
                'payment_id': payment_id,
                'reserve_id': reserve_id,
                'order_id': order_id
            }, timeout=600)

        # ریدایرکت به صفحه status
        redirect_url = f"/payment/status/?gateway=parspal&order_id={order_id}&status={status_code}"
        if receipt_number:
            redirect_url += f"&receipt={receipt_number}"

        return redirect(redirect_url)

    def get(self, request):
        return Response({
            "message": "این آدرس فقط برای callback پارس‌پال است"
        }, status=status.HTTP_400_BAD_REQUEST)


# ======= PARSPAL VERIFY VIEW (اصلاح شده با چک کردن وضعیت قبلی) ======= #
@extend_schema_view(
    get=extend_schema(tags=['Payment'], summary='درگاه پرداخت و عملیات آن'),
    post=extend_schema(tags=["Payment"]),
)
class ParspalVerifyView(APIView):
    """تأیید پرداخت با استفاده از داده‌های callback"""
    permission_classes = [AllowAny]

    def post(self, request):
        order_id = request.data.get("order_id")

        if not order_id:
            return Response({
                "success": False,
                "message": "order_id ارسال نشده است."
            }, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"[PARSPAL_VERIFY] Starting verification for order_id: {order_id}")

        # 1️⃣ یافتن پرداخت
        try:
            payment = Payment.objects.select_related(
                'subscription',
                'subscription__plan',
                'user'
            ).get(authority=order_id)
            logger.info(f"[PARSPAL_VERIFY] Payment found: ID={payment.id}, Status={payment.status}")
        except Payment.DoesNotExist:
            logger.error(f"[PARSPAL_VERIFY] Payment not found for order_id: {order_id}")
            return Response({
                "success": False,
                "message": "تراکنش مورد نظر یافت نشد."
            }, status=status.HTTP_404_NOT_FOUND)

        # 2️⃣ بررسی اینکه قبلاً verify شده یا نه
        if payment.status == PaymentStatus.COMPLETED:
            logger.warning(f"[PARSPAL_VERIFY] Payment already verified: ID={payment.id}")
            
            # اطلاعات اشتراک رو برمی‌گردونیم (بدون Verify دوباره)
            return Response({
                "success": True,
                "message": "این تراکنش قبلاً تأیید شده است.",
                "data": {
                    "amount": str(payment.amount),
                    "receipt_number": payment.ref_id,
                    "order_id": order_id,
                    "subscription_start": payment.subscription.start_date.isoformat(),
                    "subscription_end": payment.subscription.end_date.isoformat(),
                    "already_verified": True
                }
            }, status=status.HTTP_200_OK)

        # 3️⃣ دریافت داده‌های callback از کش
        cache_key = f"parspal_callback:{order_id}"
        callback_data = cache.get(cache_key)

        if not callback_data:
            logger.warning(f"[PARSPAL_VERIFY] No callback data found for order_id: {order_id}")
            return Response({
                "success": False,
                "message": "داده‌های callback یافت نشد. لطفاً دوباره تلاش کنید."
            }, status=status.HTTP_400_BAD_REQUEST)

        status_code = callback_data.get('status')
        receipt_number = callback_data.get('receipt_number')

        logger.info(f"[PARSPAL_VERIFY] Callback data: status={status_code}, receipt={receipt_number}")

        # 4️⃣ بررسی وضعیت
        if status_code != '100':
            status_messages = {
                '99': 'انصراف کاربر از پرداخت',
                '88': 'پرداخت ناموفق',
                '77': 'لغو پرداخت توسط کاربر'
            }
            
            payment.status = PaymentStatus.FAILED
            payment.save(update_fields=['status'])
            
            logger.warning(f"[PARSPAL_VERIFY] Payment failed with status: {status_code}")
            
            return Response({
                "success": False,
                "message": status_messages.get(status_code, 'پرداخت ناموفق')
            }, status=status.HTTP_400_BAD_REQUEST)

        # 5️⃣ وضعیت 100 = کاربر پرداخت کرده، حالا باید verify کنیم
        if not receipt_number:
            return Response({
                "success": False,
                "message": "شماره رسید یافت نشد."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 6️⃣ فراخوانی API تایید پارس‌پال
        headers = {
            "ApiKey": PARSPAL_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "amount": int(payment.amount),
            "receipt_number": receipt_number
        }

        logger.info(f"[PARSPAL_VERIFY] Sending verify request to ParsPal: {payload}")

        try:
            response = requests.post(
                f"{BASE_URL}/verify",
                json=payload,
                headers=headers,
                timeout=10
            )
            logger.info(f"[PARSPAL_VERIFY] Verify Response [{response.status_code}]: {response.text}")

            if response.status_code == 200:
                data = response.json()

                # 7️⃣ بررسی status از پاسخ
                if data.get("status") == "SUCCESSFUL":
                    logger.info(f"[PARSPAL_VERIFY] Payment verified successfully! Receipt: {receipt_number}")

                    # پرداخت تأیید شد
                    payment.status = PaymentStatus.COMPLETED
                    payment.ref_id = receipt_number
                    payment.paid_at = timezone.now()
                    payment.save(update_fields=["status", "ref_id", "paid_at"])

                    plan = payment.subscription.plan

                    # 8️⃣ بررسی اشتراک فعلی
                    active_sub = Subscription.objects.filter(
                        user=payment.user,
                        status=SubscriptionStatusChoicesModel.active,
                        end_date__gt=timezone.now()
                    ).order_by('-end_date').first()
                    
                    
                    if active_sub:
                        new_start = active_sub.end_date
                        new_end = new_start + timezone.timedelta(days=plan.duration_days)
                        logger.info(f"[PARSPAL_VERIFY] Extending subscription. New end date: {new_end}")
                    else:
                        new_start = timezone.now()
                        new_end = new_start + timezone.timedelta(days=plan.duration_days)
                        logger.info(f"[PARSPAL_VERIFY] Creating new subscription. End date: {new_end}")


                    # 9️⃣ بروزرسانی اشتراک
                    payment.subscription.status = SubscriptionStatusChoicesModel.active
                    payment.subscription.start_date = new_start
                    payment.subscription.end_date = new_end
                    payment.subscription.save(update_fields=['status', 'start_date', 'end_date'])
                        
                    profile = payment.user.profile
                    if profile.role == "admin":
                        pass
                    profile.role = 'premium'
                    profile.subscription_end_date = new_end
                    profile.save(update_fields=['role', 'subscription_end_date'])
                    logger.info(f"[PARSPAL_VERIFY] User profile updated: ID={profile.id}, Role=premium, SubEnd={new_end}")

                    # 🔟 پاک کردن کش
                    cache.delete(cache_key)

                    return Response({
                        "success": True,
                        "message": "پرداخت با موفقیت تأیید و اشتراک فعال شد.",
                        "data": {
                            "amount": data.get("amount"),
                            "receipt_number": receipt_number,
                            "reference_number": data.get("reference_number"),
                            "transaction_id": data.get("transaction_id"),
                            "order_id": order_id,
                            "subscription_start": new_start.isoformat(),
                            "subscription_end": new_end.isoformat(),
                            "already_verified": False
                        }
                    }, status=status.HTTP_200_OK)

                # اگر status برابر "VERIFIED" بود (قبلاً تأیید شده)
                elif data.get("status") == "VERIFIED":
                    logger.warning(f"[PARSPAL_VERIFY] Receipt already verified by ParsPal: {receipt_number}")
                    
                    # پرداخت رو Completed می‌کنیم (اگر نشده بود)
                    if payment.status != PaymentStatus.COMPLETED:
                        payment.status = PaymentStatus.COMPLETED
                        payment.ref_id = receipt_number
                        payment.paid_at = timezone.now()
                        payment.save(update_fields=["status", "ref_id", "paid_at"])
                    
                    return Response({
                        "success": True,
                        "message": "این رسید قبلاً تأیید شده است.",
                        "data": {
                            "amount": data.get("paid_amount"),
                            "receipt_number": receipt_number,
                            "order_id": order_id,
                            "subscription_start": payment.subscription.start_date.isoformat(),
                            "subscription_end": payment.subscription.end_date.isoformat(),
                            "already_verified": True
                        }
                    }, status=status.HTTP_200_OK)

                # وضعیت ناموفق
                logger.warning(f"[PARSPAL_VERIFY] Verification failed: {data}")
                payment.status = PaymentStatus.FAILED
                payment.save(update_fields=['status'])

                return Response({
                    "success": False,
                    "message": data.get("message", "تأیید پرداخت ناموفق بود."),
                    "data": data
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.error(f"[PARSPAL_VERIFY] Invalid response from ParsPal: {response.status_code}")
            return Response({
                "success": False,
                "message": "پاسخ نامعتبر از پارس‌پال.",
                "status_code": response.status_code,
                "response": response.text
            }, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            logger.error(f"[PARSPAL_VERIFY] Error in verification: {e}")
            payment.status = PaymentStatus.FAILED
            payment.save(update_fields=['status'])

            return Response({
                "success": False,
                "message": "خطا در ارتباط با پارس‌پال.",
                "error": str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)

# ======= PARSPAL INQUIRY VIEW ======= #
@extend_schema_view(
    get=extend_schema(tags=['Payment'], summary='درگاه پرداخت و عملیات آن'),
    post=extend_schema(tags=["Payment"]),
)
class ParspalInquiryView(APIView):
    """استعلام وضعیت تراکنش"""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        headers = {
            "ApiKey": PARSPAL_API_KEY,
            "Accept": "application/json"
        }

        try:
            response = requests.get(f"{BASE_URL}/inquiry/{order_id}", headers=headers, timeout=10)
            data = response.json()

            return Response({
                "success": True,
                "message": "استعلام با موفقیت انجام شد.",
                "data": data
            }, status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            return Response({
                "success": False,
                "message": "خطا در ارتباط با سرور پارس‌پال.",
                "error": str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)

