from .base import *

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ========= ZarinPal Sandbox Settings ========= #
ZARINPAL_CONFIG = {
    'MERCHANT_ID': "faeddedf-558c-4cd6-9f18-63d0c6088477",
    'SANDBOX': True,
    'REQUEST_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/request.json',
    'START_PAY_URL': 'https://sandbox.zarinpal.com/pg/StartPay/',
    'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
    'CALLBACK_URL': 'http://localhost:8000/api/v1/payments/verify/',
}

# ======= CACHE CONFIGS ======= #
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# ====== EMAIL CONFIGS ====== #
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = "587"
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "amingholami06@gmail.com"
EMAIL_HOST_PASSWORD = "oojt ugkq exew ofbs"
DEFAULT_FROM_EMAIL = "amingholami06@gmail.com"
