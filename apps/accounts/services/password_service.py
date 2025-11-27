import requests
import logging
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

# ایمپورت سرویس پیامک که قبلاً نوشتیم
from apps.accounts.services.amoot_sms import AmootSMSService 

logger = logging.getLogger(__name__)

# ================================================== #
# ============= URL SHORTENER UTILITY ============= #
# ================================================== #
def shorten_url(long_url: str) -> str:
    """
    لینک طولانی را دریافت کرده و با استفاده از سرویس TinyURL آن را کوتاه می‌کند.
    در صورت بروز خطا، همان لینک اصلی را برمی‌گرداند.
    """
    try:
        # استفاده از API رایگان TinyURL (یا هر سرویس دیگری که مد نظر دارید)
        api_url = f"http://tinyurl.com/api-create.php?url={long_url}"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            return response.text
        
        logger.warning(f"URL Shortener failed with status: {response.status_code}")
        return long_url
        
    except Exception as e:
        logger.error(f"Error shortening URL: {e}")
        return long_url

# ================================================== #
# ========== SEND PASSWORD RESET SMS TASK ========= #
# ================================================== #
def send_password_reset_sms(user):
    """
    تولید توکن، ساخت لینک، کوتاه کردن آن و ارسال پیامک بازیابی.
    """
    if not user.phone_number:
        logger.warning(f"User {user.id} has no phone number for password reset.")
        return

    try:
        # 1. تولید توکن و UID
        token_generator = PasswordResetTokenGenerator()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # 2. ساخت لینک کامل (Front-end URL)
        # فرض بر این است که فرانت روی این آدرس گوش می‌دهد
        reset_path = f"password/reset/confirm/{uid}/{token}/"
        base_url = "https://drcode-med.ir/"  # بهتر است از settings خوانده شود
        full_url = f"{base_url}{reset_path}"

        # 3. کوتاه کردن لینک
        short_link = shorten_url(full_url)

        # 4. آماده‌سازی متن پیامک
        # نکته: فاصله و نیم‌فاصله‌ها برای خوانایی تنظیم شده‌اند
        message_text = (
            f"همکار گرامی {user.first_name if user.first_name else 'عزیز'}،\n"
            "جهت بازیابی رمز عبور، لینک زیر را باز کنید:\n"
            f"{short_link}\n"
            "دکترکد"
        )

        # 5. ارسال پیامک
        sms_service = AmootSMSService()
        sms_service.send_message(mobile=user.phone_number, message_text=message_text)
        
        logger.info(f"Password reset SMS sent to {user.phone_number}")

    except Exception as e:
        logger.error(f"Failed to send password reset SMS to {user.id}: {e}")