import logging

from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin

from rest_framework import status

from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.authentication import JWTAuthentication

User = get_user_model()

logger = logging.getLogger(__name__)

class SingleDeviceLoginMiddleware(MiddlewareMixin):
    """
    این Middleware بررسی می‌کند که آیا کاربر با آخرین توکن معتبر خود درخواست می‌دهد یا خیر.
    اگر JTI توکن با JTI فعال کاربر در دیتابیس مطابقت نداشته باشد،
    به این معنی است که کاربر از دستگاه دیگری وارد شده و این توکن باطل است.
    """

    def process_request(self, request):
        # این Middleware فقط برای کاربرانی که لاگین کرده‌اند اعمال می‌شود.
        # request.user توسط Middlewareهای قبلی جنگو (مثل AuthenticationMiddleware) پر می‌شود.
        exempt_paths = ['/api/v1/accounts/register/', '/admin/']
        if any(request.path.startswith(path) for path in exempt_paths):
            return None

        jwt_authenticator = JWTAuthentication()

        # تلاش برای استخراج هدر احراز هویت
        auth_header = jwt_authenticator.get_header(request)
        if auth_header is None:
            # اگر هدر Authorization وجود ندارد، این Middleware کاری برای انجام دادن ندارد.
            # ممکن است درخواست با session auth باشد یا یک درخواست عمومی باشد.
            return None

        try:
            # توکن خام را از هدر استخراج می‌کنیم
            raw_token = jwt_authenticator.get_raw_token(auth_header)
            if raw_token is None:
                return None

            # توکن را رمزگشایی و اعتبارسنجی می‌کنیم (بدون بررسی دیتابیس)
            validated_token = jwt_authenticator.get_validated_token(raw_token)
            
            # ID کاربر و JTI را از payload توکن استخراج می‌کنیم
            user_id = validated_token.get('user_id')
            token_jti = validated_token.get('jti')

            if user_id is None or token_jti is None:
                # اگر توکن user_id یا jti را نداشت، آن را نادیده می‌گیریم تا توسط سیستم اصلی رد شود.
                return None

            try:
                # کاربر را مستقیماً از دیتابیس با استفاده از user_id موجود در توکن پیدا می‌کنیم.
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                # اگر کاربری با این ID وجود نداشت، توکن نامعتبر است.
                # هرچند simple-jwt معمولا این را مدیریت می‌کند، اما این بررسی امنیت را افزایش می‌دهد.
                return None

            # بررسی می‌کنیم که مدل کاربر فیلد active_jti را داشته باشد
            if not hasattr(user, 'active_jti'):
                return None

            # JTI توکن را با JTI فعال کاربر در دیتابیس مقایسه می‌کنیم
            user_active_jti = user.active_jti

            if token_jti == user_active_jti:
                logger.warning(
                    f"توکن نامعتبر برای کاربر {user}. "
                    f"JTI توکن: {token_jti}, JTI فعال در دیتابیس: {user_active_jti}. "
                    "ورود از دستگاه دیگر شناسایی شد."
                )
                
                return JsonResponse(
                    {
                        'success': False,
                        'message': 'نشست شما معتبر نیست. لطفاً دوباره وارد شوید.',
                        'detail': 'شما از یک دستگاه یا مرورگر دیگر وارد شده‌اید. این نشست باطل شد.',
                        'code': 'token_not_valid_for_device'
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

        except InvalidToken:
            # اگر توکن منقضی شده یا فرمت آن اشتباه است، simple-jwt آن را رد خواهد کرد.
            # پس در اینجا نیازی به مدیریت آن نیست و اجازه می‌دهیم درخواست ادامه یابد.
            return None
        
        except Exception as e:
            logger.error(f"خطای غیرمنتظره در SingleDeviceLoginMiddleware: {e}", exc_info=True)
            # در محیط production بهتر است خطای ۵۰۰ عمومی برگردانید.
            return JsonResponse(
                {
                    'success': False,
                    'message': 'خطای داخلی سرور در حین اعتبارسنجی نشست.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # اگر توکن معتبر بود و JTI هم مطابقت داشت، درخواست به مسیر خود ادامه می‌دهد.
        return None
    