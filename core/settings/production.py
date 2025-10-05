from .base import *

# Session تنظیمات
SESSION_COOKIE_AGE = 30 * 24 * 60 * 60  # 30 روز
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# امنیت
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# لاگ‌گیری
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/accounts.log',
        },
    },
    'loggers': {
        'accounts': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
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

# ====== EMAIL CONFIGS ====== #
EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = ("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = ("EMAIL_HOST_PASSWORD")
