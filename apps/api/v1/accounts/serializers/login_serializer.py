# api/v1/accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.core.validators import RegexValidator
import re

User = get_user_model()

# ======== Login Serializer ======== #
class LoginSerializer(serializers.Serializer):
    """
    Serializer برای ورود کاربر
    
    فقط از طریق شماره تلفن امکان ورود وجود دارد
    """
    phone_number = serializers.CharField(
        max_length=15,
        required=True,
        help_text="شماره تلفن همراه (09xxxxxxxxx)"
    )
    password = serializers.CharField(
        max_length=128,
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="رمز عبور"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate_phone_number(self, value):
        """اعتبارسنجی فرمت شماره تلفن"""
        # حذف فاصله‌ها و کاراکترهای اضافی
        phone_number = re.sub(r'\D', '', value)
        
        # بررسی فرمت شماره تلفن ایرانی
        if not re.match(r'^09\d{9}$', phone_number):
            raise serializers.ValidationError(
                "فرمت شماره تلفن صحیح نیست. (مثال: 09123456789)"
            )
        
        return phone_number

    def validate(self, attrs):
        """اعتبارسنجی کلی و احراز هویت کاربر"""
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')

        if not phone_number or not password:
            raise serializers.ValidationError(
                "شماره تلفن و رمز عبور الزامی است."
            )

        # احراز هویت کاربر
        # username در سیستم ما همان phone_number است
        self.user = authenticate(
            username=phone_number,
            password=password
        )

        if not self.user:
            raise serializers.ValidationError(
                "اطلاعات کاربری نامعتبر است."
            )

        # بررسی اینکه حساب کاربری فعال باشد
        if not self.user.is_active:
            raise serializers.ValidationError(
                "حساب کاربری شما غیرفعال است. لطفاً با پشتیبانی تماس بگیرید."
            )

        return attrs

    def get_user(self):
        """دریافت کاربر احراز هویت شده"""
        return self.user

# ======== Refresh Token Serializer ======== #
class RefreshTokenSerializer(serializers.Serializer):
    """
    Serializer برای refresh token
    """
    refresh_token = serializers.CharField(
        required=True,
        help_text="Refresh Token"
    )
