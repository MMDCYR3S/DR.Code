from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.cache import cache
from django.conf import settings
import random
from apps.accounts.services import AmootSMSService
from ..serializers.phone_verification_serializer import PhoneVerificationSerializer

# ===== Phone Verification View ===== #
class PhoneVerificationView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PhoneVerificationSerializer

    def get(self, request):
        """
        ایجاد کد اعتبارسنجی برای تایید شماره تلفن کاربر
        """
        user = request.user
        if user.is_phone_verified:
            return Response({"message": "شماره تلفن شما تایید شده است."}, status=status.HTTP_400_BAD_REQUEST)

        # ===== ایجاد کد 5 رقمی ===== #
        otp = str(random.randint(00000, 99999))
        
        # ===== کلید ذخیره کد اعتبارسنجی ===== #
        cache_key = f"phone_verification_{user.id}"
        
        # ===== ذخیره کد اعتبارسنجی در کش ===== #
        cache.set(cache_key, otp, timeout=120)
        
        # ===== ارسال پیامک ===== #
        service = AmootSMSService()
        result = service.send_verification_code(user.phone_number, code_length=5, optional_code=otp)
        
        if result:
            return Response({"message": "کد اعتبارسنجی با موفقیت ارسال شد."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "کد اعتبارسنجی ارسال نشد."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def post(self, request):
        """
        تایید کد اعتبارسنجی
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            user = request.user
            
            cache_key = f"phone_verification_{user.id}"
            cached_otp = cache.get(cache_key)
            
            if cached_otp and str(cached_otp) == code:
                user.is_phone_verified = True
                user.save()
                
                # ===== حذف کد اعتبارسنجی از کش ===== #
                cache.delete(cache_key)
                
                return Response({"message": "شماره تلفن شما با موفقیت تایید شد."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "کد اعتبارسنجی نامعتبر یا منقضی است."}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
