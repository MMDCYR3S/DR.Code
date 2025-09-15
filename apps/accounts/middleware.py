# accounts/middleware.py

from django.contrib.auth import logout
from django.http import JsonResponse
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class SingleSessionMiddleware:
    """
    Middleware برای کنترل ورود همزمان کاربران
    
    طبق مستند محصول: "هر حساب کاربری فقط مجاز است در یک دستگاه به‌صورت هم‌زمان وارد سامانه شود"
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_session_key = getattr(request.session, 'session_key', None)
            user_session_key = request.user.current_session_key
            
            # بررسی اینکه session key کاربر مطابقت دارد یا نه
            if user_session_key and user_session_key != current_session_key:
                logger.warning(f"تلاش ورود همزمان برای کاربر: {request.user.phone_number}")
                
                # اگر درخواست API باشد، پاسخ JSON برگردان
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        'success': False,
                        'message': 'حساب شما از دستگاه دیگری وارد شده است. لطفاً مجدداً وارد شوید.',
                        'code': 'SESSION_CONFLICT'
                    }, status=401)
                
                # در غیر این صورت، کاربر را خارج کن
                logout(request)
        
        response = self.get_response(request)
        
        # اگر کاربر وارد شده، session key را بروزرسانی کن
        if request.user.is_authenticated and hasattr(request, 'session'):
            if request.user.current_session_key != request.session.session_key:
                request.user.current_session_key = request.session.session_key
                request.user.save(update_fields=['current_session_key'])
        
        return response
