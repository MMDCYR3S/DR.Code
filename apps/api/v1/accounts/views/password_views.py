from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema_view, extend_schema

from django.contrib.auth import get_user_model

from ..serializers import (
    PasswordResetByPhoneRequestSerializer,
    PasswordResetByPhoneConfirmSerializer,
)
from apps.accounts.services.password_reset_service import (
    request_password_reset_code,
    verify_code_and_mark,
    apply_new_password,
)

User = get_user_model()


# ==================================================== #
# ====== STEP 1: REQUEST CODE BY PHONE (SMS) ======== #
# ==================================================== #
@extend_schema_view(
    post=extend_schema(
        tags=['Password Reset'],
        summary='درخواست کد تایید پیامکی برای بازنشانی رمز'
    )
)
class PasswordResetByPhoneRequestAPIView(generics.GenericAPIView):
    """
    مرحله ۱: کاربر شماره موبایل رو می‌ده → کد ۶ رقمی پیامک میشه.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetByPhoneRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'اطلاعات ارسالی نامعتبر است.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']

        try:
            request_password_reset_code(phone_number)
        except PermissionError as e:
            return Response({
                'success': False,
                'message': str(e),
                'errors': {}
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except ConnectionError as e:
            return Response({
                'success': False,
                'message': str(e),
                'errors': {}
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'کاربری با این شماره یافت نشد.',
                'errors': {'phone_number': ['کاربری با این شماره یافت نشد.']}
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'success': True,
            'message': 'کد تایید به شماره موبایل شما ارسال شد.',
            'data': {'phone_number': phone_number}
        }, status=status.HTTP_200_OK)


# ==================================================== #
# == STEP 2: VERIFY CODE + SET NEW PASSWORD ========= #
# ==================================================== #
@extend_schema_view(
    post=extend_schema(
        tags=['Password Reset'],
        summary='تایید کد پیامکی و تنظیم رمز جدید'
    )
)
class PasswordResetByPhoneConfirmAPIView(generics.GenericAPIView):
    """
    مرحله ۲: کاربر کد پیامکی + رمز جدید + تکرارش رو می‌ده.
    - اگه کد درست باشه و تاییدیه گرفته باشه، رمز عوض میشه.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetByPhoneConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'اطلاعات ارسالی نامعتبر است.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        phone_number = data['phone_number']
        code = data['code']
        new_password = data['password']

        try:
            verify_code_and_mark(phone_number, code)
        except TimeoutError as e:
            return Response({
                'success': False,
                'message': str(e),
                'errors': {'code': [str(e)]}
            }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e),
                'errors': {'code': [str(e)]}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            apply_new_password(phone_number, new_password)
        except PermissionError as e:
            return Response({
                'success': False,
                'message': str(e),
                'errors': {}
            }, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'کاربری با این شماره یافت نشد.',
                'errors': {}
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'success': True,
            'message': 'رمز عبور شما با موفقیت تغییر کرد. اکنون می‌توانید وارد شوید.'
        }, status=status.HTTP_200_OK)
