import random
import logging

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.cache import cache
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_view, extend_schema

# ===== Local Services ===== #
from apps.accounts.services import AmootSMSService
from ..serializers import (
    PasswordResetByPhoneRequestSerializer,
    PasswordResetByPhoneConfirmSerializer,
)

logger = logging.getLogger('user_verification')
User = get_user_model()


# ================= PASSWORD RESET BY PHONE - STEP 1 (REQUEST) ================= #
@extend_schema_view(
    post=extend_schema(
        tags=['Accounts'],
        summary='درخواست کد تایید برای بازنشانی رمز عبور (ارسال پیامک)'
    )
)
class PasswordResetByPhoneRequestAPIView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetByPhoneRequestSerializer

    # ⚠️ اگر کد پترن مخصوص بازنشانی رمز متفاوت است، این مقدار را عوض کن
    AMOOT_PATTERN_CODE = "4311"

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        user = User.objects.filter(phone_number=phone_number).first()

        # کاربر وجود دارد (سریالایزر چک کرده) - ولی محکم‌کاری:
        if not user:
            logger.warning(f"Password reset requested but user not found: {phone_number}")
            return Response(
                {"message": "کاربری با این شماره موبایل در سیستم ثبت نشده است."},
                status=status.HTTP_404_NOT_FOUND
            )

        logger.info(f"Password reset request for User: {phone_number} (ID: {user.id})")

        # ---- ساخت کد ۵ رقمی ----
        code = str(random.randint(10000, 99999))

        cache_key = f"password_reset_{user.id}"
        cache.set(cache_key, code, timeout=120)

        logger.info(f"Generated Password-Reset OTP for {phone_number}: {code}")

        # ---- آماده‌سازی مقادیر پترن ----
        full_name = " ".join(
            filter(None, [user.first_name, user.last_name])
        ) or "کاربر"

        pattern_values = [full_name, code]

        # ---- ارسال پیامک ----
        try:
            service = AmootSMSService()
            success = service.send_with_pattern(
                mobile=str(phone_number),
                pattern_code=self.AMOOT_PATTERN_CODE,
                values=pattern_values,
            )

            if success:
                return Response(
                    {"message": "کد تایید با موفقیت ارسال شد."},
                    status=status.HTTP_200_OK
                )

            return Response(
                {"message": "خطا در ارسال پیامک. لطفاً دقایقی دیگر تلاش کنید."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except Exception as e:
            logger.error(
                f"Unexpected Error in PasswordResetRequest: {str(e)}",
                exc_info=True
            )
            return Response(
                {"message": "خطای داخلی سرور."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ================= PASSWORD RESET BY PHONE - STEP 2 (CONFIRM) ================= #
@extend_schema_view(
    post=extend_schema(
        tags=['Accounts'],
        summary='تایید کد پیامکی و تغییر رمز عبور'
    )
)
class PasswordResetByPhoneConfirmAPIView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetByPhoneConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data['phone_number']
        input_code = serializer.validated_data['code']
        new_password = serializer.validated_data['password']

        user = User.objects.filter(phone_number=phone_number).first()
        if not user:
            logger.warning(f"Password reset confirm: user not found for {phone_number}")
            return Response(
                {"message": "کاربری با این شماره موبایل یافت نشد."},
                status=status.HTTP_404_NOT_FOUND
            )

        cache_key = f"password_reset_{user.id}"
        cached_otp = cache.get(cache_key)

        if cached_otp and str(cached_otp) == str(input_code):
            # ---- تغییر رمز عبور ----
            user.set_password(new_password)
            user.save(update_fields=['password'])

            # پاک‌کردن کد از کش
            cache.delete(cache_key)

            logger.info(f"Password reset SUCCESS for user {user.id} ({phone_number})")

            return Response(
                {"message": "رمز عبور شما با موفقیت تغییر کرد."},
                status=status.HTTP_200_OK
            )

        logger.warning(
            f"Failed password reset attempt for {phone_number}. "
            f"Input: {input_code}, Cached: {cached_otp}"
        )
        return Response(
            {"message": "کد وارد شده نامعتبر یا منقضی شده است."},
            status=status.HTTP_400_BAD_REQUEST
        )
