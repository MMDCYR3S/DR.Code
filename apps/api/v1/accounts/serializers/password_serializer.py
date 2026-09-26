import re
import random
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()

# =========== PASSWORD RESET BY PHONE - STEP 1 =========== #
class PasswordResetByPhoneRequestSerializer(serializers.Serializer):
    """
    مرحله اول: دریافت شماره موبایل و ارسال کد پیامکی
    """
    phone_number = serializers.CharField(
        max_length=15,
        required=True,
        error_messages={
            "required": "وارد کردن شماره موبایل الزامی است.",
            "blank": "شماره موبایل نمی‌تواند خالی باشد."
        }
    )

    def validate_phone_number(self, value):
        value = re.sub(r'\D', '', value)
        if not re.match(r'^09\d{9}$', value):
            raise serializers.ValidationError(
                "فرمت شماره موبایل صحیح نیست. (مثال: 09123456789)"
            )
        if not User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "کاربری با این شماره موبایل در سیستم ثبت نشده است."
            )
        return value


# =========== PASSWORD RESET BY PHONE - STEP 2 =========== #
class PasswordResetByPhoneConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=15, required=True,
        error_messages={"required": "شماره موبایل الزامی است."}
    )
    code = serializers.CharField(
        max_length=5, min_length=5, required=True,
        error_messages={
            "required": "کد تایید الزامی است.",
            "min_length": "کد تایید باید ۵ رقم باشد.",
            "max_length": "کد تایید باید ۵ رقم باشد.",
        }
    )
    password = serializers.CharField(
        write_only=True, required=True,
        style={'input_type': 'password'},
        error_messages={
            "required": "وارد کردن رمز عبور جدید الزامی است.",
            "blank": "رمز عبور نمی‌تواند خالی باشد.",
        }
    )
    password_confirm = serializers.CharField(
        write_only=True, required=True,
        style={'input_type': 'password'},
        error_messages={
            "required": "وارد کردن تکرار رمز عبور الزامی است.",
            "blank": "تکرار رمز عبور نمی‌تواند خالی باشد.",
        }
    )

    def validate_phone_number(self, value):
        value = re.sub(r'\D', '', value)
        if not re.match(r'^09\d{9}$', value):
            raise serializers.ValidationError("فرمت شماره موبایل صحیح نیست.")
        return value

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("کد تایید باید فقط شامل اعداد باشد.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'رمز عبور و تکرار آن باید یکسان باشند.'
            })
        return attrs
