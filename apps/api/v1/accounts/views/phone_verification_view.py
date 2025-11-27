import random
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.cache import cache

from apps.accounts.services import AmootSMSService
from ..serializers import PhoneVerificationSerializer

class PhoneVerificationView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PhoneVerificationSerializer

    def get(self, request):
        user = request.user
        print(f"DEBUG: User {user.phone_number} requested OTP via QuickOTP.")

        if user.is_phone_verified:
            return Response(
                {"message": "Your phone is already verified."}, # پیام انگلیسی برای جلوگیری از ارور اسکی در لاگ‌های خاص
                status=status.HTTP_400_BAD_REQUEST
            )

        # تولید کد ۵ رقمی
        otp_code = str(random.randint(10000, 99999))
        
        # ذخیره در کش
        cache_key = f"phone_verification_{user.id}"
        cache.set(cache_key, otp_code, timeout=120)

        try:
            service = AmootSMSService() 
            mobile_number = str(user.phone_number)
            
            # === استفاده از متد جدید SendQuickOTP ===
            result = service.send_quick_otp(
                mobile=mobile_number,
                code_length=5,          # طول کد (جهت اطمینان)
                optional_code=otp_code  # کد تولید شده توسط ما
            )
            
            if result:
                # معمولا اگر موفق باشد جیسون یا پیامی برمی‌گرداند
                return Response(
                    {"message": "کد اعتبارسنجی ارسال شد."}, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": "خطا در سرویس پیامک (QuickOTP)."}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
                
        except Exception as e:
            print(f"CRITICAL ERROR: {repr(e)}")
            return Response(
                {"message": "خطای داخلی سرور."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        # متد POST بدون تغییر باقی می‌ماند
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
                
                return Response(
                    {"message": "شماره تلفن تایید شد."}, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": "کد نامعتبر است."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
