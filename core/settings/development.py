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

# ========= LOGS SETTINGS ========= #
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)  # ایجاد پوشه در صورت عدم وجود

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'celery': {
            'format': '[{asctime}] {levelname} [{name}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    
    'handlers': {
        # لاگ عمومی Django
        'django_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        # ===== هندلر اختصاصی احراز هویت ===== #
        'verification_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'verification.log',  # فایل جداگانه
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        # ===== هندلر اختصاصی احراز هویت ===== #
        'verification_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'verification.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        
        # لاگ Celery Tasks
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'celery.log',
            'maxBytes': 20 * 1024 * 1024,  # 20 MB
            'backupCount': 10,
            'formatter': 'celery',
            'encoding': 'utf-8',
        },
        
        # لاگ فشرده‌سازی تصاویر
        'compression_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'image_compression.log',
            'maxBytes': 50 * 1024 * 1024,  # 50 MB
            'backupCount': 15,
            'formatter': 'celery',
            'encoding': 'utf-8',
        },
        
        # لاگ خطاها
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        
        'email_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'email.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'simple',
            'encoding': 'utf-8',
        },
        # ===== هندلر اختصاصی پرداخت (جدید) ===== #
        'payment_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'payments.log',  # ذخیره در فایل جداگانه
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        # کنسول (اختیاری)
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    
    'loggers': {
        # Django عمومی
        'apps.dashboard.administrator.services.email_service': {
            'handlers': ['email_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # ===== لاگر اختصاصی احراز هویت ===== #
        'user_verification': {
            'handlers': ['verification_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['django_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # ===== لاگر اختصاصی احراز هویت ===== #
        'user_verification': {
            'handlers': ['verification_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Celery عمومی
        'celery': {
            'handlers': ['celery_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Task های فشرده‌سازی
        'apps.prescriptions.tasks': {
            'handlers': ['compression_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        # خطاها
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        
        # لاگر سفارشی برای فشرده‌سازی
        'image_compression': {
            'handlers': ['compression_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # ===== لاگر اختصاصی زرین‌پال (جدید) ===== #
        'zarinpal': {
            'handlers': ['payment_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

