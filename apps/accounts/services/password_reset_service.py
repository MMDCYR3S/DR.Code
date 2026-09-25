import random
import logging

from django.core.cache import cache
from django.contrib.auth import get_user_model

# سرویس پیامک خودت
from apps.accounts.services.amoot_sms import AmootSMSService
from apps.accounts.services.password_service import send_password_reset_sms

logger = logging.getLogger(__name__)
User = get_user_model()

# ========== کلیدهای کش ========== #
PHONE_RESET_CODE_KEY      = "phone_reset_code:{phone}"     # کد ۶ رقمی → TTL: 120s
PHONE_RESET_VERIFIED_KEY  = "phone_reset_verified:{phone}" # تاییدیه کد → TTL: 600s (10 دقیقه)
PHONE_RESET_RATE_KEY      = "phone_reset_rate:{phone}"     # محدودیت درخواست → TTL: 120s

# ========== تنظیمات ========== #
CODE_TTL_SECONDS      = 120   # ۲ دقیقه اعتبار کد پیامکی
VERIFIED_TTL_SECONDS  = 600   # ۱۰ دقیقه فرصت برای تغییر رمز
RATE_LIMIT_SECONDS    = 120   # هر ۲ دقیقه یکبار می‌تونه درخواست بده
CODE_LENGTH           = 6


def generate_verification_code() -> str:
    """تولید کد ۶ رقمی تصادفی (بدون صفر ابتدایی از دست نره)"""
    return str(random.randint(100000, 999999))


def request_password_reset_code(phone_number: str) -> bool:
    """
    ارسال کد تایید به شماره موبایل و ذخیره در کش.
    Returns:
        bool: True اگه پیامک با موفقیت ارسال شد.
    Raises:
        User.DoesNotExist: اگه کاربری با این شماره نباشه.
    """
    # ۱. چک کردن کاربر
    user = User.objects.get(phone_number=phone_number)

    # ۲. چک کردن محدودیت ارسال
    rate_key = PHONE_RESET_RATE_KEY.format(phone=phone_number)
    if cache.get(rate_key):
        raise PermissionError("لطفاً کمی صبر کنید و مجدداً تلاش کنید.")

    # ۳. تولید کد و ذخیره در کش
    code = generate_verification_code()
    code_key = PHONE_RESET_CODE_KEY.format(phone=phone_number)
    cache.set(code_key, code, timeout=CODE_TTL_SECONDS)

    # هر بار درخواست جدید، تاییدیه قبلی پاک میشه
    cache.delete(PHONE_RESET_VERIFIED_KEY.format(phone=phone_number))

    # ۴. ارسال پیامک
    sms_service = AmootSMSService()
    message = (
        f"کد تایید بازنشانی رمز عبور شما در دکترکد:\n"
        f"{code}\n"
        f"این کد تا {CODE_TTL_SECONDS // 60} دقیقه معتبر است."
    )
    sent_ok = sms_service.send_message(mobile=phone_number, message_text=message)

    if not sent_ok:
        # اگه پیامک نرفت، کش رو پاک کن که کاربر گیر نکنه
        cache.delete(code_key)
        logger.error(f"پیامک بازیابی برای {phone_number} ارسال نشد.")
        raise ConnectionError("ارسال پیامک با خطا مواجه شد. لطفاً مجدداً تلاش کنید.")

    # ۵. ثبت محدودیت ارسال
    cache.set(rate_key, "1", timeout=RATE_LIMIT_SECONDS)

    logger.info(f"کد بازیابی برای {phone_number} ارسال شد.")
    return True


def verify_code_and_mark(phone_number: str, code: str) -> bool:
    """
    کد وارد شده توسط کاربر رو چک می‌کنه.
    اگه درست بود، یک flag تایید در کش ست می‌کنه که مرحله بعد ازش استفاده کنه.
    """
    code_key = PHONE_RESET_CODE_KEY.format(phone=phone_number)
    saved_code = cache.get(code_key)

    if not saved_code:
        raise TimeoutError("کد تایید منقضی شده است. لطفاً دوباره درخواست دهید.")

    if str(saved_code) != str(code):
        raise ValueError("کد تایید وارد شده صحیح نیست.")

    # علامت‌گذاری به‌عنوان تایید شده
    verified_key = PHONE_RESET_VERIFIED_KEY.format(phone=phone_number)
    cache.set(verified_key, True, timeout=VERIFIED_TTL_SECONDS)

    # کد رو پاک می‌کنیم که دیگه قابل استفاده نباشه
    cache.delete(code_key)

    return True


def is_phone_verified_for_reset(phone_number: str) -> bool:
    """چک می‌کنه آیا این شماره تاییدیه معتبر برای تغییر رمز داره یا نه"""
    verified_key = PHONE_RESET_VERIFIED_KEY.format(phone=phone_number)
    return bool(cache.get(verified_key))


def apply_new_password(phone_number: str, new_password: str) -> None:
    """
    رمز جدید رو اعمال می‌کنه و تاییدیه کش رو پاک می‌کنه.
    ⚠️ فقط اگه شماره تایید شده باشه.
    """
    if not is_phone_verified_for_reset(phone_number):
        raise PermissionError("شماره موبایل شما برای تغییر رمز تایید نشده است. لطفاً از ابتدا شروع کنید.")

    user = User.objects.get(phone_number=phone_number)
    user.set_password(new_password)
    user.save()

    # پاک کردن تاییدیه و محدودیت
    cache.delete(PHONE_RESET_VERIFIED_KEY.format(phone=phone_number))
    cache.delete(PHONE_RESET_RATE_KEY.format(phone=phone_number))

    logger.info(f"رمز عبور برای {phone_number} تغییر کرد.")