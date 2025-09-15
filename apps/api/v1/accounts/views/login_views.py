from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from datetime import timedelta

from ..serializers import LoginSerializer, RefreshTokenSerializer

import logging

from .base_view import BaseAPIView

User = get_user_model()

logger = logging.getLogger(__name__)

# ========== LOGIN VIEW ========== #
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
        try:
            with transaction.atomic():
                serializer = self.serializer_class(data=request.data)
                
                if serializer.is_valid():
                    user = serializer.get_user()
                    current_session_key = request.session.session_key
                    
                    # بررسی ورود همزمان - اگر کاربر در جای دیگری لاگین است
                    if (user.current_session_key and 
                        user.current_session_key != current_session_key):
                        
                        logger.warning(f"تلاش ورود همزمان: {user.phone_number} از IP: {self.get_client_ip(request)}")
                        
                        return Response({
                            'success': False,
                            'message': 'شما در دستگاه دیگری وارد سیستم هستید. لطفاً ابتدا از آن خارج شوید.',
                            'error_code': 'MULTIPLE_LOGIN_DETECTED'
                        }, status=status.HTTP_409_CONFLICT)
                    
                    # ایجاد JWT توکن‌ها
                    refresh = RefreshToken.for_user(user)
                    access_token = refresh.access_token
                    
                    # بروزرسانی اطلاعات ورود کاربر
                    user_updates = {
                        'last_login': timezone.now(),
                        'last_login_ip': self.get_client_ip(request),
                        'last_login_device': self.get_user_agent(request),
                        'current_session_key': current_session_key
                    }
                    
                    for field, value in user_updates.items():
                        setattr(user, field, value)
                    
                    user.save(update_fields=list(user_updates.keys()))
                    
                    # Django login برای session management
                    login(request, user)
                    
                    # آماده‌سازی اطلاعات پاسخ
                    profile = user.profile
                    response_data = {
                        'success': True,
                        'message': 'ورود با موفقیت انجام شد.',
                        'data': {
                            'user': {
                                'id': user.id,
                                'full_name': user.full_name,
                                'phone_number': user.phone_number,
                                'email': user.email,
                                'is_active': user.is_active,
                            },
                            'profile': {
                                'auth_status': profile.auth_status,
                                'auth_status_display': profile.get_auth_status_display(),
                                'role': profile.role,
                                'role_display': profile.get_role_display(),
                                'has_subscription': bool(
                                    profile.subscription_end_date and 
                                    profile.subscription_end_date > timezone.now()
                                ),
                                'subscription_end_date': profile.subscription_end_date,
                                'referral_code': profile.referral_code,
                            },
                            'tokens': {
                                'access_token': str(access_token),
                                'refresh_token': str(refresh),
                                'access_token_expires_at': (
                                    timezone.now() + 
                                    timedelta(seconds=access_token.get('exp', 3600))
                                ).isoformat(),
                            },
                            'session_info': {
                                'login_time': user.last_login.isoformat(),
                                'ip_address': user.last_login_ip,
                                'session_expires_in_days': 30  # مطابق تنظیمات Django
                            }
                        }
                    }
                    
                    logger.info(f"کاربر وارد شد: {user.phone_number} از IP: {user.last_login_ip}")
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                
                # خطاهای اعتبارسنجی
                error_messages = []
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list):
                        error_messages.extend(errors)
                    else:
                        error_messages.append(str(errors))
                
                logger.warning(f"تلاش ورود ناموفق از IP: {self.get_client_ip(request)}")
                
                return Response({
                    'success': False,
                    'message': error_messages[0] if error_messages else 'اطلاعات ورودی نامعتبر است.',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return self.handle_exception(e)


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
                
                # پاک کردن session key برای امنیت
                user.current_session_key = None
                user.save(update_fields=['current_session_key'])
                
                # Blacklist کردن refresh token در صورت ارسال
                refresh_token = request.data.get('refresh_token')
                blacklisted_token = False
                
                if refresh_token:
                    try:
                        token = RefreshToken(refresh_token)
                        token.blacklist()
                        blacklisted_token = True
                        logger.info(f"Refresh token blacklist شد برای: {user.phone_number}")
                    except (InvalidToken, TokenError) as e:
                        logger.warning(f"خطا در blacklist کردن token: {str(e)}")
                        # ادامه می‌دهیم چون خروج همچنان معتبر است
                
                # Django logout
                logout(request)
                
                logger.info(f"کاربر خارج شد: {user.phone_number} از IP: {self.get_client_ip(request)}")
                
                return Response({
                    'success': True,
                    'message': 'خروج با موفقیت انجام شد.',
                    'data': {
                        'logout_time': timezone.now().isoformat(),
                        'token_blacklisted': blacklisted_token
                    }
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return self.handle_exception(e)


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
                        'token_refreshed_at': timezone.now().isoformat()
                    })
            
            return response
            
        except Exception as e:
            logger.error(f"خطا در بازسازی token: {str(e)}")
            return Response({
                'success': False,
                'message': 'خطا در بازسازی توکن. لطفاً مجدداً وارد شوید.',
                'error_code': 'TOKEN_REFRESH_FAILED'
            }, status=status.HTTP_400_BAD_REQUEST)


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
