from .base import *
import os


# امنیت فایل آپلود
FILE_UPLOAD_PERMISSIONS = 0o644  # مجوزهای امن برای فایل های آپلود شده
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024  # 2MB حداکثر اندازه فایل

# محدودیت اندازه درخواست
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024  # 2MB حداکثر اندازه آپلود
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # حداکثر تعداد فیلدهای فرم
# ========= ZarinPal Sandbox Settings ========= #
ZARINPAL_CONFIG = {
    'MERCHANT_ID': "45209320-b090-4116-a1bd-8abd770d7787",
    'SANDBOX': False,
    'REQUEST_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/request.json',
    'START_PAY_URL': 'https://sandbox.zarinpal.com/pg/StartPay/',
    'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
    'CALLBACK_URL': 'http://localhost:8000/api/v1/payments/verify/',
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-suffix',
    }
}

# ====== EMAIL CONFIGS ====== #
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "arad.pws-dns.net"
EMAIL_PORT = "465"
EMAIL_USE_SSL = True
EMAIL_HOST_USER = "info@drcode-med.ir"
EMAIL_HOST_PASSWORD = "A!s2D#f4G%h6J&"
DEFAULT_FROM_EMAIL = "info@drcode-med.ir"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# تنظیمات امنیت رمز عبور
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # افزایش حداقل طول رمز عبور
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
