from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from datetime import timedelta

from ..serializers import LoginSerializer, RefreshTokenSerializer

import logging
import uuid

from .base_view import BaseAPIView

User = get_user_model()

logger = logging.getLogger(__name__)

# ================================ #
# ========== LOGIN VIEW ========== #
# ================================ #
class LoginView(BaseAPIView):
    """
    ورود کاربر به سیستم
    
    امنیت:
    - کنترل ورود همزمان
    - ثبت IP و دستگاه
    - مدیریت Session
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            logger.warning(f"تلاش ورود ناموفق از IP: {self.get_client_ip(request)}")
            return Response({
                'success': False,
                'message': 'اطلاعات ورودی نامعتبر است.',
                'errors': e.detail 
            }, status=status.HTTP_400_BAD_REQUEST)
            
        user = serializer.user

        try:
            with transaction.atomic():
                new_jti = uuid.uuid4().hex

                refresh = RefreshToken.for_user(user)
                refresh['jti'] = new_jti

                access_token = refresh.access_token

                access_token['jti'] = new_jti

                user.active_jti = new_jti
                
                user.last_login = timezone.now()
                user.last_login_ip = self.get_client_ip(request)
                user.last_login_device = self.get_user_agent(request)
                user.save(update_fields=['active_jti', 'last_login', 'last_login_ip', 'last_login_device'])

                login(request, user)
                
                if user.is_superuser or user.profile.role == "admin":
                    request.session['jwt_tokens'] = {
                        'access_token': str(access_token),
                        'refresh_token': str(refresh),
                        'jti': new_jti
                    }
                
                logger.info(f"کاربر وارد شد: {user.phone_number} | JTI: {new_jti}")

                profile = user.profile
                response_data = {
                    'success': True,
                    'message': 'ورود با موفقیت انجام شد.',
                    'data': {
                        'user': {
                            'id': user.id,
                            'full_name': user.full_name,
                            'phone_number': user.phone_number,
                        },
                        'profile': {
                            'role': profile.role,
                            'role_display': profile.get_role_display(),
                            "auth_status": profile.auth_status,
                            "medical_code": profile.medical_code,
                        },
                        'tokens': {
                            'access_token': str(access_token),
                            'refresh_token': str(refresh),
                            "jti": str(new_jti)
                        }
                    }
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
                                
        except Exception as e:
            logger.error(f"خطای داخلی هنگام ورود کاربر {user.phone_number}: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "یک خطای داخلی در سرور رخ داد. لطفاً بعداً تلاش کنید."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ====================================== #
# ============ LOGOUT VIEW ============ # 
# ====================================== #
class LogoutView(BaseAPIView):
    """
    خروج کاربر از سیستم
    
    امنیت:
    - پاک کردن Session Key
    - Blacklist کردن Refresh Token
    - لاگ‌گیری
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                user = request.user
                
                if user.active_jti:
                    user.active_jti = None
                    user.save(update_fields=['active_jti'])
                
                refresh_token_str = request.data.get('refresh_token')
                if refresh_token_str:
                    try:
                        token = RefreshToken(refresh_token_str)
                        token.blacklist()
                    except Exception as e:
                        logger.warning(f"خطا در blacklist کردن token هنگام خروج: {str(e)}")
                        
                logout(request)
                
                logger.info(f"کاربر خارج شد: {user.phone_number}")
                
                return Response({
                    'success': True,
                    'message': 'خروج با موفقیت انجام شد.'
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return self.handle_exception(e)

# ===================================================== #
# ============ REFRESH ACCESS TOKEN VIEW ============ #
# ===================================================== #
class RefreshAccessTokenView(TokenRefreshView, BaseAPIView):
    """
    بازسازی Access Token با استفاده از Refresh Token
    
    امنیت:
    - استفاده از مکانیزم استاندارد JWT
    - بررسی اعتبار Refresh Token
    - لاگ‌گیری درخواست‌ها
    """
    
    def post(self, request, *args, **kwargs):
        try:
            # استفاده از implementation پایه TokenRefreshView
            response = super().post(request, *args, **kwargs)
            
            # اگر موفقیت‌آمیز بود، لاگ بگیریم
            if response.status_code == status.HTTP_200_OK:
                # تلاش برای شناسایی کاربر از روی refresh token
                refresh_token = request.data.get('refresh')
                if refresh_token:
                    try:
                        token_obj = RefreshToken(refresh_token)
                        jti = token_obj.get('jti')
                        token = UntypedToken(refresh_token)
                        user_id = token.get('user_id')
                        user = User.objects.get(id=user_id)
                        logger.info(f"Access token بازسازی شد برای: {user.phone_number}")
                    except (User.DoesNotExist, InvalidToken, TokenError):
                        logger.warning("بازسازی token برای کاربر نامشخص")
                
                # اضافه کردن اطلاعات اضافی به پاسخ
                if hasattr(response, 'data') and isinstance(response.data, dict):
                    response.data.update({
                        'success': True,
                        'message': 'توکن با موفقیت بازسازی شد.',
                        'token_refreshed_at': timezone.now().isoformat(),
                        "jti": jti
                    })
            
            return response
            
        except Exception as e:
            logger.error(f"خطا در بازسازی token: {str(e)}")
            return Response({
                'success': False,
                'message': 'خطا در بازسازی توکن. لطفاً مجدداً وارد شوید.',
                'error_code': 'TOKEN_REFRESH_FAILED'
            }, status=status.HTTP_400_BAD_REQUEST)

# ============================================= #
# ============ FORCE LOGOUT VIEW ============ #
# ============================================= #
class ForceLogoutView(BaseAPIView):
    """
    خروج اجباری از تمام دستگاه‌ها
    
    برای مواردی که کاربر می‌خواهد از همه جا خارج شود
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                user = request.user
                
                # پاک کردن session key
                user.current_session_key = None
                user.save(update_fields=['current_session_key'])
                
                # تلاش برای blacklist کردن همه refresh tokenها
                # (نیاز به پیاده‌سازی سیستم ذخیره‌سازی tokenها دارد)
                
                # Django logout
                logout(request)
                
                logger.info(f"خروج اجباری انجام شد برای: {user.phone_number}")
                
                return Response({
                    'success': True,
                    'message': 'شما از تمام دستگاه‌ها خارج شدید.',
                    'data': {
                        'logout_time': timezone.now().isoformat(),
                        'force_logout': True
                    }
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return self.handle_exception(e)

# ============================================ #
# ============ LOGIN STATUS VIEW ============ #
# ============================================ #
class LoginStatusView(BaseAPIView):
    """
    بررسی وضعیت ورود کاربر
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            profile = user.profile
            
            return Response({
                'success': True,
                'data': {
                    'user': {
                        'id': user.id,
                        'full_name': user.full_name,
                        'phone_number': user.phone_number,
                        'is_active': user.is_active,
                        'last_login': user.last_login,
                        'last_login_ip': user.last_login_ip,
                        'current_session_active': bool(user.current_session_key),
                    },
                    'profile': {
                        'auth_status': profile.auth_status,
                        'role': profile.role,
                        'has_subscription': bool(
                            profile.subscription_end_date and 
                            profile.subscription_end_date > timezone.now()
                        ),
                    },
                    'session_info': {
                        'current_ip': self.get_client_ip(request),
                        'current_device': self.get_user_agent(request),
                        'session_matches': (
                            user.current_session_key == request.session.session_key
                        )
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return self.handle_exception(e)
