# apps/payment/views/parspal_dynamic_view.py
import uuid
import json
import logging
import requests
import random

from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

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
        "amount": 80000,
        "currency": "IRT",
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
            subscription = Subscription.objects.acreate(
                user=request.user,
                plan=plan,
                payment_amount=payload["amount"],
                status=SubscriptionStatusChoicesModel.pending,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=plan.duration_days)
            )

            # ایجاد رکورد پرداخت
            payment = Payment.objects.acreate(
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
                        "redirect_url": data.get("link"),
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

# ======= PARSPAL VERIFY VIEW ======= #
class ParspalVerifyView(APIView):
    """تأیید پرداخت پس از بازگشت از درگاه"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")
        ref_id = request.data.get("ref_id")

        if not order_id or not ref_id:
            return Response({
                "success": False,
                "message": "پارامترهای لازم (order_id یا ref_id) ارسال نشده‌اند."
            }, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "ApiKey": PARSPAL_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payment = Payment.objects.filter(authority=order_id, user=request.user).first()
        if not payment:
            return Response({
                "success": False,
                "message": "تراکنش مورد نظر یافت نشد."
            }, status=status.HTTP_404_NOT_FOUND)

        payload = {
            "amount": int(payment.amount),
            "order_id": order_id,
            "ref_id": ref_id
        }

        try:
            response = requests.post(f"{BASE_URL}/verify", json=payload, headers=headers, timeout=10)
            logger.info(f"Verify Response [{response.status_code}]: {response.text}")

            if response.status_code == 200:
                data = response.json()

                if data.get("status"):
                    # --- پرداخت تأیید شد ---
                    payment.status = PaymentStatus.COMPLETED.value
                    payment.ref_id = ref_id
                    payment.paid_at = timezone.now()
                    payment.save(update_fields=["status", "ref_id", "paid_at"])

                    plan = payment.subscription.plan

                    # بررسی اشتراک فعلی کاربر
                    active_sub = Subscription.objects.filter(
                        user=request.user,
                        status=SubscriptionStatusChoicesModel.active,
                        end_date__gt=timezone.now()
                    ).order_by('-end_date').first()

                    if active_sub:
                        # اگر اشتراک فعالی دارد، تمدید می‌کنیم از انتهای قبلی
                        new_start = active_sub.end_date
                        new_end = new_start + timezone.timedelta(days=plan.duration_days)
                    else:
                        # اگر اشتراک فعال ندارد، اشتراک از الان شروع شود
                        new_start = timezone.now()
                        new_end = new_start + timezone.timedelta(days=plan.duration_days)

                    # ایجاد اشتراک جدید
                    new_subscription = Subscription.objects.create(
                        user=request.user,
                        plan=plan,
                        payment_amount=payment.amount,
                        status=SubscriptionStatusChoicesModel.active,
                        start_date=new_start,
                        end_date=new_end
                    )

                    # لینک دادن پرداخت به اشتراک جدید
                    payment.subscription = new_subscription
                    payment.save(update_fields=["subscription"])

                    return Response({
                        "success": True,
                        "message": "پرداخت با موفقیت تأیید و اشتراک فعال شد.",
                        "data": {
                            "amount": data.get("amount"),
                            "ref_id": ref_id,
                            "order_id": order_id,
                            "subscription_start": new_start,
                            "subscription_end": new_end
                        }
                    }, status=status.HTTP_200_OK)

                # وضعیت ناموفق از پارس‌پال
                return Response({
                    "success": False,
                    "message": data.get("message", "تأیید پرداخت ناموفق بود."),
                    "data": data
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "success": False,
                "message": "پاسخ نامعتبر از پارس‌پال دریافت شد.",
                "status_code": response.status_code
            }, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.Timeout:
            return Response({
                "success": False,
                "message": "مهلت پاسخ پارس‌پال به پایان رسید."
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)

        except requests.exceptions.RequestException as e:
            logger.error(f"خطا در verify: {e}")
            return Response({
                "success": False,
                "message": "خطا در برقراری ارتباط با پارس‌پال.",
                "error": str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)

# ======= PARSPAL INQUIRY VIEW ======= #
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

