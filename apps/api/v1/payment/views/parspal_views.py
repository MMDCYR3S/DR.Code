# apps/payment/views/parspal_dynamic_view.py
import uuid
import json
import logging
import requests
from decimal import Decimal

from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.payment.models import Payment
from apps.subscriptions.models import Subscription, SubscriptionStatusChoicesModel, Plan
from ..serializers import PaymentCreateSerializer

logger = logging.getLogger(__name__)

# ======= تنظیمات پارس‌پال ======= #
PARSPAL_API_KEY = "00000000aaaabbbbcccc000000000000"
PARSPAL_SANDBOX = True
BASE_URL = "https://sandbox.api.parspal.com/v1/payment" if PARSPAL_SANDBOX else "https://api.parspal.com/v1/payment"


# ======= تابع کمکی تبدیل کش به JSON آماده ارسال ======= #
def prepare_cached_payment_data(cached_data):
    """
    تبدیل داده‌های کش به فرمت قابل استفاده برای payload پارس‌پال
    Decimal به int تبدیل می‌شود
    """
    if not isinstance(cached_data, dict):
        # اگر داده کش عدد یا None بود، dict پیش‌فرض بساز
        cached_data = {}

    # استخراج مقدار نهایی
    pricing_info = cached_data.get("pricing_info", {})
    final_price = pricing_info.get("final_price") or cached_data.get("final_price") or 10000
    final_price = int(final_price)  # تبدیل به عدد صحیح

    return {
        "amount": 200000,
        "currency": "IRR",
        "return_url": cached_data.get("return_url", "https://example.com/payment/verify"),
        "reserve_id": str(uuid.uuid4()),
        "order_id": str(uuid.uuid4()),
        "payer": {
            "name": cached_data.get("payer_name", "Test User"),
            "mobile": cached_data.get("payer_mobile", "09123456789"),
            "email": cached_data.get("payer_email", "test@example.com"),
            "allowed_cards": None,
            "match_card_and_mobile_nationalid": None
        },
        "description": cached_data.get("description", "پرداخت داینامیک از کش"),
        "default_psp": None
    }

# ======= ویو ======= #
class ParspalPaymentRequestView(APIView):
    """ایجاد درخواست پرداخت پارس‌پال با داده‌های کش شده"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # اعتبارسنجی اولیه
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan_id = serializer.validated_data['plan_id']

        # دریافت پلن
        plan = get_object_or_404(Plan, id=plan_id)

        # خواندن داده‌ها از کش
        cache_key = f"purchase_summary:{request.user.id}:{plan_id}"
        cached_data = cache.get(cache_key)


        if not cached_data:
            return Response({
                "success": False,
                "message": "داده‌ای برای این پلن در کش یافت نشد."
            }, status=status.HTTP_400_BAD_REQUEST)

        # آماده‌سازی payload
        payload = prepare_cached_payment_data(cached_data)
        logger.info(f"Payload نهایی برای ارسال به پارس‌پال: {json.dumps(payload)}")

        headers = {
            "ApiKey": PARSPAL_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            # ایجاد Subscription
            subscription = Subscription.objects.create(
                user=request.user,
                plan=plan,
                payment_amount=payload["amount"],
                status=SubscriptionStatusChoicesModel.pending,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=plan.duration_days)
            )

            # ایجاد Payment
            payment = Payment.objects.create(
                user=request.user,
                subscription=subscription,
                amount=payload["amount"],
                discount_amount=cached_data.get("discount_amount", 0),
                final_amount=payload["amount"],
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                authority=payload["order_id"]
            )

            response = requests.post(f"{BASE_URL}/request", json=payload, headers=headers, timeout=10)

            logger.info(f"کد وضعیت: {response.status_code}")
            logger.info(f"پاسخ دریافتی: {response.text}")

            if response.status_code in [200, 201]:
                data = response.json()
                # ذخیره اطلاعات پرداخت در کش برای استفاده بعدی
                cache.set(f"parspal_payment:{payload['order_id']}", data, timeout=60 * 15)

                return Response({
                    "success": True,
                    "message": "درخواست پرداخت با موفقیت ایجاد شد.",
                    "data": {
                        "order_id": payload["order_id"],
                        "amount": payload["amount"],
                        "payment_info": data
                    }
                }, status=status.HTTP_200_OK)

            return Response({
                "success": False,
                "message": "درخواست به پارس‌پال ناموفق بود.",
                "status_code": response.status_code,
                "response": response.text,
                "data": {
                    "order_id": payload["order_id"],
                    "amount": payload["amount"]
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.Timeout:
            logger.error("Timeout در ارتباط با پارس‌پال")
            return Response({
                "success": False,
                "message": "زمان انتظار برای پاسخ از درگاه به پایان رسید."
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)

        except requests.exceptions.RequestException as e:
            logger.error(f"خطا در ارسال درخواست: {str(e)}")
            return Response({
                "success": False,
                "message": "خطا در ارتباط با سرور پارس‌پال",
                "error": str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)
