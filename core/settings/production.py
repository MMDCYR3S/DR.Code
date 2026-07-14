from .base import *
import os

SESSION_COOKIE_AGE = 2 * 24 * 60 * 60  # 30 روز
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_REDIRECT_EXEMPT = []
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "https://drcode-med.ir",
    "https://www.drcode-med.ir",
]

CORS_ALLOW_HEADERS = [
    "authorization",
    "content-type",
    "accept",
    "origin",
]
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS"
]

# Content Security Policy (CSP) - اگر پکیج django-csp نصب باشد
# CSP_DEFAULT_SRC = ("'self'",)
# CSP_SCRIPT_SRC = ("'self'",)
# CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")

# امنیت فایل آپلود
FILE_UPLOAD_PERMISSIONS = 0o644  # مجوزهای امن برای فایل های آپلود شده
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024  # 2MB حداکثر اندازه فایل

# محدودیت اندازه درخواست
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024  # 2MB حداکثر اندازه آپلود
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # حداکثر تعداد فیلدهای فرم

# تنظیمات امنیتی اضافی برای API
SECURE_REFERRER_POLICY = 'same-origin'  # سیاست ارجاع امن

# ==================== BACKEND SESSION ENGINE ==================== #
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# ==================== CACHE CONFIGS ==================== #
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "unix:///home/drcodeme/redis/redis.sock?db=0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Broker (Redis با socket)
CELERY_BROKER_URL = "redis+socket:///home/drcodeme/redis/redis.sock?virtual_host=1"

# Backend (ذخیره نتایج)
CELERY_RESULT_BACKEND = "redis+socket:///home/drcodeme/redis/redis.sock?virtual_host=2"

# تنظیمات عمومی
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Tehran'
CELERY_ENABLE_UTC = False

# تنظیمات Task
CELERY_TASK_TRACK_STARTED = True


# فقط 1 Task همزمان
CELERY_WORKER_CONCURRENCY = 1

# حداکثر 200MB حافظه، بعدش Restart
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 500000

# محدودیت زمان
CELERYD_TASK_TIME_LIMIT = 300  # 5 دقیقه
CELERYD_TASK_SOFT_TIME_LIMIT = 240  # 4 دقیقه

# Prefetch کم (تعداد Task در صف)
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Ack دیر‌هنگام (بعد از اتمام Task)
CELERY_TASK_ACKS_LATE = True

# اگر Task کشته شد، دوباره نره توی صف
CELERY_TASK_REJECT_ON_WORKER_LOST = True


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
        
        # ===== هندلر اختصاصی OrderManager ===== #
        'order_manager_file': {
            'level': 'DEBUG', # می‌توانید به INFO یا ERROR تغییر دهید
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'order_manager.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
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

        # ===== لاگر اختصاصی OrderManager ===== #
        'order_manager': {
            'handlers': ['order_manager_file', 'console'],
            'level': 'DEBUG', # برای ثبت تمام جزئیات خطاها
            'propagate': False,
        },
    },
    
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# ========= ZarinPal Sandbox Settings ========= #
ZARINPAL_CONFIG = {
    'MERCHANT_ID': "511d8079-0a4d-43de-884c-29be8e57fdbb",
    'SANDBOX': False,
    'CALLBACK_URL': 'https://drcode-med.ir/payment/status/',
}

# ====== EMAIL CONFIGS ====== #
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.drcode-med.ir'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = 'info@drcode-med.ir'
EMAIL_HOST_PASSWORD = 'a1S@d3F$g5H^j7'
DEFAULT_FROM_EMAIL = 'info@drcode-med.ir'

# ====== DATABASE CONFIGS ====== #
DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.mysql'),
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True,
            'init_command': "SET NAMES utf8mb4; SET character_set_connection = 'utf8mb4';",
        },
    }
}

GA4_PROPERTY_ID = '514184786'
