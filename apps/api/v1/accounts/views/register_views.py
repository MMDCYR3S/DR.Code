import uuid
import logging

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Profile, AuthStatusChoices, AuthenticationDocument
from ..serializers import RegisterSerializer, AuthenticationSerializer
from apps.dashboard.administrator.services.email_service import send_welcome_email
from .base_view import BaseAPIView

User = get_user_model()
logger = logging.getLogger(__name__)

# ============ REGISTER VIEW ============ #
class RegisterView(CreateAPIView, BaseAPIView):
    """
    ثبت‌نام کاربر جدید
    
    مرحله اول: دریافت اطلاعات پایه کاربر
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                serializer = self.get_serializer(data=request.data)
                
                if serializer.is_valid():
                    user = serializer.save()

                    user.last_login_ip = self.get_client_ip(request)
                    user.last_login_device = self.get_user_agent(request)
                    
                    uuid_jti = uuid.uuid4().hex
                    
                    
                    refresh = RefreshToken.for_user(user)
                    refresh["jti"] = uuid_jti
                    
                    access_token = refresh.access_token
                    access_token["jti"] = uuid_jti
                    
                    user.active_jti = uuid_jti
                    
                    user.save(update_fields=['last_login_ip', 'last_login_device', 'active_jti'])
                    
                    user.profile.medical_code = "DR-CODE"
                    user.profile.save()
                    
                    send_welcome_email(user=user)
                    
                    login(request, user)
                    
                    logger.info(f"کاربر جدید ثبت‌نام شد: {user.phone_number}")
                    
                    return Response({
                        'success': True,
                        'message': 'ثبت‌نام با موفقیت انجام شد. لطفاً مرحله احراز هویت را تکمیل کنید.',
                        'data': {
                            'user_id': user.id,
                            'full_name': user.full_name,
                            'phone_number': user.phone_number,
                            'access_token': str(access_token),
                            'refresh_token': str(refresh),
                            'jti' : user.active_jti,
                            'profile': {
                                'role': user.profile.role,
                                'role_display': user.profile.get_role_display(),
                                "auth_status": user.profile.auth_status,
                                "medical_code": user.profile.medical_code,
                            },
                            'next_step': 'authentication'
                        }
                    }, status=status.HTTP_201_CREATED)
                
                return Response({
                    'success': False,
                    'message': 'خطا در اطلاعات ورودی',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return self.handle_exception(e)

# =============== AUTHENTICATION VIEW =============== #
class AuthenticationView(BaseAPIView):
    """
    احراز هویت پزشکی
    
    مرحله دوم: ارسال مدارک احراز هویت
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AuthenticationSerializer

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                user = request.user
                profile = user.profile
                
                # بررسی اینکه کاربر قبلاً احراز هویت نکرده باشد
                if profile.auth_status == AuthStatusChoices.APPROVED:
                    return Response({
                        'success': False,
                        'message': 'شما قبلاً احراز هویت شده‌اید.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                serializer = self.serializer_class(data=request.data)
                
                if serializer.is_valid():
                    # بروزرسانی اطلاعات احراز هویت
                    validated_data = serializer.validated_data
                    
                    profile.medical_code = validated_data.get('medical_code', profile.medical_code)
                    profile.auth_link = validated_data.get('auth_link', profile.auth_link)
                    
                    profile.documents.all().delete()
                    
                    document_files = validated_data.get("documents", [])
                    for doc_file in document_files:
                        AuthenticationDocument.objects.create(profile=profile, file=doc_file)
                        
                        logger.info(f"مدارک احراز هویت ارسال شد: {user.phone_number}")
                    
                    # تنظیم معرف در صورت وجود
                    referral_code = validated_data.get('referral_code')
                    if referral_code and not profile.referred_by:
                        try:
                            referrer_profile = Profile.objects.get(referral_code=referral_code.upper())
                            profile.referred_by = referrer_profile.user
                        except Profile.DoesNotExist:
                            pass
                    
                    profile.auth_status = AuthStatusChoices.PENDING
                    profile.rejection_reason = None
                    profile.save()
                    
                    logger.info(f"مدارک احراز هویت ارسال شد: {user.phone_number}")
                    
                    return Response({
                        'success': True,
                        'message': 'مدارک احراز هویت با موفقیت ارسال شد. در کوتاه‌ترین زمان ممکن بررسی و نتیجه اطلاع‌رسانی خواهد شد.',
                        'data': {
                            'auth_status': profile.auth_status,
                            'auth_status_display': profile.get_auth_status_display()
                        }
                    }, status=status.HTTP_200_OK)
                
                return Response({
                    'success': False,
                    'message': 'خطا در اطلاعات ارسالی',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return self.handle_exception(e)

# ========== LOGOUT VIEW ========== #
class LogoutView(BaseAPIView):
    """
    خروج کاربر از سیستم
    
    پاک کردن session key برای امنیت بیشتر
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            
            # پاک کردن session key
            user.current_session_key = None
            user.save(update_fields=['current_session_key'])
            
            # Blacklist کردن refresh token در صورت ارسال
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception:
                    pass  # اگر token معتبر نبود، مهم نیست
            
            logger.info(f"کاربر خروج کرد: {user.phone_number}")
            
            return Response({
                'success': True,
                'message': 'خروج با موفقیت انجام شد.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return self.handle_exception(e)


class CheckAuthStatusView(BaseAPIView):
    """
    بررسی وضعیت احراز هویت کاربر
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            profile = request.user.profile
            
            return Response({
                'success': True,
                'data': {
                    'auth_status': profile.auth_status,
                    'auth_status_display': profile.get_auth_status_display(),
                    'role': profile.role,
                    'rejection_reason': profile.rejection_reason if profile.auth_status == AuthStatusChoices.REJECTED else None,
                    'has_subscription': bool(profile.subscription_end_date and profile.subscription_end_date > timezone.now()),
                    'subscription_end_date': profile.subscription_end_date
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return self.handle_exception(e)


class ResendAuthenticationView(BaseAPIView):
    """
    ارسال مجدد مدارک احراز هویت
    
    برای کاربرانی که مدارکشان رد شده است
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AuthenticationSerializer

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                user = request.user
                profile = user.profile
                
                # بررسی اینکه کاربر مجاز به ارسال مجدد باشد
                if profile.auth_status not in [AuthStatusChoices.REJECTED, AuthStatusChoices.PENDING]:
                    return Response({
                        'success': False,
                        'message': 'شما مجاز به ارسال مجدد مدارک نیستید.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                serializer = self.serializer_class(data=request.data)
                
                if serializer.is_valid():
                    # بروزرسانی اطلاعات احراز هویت
                    validated_data = serializer.validated_data
                    
                    profile.medical_code = validated_data.get('medical_code', profile.medical_code)
                    profile.auth_link = validated_data.get('auth_link', profile.auth_link)
                    
                    if validated_data.get('auth_image'):
                        profile.auth_image = validated_data['auth_image']
                    
                    # تغییر وضعیت به در انتظار تایید
                    profile.auth_status = AuthStatusChoices.PENDING
                    profile.rejection_reason = None
                    profile.save()
                    
                    logger.info(f"مدارک احراز هویت مجدداً ارسال شد: {user.phone_number}")
                    
                    return Response({
                        'success': True,
                        'message': 'مدارک احراز هویت مجدداً با موفقیت ارسال شد. در کوتاه‌ترین زمان ممکن بررسی خواهد شد.',
                        'data': {
                            'auth_status': profile.auth_status,
                            'auth_status_display': profile.get_auth_status_display()
                        }
                    }, status=status.HTTP_200_OK)
                
                return Response({
                    'success': False,
                    'message': 'خطا در اطلاعات ارسالی',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return self.handle_exception(e)



