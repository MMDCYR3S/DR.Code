from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()

# =========== PASSWORD RESET SERIALIZERS =========== #
class PasswordResetRequestSerializer(serializers.Serializer):
    """
    سریالایزر برای درخواست بازنشانی رمز عبور.
    فقط فیلد ایمیل را برای شناسایی کاربر دریافت می‌کند.
    """
    
    email = serializers.EmailField(
        max_length=255,
        error_messages={
            "required": "وارد کردن ایمیل الزامی است.",
            "blank": "ایمیل نمی‌تواند خالی باشد.",
            "invalid": "یک ایمیل معتبر وارد کنید.",
        }
    )
    
    def validate_email(self, value):
        """
        بررسی می‌کند که آیا کاربری با این ایمیل وجود دارد یا خیر.
        """
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("کاربری با این ایمیل وجود ندارد.")
        return value

# =========== PASSWORD RESET SERIALIZERS =========== #
class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    سریالایزر برای تایید بازنشانی رمز عبور و تنظیم رمز جدید.
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password],
        error_messages={
            "required": "وارد کردن رمز عبور الزامی است.",
            "blank": "رمز عبور نمی‌تواند خالی باشد.",
        }
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            "required": "وارد کردن تکرار رمز عبور الزامی است.",
            "blank": "تکرار رمز عبور نمی‌تواند خالی باشد.",
        }
    )
    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "رمز عبور و تکرار آن باید یکسان باشند."})
        return super().validate(attrs)
