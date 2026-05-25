import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from unittest.mock import patch, MagicMock

# مدل‌ها و ابزارها (مسیرها را طبق پروژه خود تنظیم کنید)
from apps.payment.models import Payment, PaymentStatus
from apps.subscriptions.models.membership import Membership 
from apps.subscriptions.models.subscription import Subscription, SubscriptionStatusChoicesModel
from apps.subscriptions.models.plan import Plan
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', email='test@test.com', phone_number='09123456789', password='password123')

@pytest.fixture
def plan():
    return Plan.objects.create(name="طرح ماهانه", price=100000, duration_days=30)

@pytest.fixture
def create_payment(user, plan):
    """یک فیکسچر کمکی برای ساخت سریع آبجکت‌های پرداخت و اشتراک"""
    def _create(authority="A0000000000000000000", status=PaymentStatus.PENDING, final_amount=100000):
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            payment_amount=final_amount,
            status=SubscriptionStatusChoicesModel.pending,
            start_date=timezone.now(),
            end_date=timezone.now()
        )
        payment = Payment.objects.create(
            user=user,
            subscription=subscription,
            amount=final_amount,
            final_amount=final_amount,
            authority=authority,
            status=status,
        )
        return payment
    return _create

@pytest.mark.django_db
class TestPaymentVerifyView:
    # مسیر URL را طبق فایل urls.py خود تنظیم کنید
    url = reverse('payment:payment-callback') 

    @patch('apps.payment.views.ZarinpalService')  # ماک کردن کلاس سرویس در جایی که ایمپورت شده (views)
    def test_payment_verify_success_new_subscription(self, MockZarinpalService, api_client, user, create_payment):
        """تست سناریو موفقیت: پرداخت تایید شده و اشتراک جدید فعال می‌شود"""
        # 1. آماده‌سازی داده‌ها
        payment = create_payment()
        api_client.force_authenticate(user=user)

        # 2. تنظیم رفتار Mock (شبیه‌سازی پاسخ مثبت زرین‌پال)
        mock_service = MockZarinpalService.return_value
        mock_service.verify_payment.return_value = {
            'success': True,
            'ref_id': 'REF123456',
            'error': None
        }

        # 3. ارسال درخواست
        data = {'authority': payment.authority, 'status': 'OK'}
        response = api_client.post(self.url, data)

        # 4. بررسی پاسخ API
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['ref_id'] == 'REF123456'

        # 5. بررسی تغییرات دیتابیس (Payment)
        payment.refresh_from_db()
        assert payment.status == PaymentStatus.COMPLETED
        assert payment.ref_id == 'REF123456'
        assert payment.paid_at is not None

        # 6. بررسی تغییرات دیتابیس (Subscription)
        payment.subscription.refresh_from_db()
        assert payment.subscription.status == SubscriptionStatusChoicesModel.active
        # اطمینان از اینکه تاریخ پایان حدودا 30 روز بعد است
        assert payment.subscription.end_date > timezone.now() + timedelta(days=29)

    @patch('apps.payment.views.ZarinpalService')
    def test_payment_verify_failed_by_gateway(self, MockZarinpalService, api_client, user, create_payment):
        """تست سناریو شکست: زرین‌پال پرداخت را تایید نمی‌کند (مثلا موجودی ناکافی)"""
        payment = create_payment()
        api_client.force_authenticate(user=user)

        # شبیه‌سازی خطای زرین‌پال
        mock_service = MockZarinpalService.return_value
        mock_service.verify_payment.return_value = {
            'success': False,
            'error': 'تراکنش ناموفق بود'
        }

        data = {'authority': payment.authority, 'status': 'OK'}
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        payment.refresh_from_db()
        assert payment.status == PaymentStatus.FAILED
        
        payment.subscription.refresh_from_db()
        assert payment.subscription.status == SubscriptionStatusChoicesModel.canceled

    def test_payment_verify_canceled_by_user(self, api_client, user, create_payment):
        """تست سناریو لغو: کاربر در صفحه درگاه دکمه انصراف را زده است"""
        payment = create_payment()
        api_client.force_authenticate(user=user)

        # وقتی کاربر انصراف می‌دهد، پارامتر status معمولا NOK ارسال می‌شود
        data = {'authority': payment.authority, 'status': 'NOK'}
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'لغو شد' in response.data['error']

        payment.refresh_from_db()
        assert payment.status == PaymentStatus.CANCELLED

    def test_payment_verify_unauthorized_user(self, api_client, create_payment):
        """تست امنیتی: کاربری سعی کند پرداخت کاربر دیگری را تایید کند"""
        # پرداخت متعلق به user1 است
        payment = create_payment()
        
        # لاگین با user2
        other_user = User.objects.create_user(username='hacker', password='123')
        api_client.force_authenticate(user=other_user)

        data = {'authority': payment.authority, 'status': 'OK'}
        response = api_client.post(self.url, data)

        # باید دسترسی غیرمجاز دریافت کند
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('apps.payment.views.ZarinpalService')
    def test_payment_verify_extension_logic(self, MockZarinpalService, api_client, user, plan, create_payment):
        """تست سناریو تمدید: کاربر اشتراک فعال دارد و آن را تمدید می‌کند"""
        # 1. ایجاد یک اشتراک فعال که هنوز 5 روز از آن باقی مانده
        active_sub = Subscription.objects.create(
            user=user,
            plan=plan,
            status=SubscriptionStatusChoicesModel.active,
            start_date=timezone.now() - timedelta(days=25),
            end_date=timezone.now() + timedelta(days=5) # 5 روز مانده
        )
        original_end_date = active_sub.end_date

        # 2. ایجاد درخواست پرداخت جدید (pending)
        payment = create_payment() # اشتراک متصل به این پرداخت pending است
        api_client.force_authenticate(user=user)

        # 3. ماک موفقیت آمیز
        mock_service = MockZarinpalService.return_value
        mock_service.verify_payment.return_value = {'success': True, 'ref_id': 'REF_EXTEND', 'error': None}

        # 4. تایید پرداخت
        api_client.post(self.url, {'authority': payment.authority, 'status': 'OK'})

        # 5. بررسی لاجیک خاص تمدید در کد شما:
        # طبق کد شما: اشتراک جدید باید Expired شود و روزها به اشتراک قدیم اضافه شود
        active_sub.refresh_from_db()
        payment.subscription.refresh_from_db()

        # اشتراک قدیمی باید تمدید شده باشد (5 روز + 30 روز پلن جدید)
        expected_date = original_end_date + timedelta(days=plan.duration_days)
        # مقایسه با تلورانس 1 ثانیه برای اختلاف زمان اجرا
        assert abs((active_sub.end_date - expected_date).total_seconds()) < 5
        
        # اشتراک جدید (که با پرداخت ساخته شد) باید منقضی نشانه گذاری شود (طبق کد شما)
        assert payment.subscription.status == SubscriptionStatusChoicesModel.expired

    def test_payment_already_verified(self, api_client, user, create_payment):
        """تست Idempotency: جلوگیری از تایید مجدد تراکنش موفق"""
        payment = create_payment(status=PaymentStatus.COMPLETED)
        api_client.force_authenticate(user=user)

        data = {'authority': payment.authority, 'status': 'OK'}
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['already_verified'] is True