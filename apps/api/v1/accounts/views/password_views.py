from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from ..serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from apps.dashboard.administrator.services.email_service import send_password_reset_email 

User = get_user_model()

# ============= PASSWORD RESET REQUEST ============= #
class PasswordResetRequestAPIView(generics.GenericAPIView):
    """
    API برای درخواست لینک بازنشانی رمز عبور.
    یک ایمیل دریافت می‌کند و در صورت وجود کاربر، لینک بازنشانی را ایمیل می‌کند.
    """
    
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email__iexact=email)
            
            send_password_reset_email(user)
        except User.DoesNotExist:
            return Response(
                {'detail': 'کاربری با این ایمیل یافت نشد.'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        return Response(
            {"detail": "اگر ایمیل وارد شده در سیستم ما موجود باشد، یک لینک بازیابی رمز عبور برای شما ارسال خواهد شد."},
            status=status.HTTP_200_OK
        )

# ============= PASSWORD RESET CONFIRM ============= #
class PasswordResetConfirmAPIView(generics.GenericAPIView):
    """
    API برای تایید بازنشانی رمز عبور.
    uid، توکن، و رمز عبور جدید را دریافت کرده، اعتبارسنجی می‌کند و رمز را تغییر می‌دهد.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        uidb64 = data['uidb64']
        token = data['token']
        password = data['password']

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            
        token_generator = PasswordResetTokenGenerator()
        if user is not None and token_generator.check_token(user, token):
            user.set_password(password)
            user.save()
            return Response(
                {"detail": "رمز عبور شما با موفقیت تغییر کرد. اکنون می‌توانید با رمز جدید وارد شوید."},
                status=status.HTTP_200_OK
            )
            
        else:
            return Response(
                {"detail": "لینک بازیابی نامعتبر یا منقضی شده است. لطفاً دوباره درخواست دهید."},
                status=status.HTTP_400_BAD_REQUEST
            )
