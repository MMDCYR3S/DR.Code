from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.accounts.models import Profile, AuthStatusChoices # مسیر ایمپورت را متناسب با پروژه خود تنظیم کنید

User = get_user_model()

class Command(BaseCommand):
    """
    یک دستور مدیریتی برای ایجاد کاربران تستی با پروفایل‌های مختلف.
    این دستور برای پر کردن دیتابیس با داده‌های نمونه جهت تست پنل ادمین کاربرد دارد.
    """
    help = 'Creates a number of test users with different verification statuses.'

    @transaction.atomic
    def handle(self, *args, **options):
        """ منطق اصلی اجرای دستور در این متد قرار دارد """
        
        self.stdout.write(self.style.NOTICE('شروع فرآیند ساخت کاربران تستی...'))
        
        # اگر کاربران تستی از قبل وجود دارند، برای جلوگیری از خطا آن‌ها را حذف می‌کنیم
        phone_numbers_to_delete = [
            '09120000001', '09120000002', '09120000003', '09120000004', 
            '09120000005', '09120000006', '09120000007', '09120000008'
        ]
        User.objects.filter(phone_number__in=phone_numbers_to_delete).delete()
        self.stdout.write(self.style.WARNING('کاربران تستی قبلی (در صورت وجود) حذف شدند.'))

        # رمز عبور مشترک برای همه کاربران تستی
        password = 'testpassword123'

        # لیستی از داده‌های کاربران برای ساخت
        users_data = [
            {
                'first_name': 'سارا', 'last_name': 'رضایی', 'phone_number': '09120000001',
                'status': AuthStatusChoices.PENDING.value, 'role': 'visitor', 'medical_code': '۱۱۱۲۲'
            },
            {
                'first_name': 'علی', 'last_name': 'کریمی', 'phone_number': '09120000002',
                'status': AuthStatusChoices.PENDING.value, 'role': 'visitor', 'medical_code': None
            },
            {
                'first_name': 'زهرا', 'last_name': 'محمدی', 'phone_number': '09120000003',
                'status': AuthStatusChoices.PENDING.value, 'role': 'visitor', 'medical_code': '۳۳۴۴۵'
            },
            {
                'first_name': 'حسین', 'last_name': 'اکبری', 'phone_number': '09120000004',
                'status': AuthStatusChoices.APPROVED.value, 'role': 'regular', 'medical_code': '۵۵۶۶۷'
            },
            {
                'first_name': 'مریم', 'last_name': 'حسینی', 'phone_number': '09120000005',
                'status': AuthStatusChoices.APPROVED.value, 'role': 'premium', 'medical_code': '۷۷۸۸۹'
            },
            {
                'first_name': 'رضا', 'last_name': 'صادقی', 'phone_number': '09120000006',
                'status': AuthStatusChoices.REJECTED.value, 'role': 'visitor', 'medical_code': '۹۹۰۰۱',
                'rejection_reason': 'تصویر کارت ملی ارسالی خوانا نبود.'
            },
            {
                'first_name': 'فاطمه', 'last_name': 'احمدی', 'phone_number': '09120000007',
                'status': AuthStatusChoices.APPROVED.value, 'role': 'regular', 'medical_code': '۱۱۲۲۳'
            },
            {
                'first_name': 'محمد', 'last_name': 'نوروزی', 'phone_number': '09120000008',
                'status': AuthStatusChoices.PENDING.value, 'role': 'visitor', 'medical_code': '۴۴۵۵۶'
            },
        ]

        for data in users_data:
            user = User.objects.create_user(
                phone_number=data['phone_number'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password=password
            )
            
            # پروفایل به صورت خودکار توسط سیگنال ساخته می‌شود، ما فقط آن را آپدیت می‌کنیم
            profile = user.profile
            profile.role = data['role']
            profile.auth_status = data['status']
            profile.medical_code = data.get('medical_code')
            profile.rejection_reason = data.get('rejection_reason')
            profile.save()

            self.stdout.write(self.style.SUCCESS(f'کاربر "{user.full_name}" با وضعیت "{profile.get_auth_status_display()}" با موفقیت ساخته شد.'))

        self.stdout.write(self.style.SUCCESS('عملیات ساخت کاربران تستی با موفقیت به پایان رسید!'))