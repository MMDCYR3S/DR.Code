import random
import logging
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.cache import cache

# ===== Local Services ===== #
from apps.accounts.services import AmootSMSService
from ..serializers import PhoneVerificationSerializer

# فراخوانی همان لاگر
logger = logging.getLogger('user_verification')

class PhoneVerificationView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PhoneVerificationSerializer

    AMOOT_PATTERN_CODE = "4311"  # بهتر است استرینگ باشد یا مطمئن شوید سرویس int میپذیرد

    def get(self, request):
        user = request.user
        
        logger.info(f"Verify Request received for User: {user.phone_number} (ID: {user.id})")

        if getattr(user, 'is_phone_verified', False):
            logger.warning(f"User {user.id} is already verified.")
            return Response(
                {"message": "حساب کاربری شما قبلاً تایید شده است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        code = str(random.randint(10000, 99999))
        
        cache_key = f"phone_verification_{user.id}"
        cache.set(cache_key, code, timeout=120)
        
        # لاگ کردن کد ساخته شده (فقط در محیط توسعه استفاده شود، در پروداکشن بهتر است لاگ نشود)
        logger.info(f"Generated OTP for {user.phone_number}: {code}")

        full_name = " ".join([user.first_name, user.last_name]) if user.first_name and user.last_name else "گرامی"

        user_name = full_name
        pattern_values = [user_name, code]

        try:
            service = AmootSMSService()
            mobile_number = str(user.phone_number)
            
            success = service.send_with_pattern(
                mobile=mobile_number,
                pattern_code=self.AMOOT_PATTERN_CODE,
                values=pattern_values
            )
            
            if success:
                return Response(
                    {"message": "کد تایید با موفقیت ارسال شد."}, 
                    status=status.HTTP_200_OK
                )
            else:
                # اینجا لاگ نمی‌کنیم چون خود سرویس با جزئیات لاگ کرده است
                return Response(
                    {"message": "خطا در ارسال پیامک. لطفاً دقایقی دیگر تلاش کنید."}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
        except Exception as e:
            # لاگ کردن خطای پیش‌بینی نشده در ویو
            logger.error(f"Unexpected Error in View: {str(e)}", exc_info=True)
            return Response(
                {"message": "خطای داخلی سرور."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            input_code = serializer.validated_data['code']
            user = request.user
            
            cache_key = f"phone_verification_{user.id}"
            cached_otp = cache.get(cache_key)
            
            if cached_otp and str(cached_otp) == str(input_code):
                user.is_phone_verified = True
                user.save()
                cache.delete(cache_key)
                
                logger.info(f"User {user.id} verified successfully.")
                
                return Response(
                    {"message": "شماره موبایل شما با موفقیت تایید شد."}, 
                    status=status.HTTP_200_OK
                )
            else:
                logger.warning(f"Failed verification attempt for User {user.id}. Input: {input_code}, Cached: {cached_otp}")
                return Response(
                    {"message": "کد وارد شده نامعتبر یا منقضی شده است."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
