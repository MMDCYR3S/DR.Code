from .base import *
import os

# Session تنظیمات
SESSION_COOKIE_AGE = 2 * 24 * 60 * 60  # 30 روز
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# جلسات امن
SESSION_COOKIE_SECURE = True  # فقط روی HTTPS
SESSION_COOKIE_HTTPONLY = True  # محافظت از جلسات در برابر جاوا اسکریپت
SESSION_COOKIE_SAMESITE = 'Strict'  # محافظت در برابر CSRF - افزایش امنیت
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # منقضی شدن جلسه در بسته شدن مرورگر

# امنیت
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'  # محافظت در برابر clickjacking
SECURE_SSL_REDIRECT = True  # هدایت اجباری به HTTPS
SECURE_HSTS_SECONDS = 31536000  # 1 year  - HTTP Strict Transport Security
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# امنیت اضافی
SECURE_REDIRECT_EXEMPT = []  # لیست مسیرهایی که نیاز به redirect ندارند
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'  # محافظت در برابر طرح های مبتنی بر origin

# CSRF تنظیمات امنیتی
CSRF_COOKIE_SECURE = True  # کوکی CSRF فقط در ارتباطات HTTPS ارسال شود
CSRF_COOKIE_HTTPONLY = True  # محافظت در برابر دسترسی جاوا اسکریپت به CSRF
CSRF_COOKIE_SAMESITE = 'Strict'  # محافظت در برابر CSRF
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'  # نمای خطا CSRF سفارشی

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

# لاگ‌گیری امنیتی
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}] {message}',
            'style': '{',
        },
        'security': {
            'format': '[{asctime}] SECURITY {levelname} user={user} ip={ip} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'security',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ========= ZarinPal Production Settings ========= #
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

# Cache session backend
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Database for production (PostgreSQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
        "OPTIONS": {
            "connect_timeout": 10,
            "sslmode": "require",  # الزام استفاده از SSL برای اتصال به دیتابیس
        },
        "CONN_MAX_AGE": 60,  # reuse connections
    }
}

# افزودن امنیت API
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # ادامه تنظیمات از base
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # افزایش محدودیت برای کاربران ناشناس
        'user': '1000/hour',  # افزایش محدودیت برای کاربران عضو
        'login_attempts': '5/hour',  # محدودیت تلاش ورود
        'login_attempts_ip': '10/hour',  # محدودیت تلاش ورود بر اساس IP
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',  # فقط JSON - جلوگیری از مخاطرات XSS
    ],
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
