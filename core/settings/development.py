from .base import *
import os

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ========= ZarinPal Sandbox Settings ========= #
ZARINPAL_CONFIG = {
    'MERCHANT_ID': env("ZARINPAL_MERCHANT_ID", default="faeddedf-558c-4cd6-9f18-63d0c6088477"),
    'SANDBOX': env("ZARINPAL_SANDBOX", default=True),
    'REQUEST_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/request.json',
    'START_PAY_URL': 'https://sandbox.zarinpal.com/pg/StartPay/',
    'VERIFY_URL': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
    'CALLBACK_URL': env("ZARINPAL_CALLBACK_URL", default='http://localhost:8000/api/v1/payments/verify/'),
}

PARSPAL_CONFIG = {
    'API_KEY': "00000000aaaabbbbcccc000000000000",
    'PARSPAL_CALLBACK_URL': 'https://drcode-med.com/',
    'SANDBOX': True,
}

# ======= CACHE CONFIGS ======= #
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.redis.RedisCache",
#         "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/1"),
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         },
#         "KEY_PREFIX": "dr_code_dev",
#         "TIMEOUT": 300,  # 5 minutes default timeout
#     }
# }

# Cache session backend
# SESSION_ENGINE = "django.contrib.sessions.backends.cache"
# SESSION_CACHE_ALIAS = "default"

# ====== EMAIL CONFIGS ====== #
EMAIL_BACKEND = env("EMAIL_BACKEND", default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env("EMAIL_HOST", default='smtp.gmail.com')
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="amingholami06@gmail.com")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="oojt ugkq exew ofbs")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)

# Add Redis Queue configuration
# RQ_QUEUES = {
#     'default': {
#         'HOST': env("REDIS_HOST", default='127.0.0.1'),
#         'PORT': env.int("REDIS_PORT", default=6379),
#         'DB': env.int("REDIS_DB", default=0),
#     }
# }
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-suffix',
    }
}