from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers import UserRegisterSerializer, UserProfileVerificationSerializer

# ============ User Registration View ============ #
class UserRegisterView(generics.CreateAPIView):
    """
    این ویو اطلاعات اولیه کاربر را دریافت کرده، یک حساب کاربری ایجاد می‌کند
    و یک توکن JWT برای دسترسی به مرحله بعد (ارسال مدارک) برمی‌گرداند.
    """
    serializer_class = UserRegisterSerializer
    
    throttle_classes = [AnonRateThrottle]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        tokens = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        response_data = {
            "message": "ثبت‌نام اولیه با موفقیت انجام شد. لطفاً برای تکمیل فرآیند، مدارک خود را ارسال کنید.",
            "tokens": tokens
        }
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

# ============ User Profile Verification View ============ #
class UserProfileVerificationView(generics.UpdateAPIView):
    """
    این ویو مدارک هویتی کاربر احراز هویت شده را دریافت و پروفایل او را به‌روزرسانی می‌کند.
    دسترسی به این ویو فقط با توکن معتبر امکان‌پذیر است.
    """
    serializer_class = UserProfileVerificationSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get_object(self):
        return self.request.user.profile
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        response_data = {
            "message": "مدارک شما با موفقیت دریافت شد. حساب شما پس از بررسی توسط ادمین فعال خواهد شد. نتیجه از طریق ایمیل به شما اطلاع داده می‌شود."
        }

        return Response(response_data, status=status.HTTP_200_OK)
