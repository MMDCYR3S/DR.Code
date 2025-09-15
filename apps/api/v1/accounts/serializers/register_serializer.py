from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from apps.accounts.models import Profile, AuthStatusChoices
import re

User = get_user_model()

# ======== Register Serializer ======== #
class RegisterSerializer(serializers.ModelSerializer):
    """سریالایزر ثبت‌نام کاربر"""
    
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='رمز عبور باید حداقل ۸ کاراکتر باشد'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='تکرار رمز عبور'
    )
    
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'phone_number', 
            'email', 'password', 'password_confirm'
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'phone_number': {'required': True},
            'email': {'required': False},
        }

    def validate_phone_number(self, value):
        """اعتبارسنجی شماره تلفن"""
        if not re.match(r'^09\d{9}$', value):
            raise serializers.ValidationError(
                "شماره تلفن باید با 09 شروع شده و 11 رقم باشد."
            )
        
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "کاربری با این شماره تلفن قبلاً ثبت‌نام کرده است."
            )
        return value

    def validate_email(self, value):
        """اعتبارسنجی ایمیل"""
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "کاربری با این ایمیل قبلاً ثبت‌نام کرده است."
            )
        return value

    def validate_password(self, value):
        """اعتبارسنجی رمز عبور"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """اعتبارسنجی کلی"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'رمزهای عبور مطابقت ندارند.'
            })
        
        # بررسی نام و نام خانوادگی
        if len(attrs['first_name'].strip()) < 2:
            raise serializers.ValidationError({
                'first_name': 'نام باید حداقل ۲ کاراکتر باشد.'
            })
        
        if len(attrs['last_name'].strip()) < 2:
            raise serializers.ValidationError({
                'last_name': 'نام خانوادگی باید حداقل ۲ کاراکتر باشد.'
            })
        
        return attrs

    def create(self, validated_data):
        """ایجاد کاربر جدید"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            username=validated_data['phone_number'],
            password=password,
            **validated_data
        )
        return user


class AuthenticationSerializer(serializers.Serializer):
    """سریالایزر احراز هویت پزشکی"""
    
    medical_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=50,
        help_text='کد نظام پزشکی یا کد دانشجویی'
    )
    auth_image = serializers.ImageField(
        required=False,
        allow_empty_file=False,
        help_text='تصویر کارت نظام پزشکی یا کارت دانشجویی'
    )
    auth_link = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text='لینک پروفایل نظام پزشکی'
    )
    referral_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=10,
        help_text='کد معرف (اختیاری)'
    )

    def validate(self, attrs):
        """اعتبارسنجی کلی - حداقل یکی از فیلدها باید پر باشد"""
        medical_code = attrs.get('medical_code', '').strip()
        auth_image = attrs.get('auth_image')
        auth_link = attrs.get('auth_link', '').strip()
        
        if not any([medical_code, auth_image, auth_link]):
            raise serializers.ValidationError(
                'حداقل یکی از موارد زیر را وارد کنید: کد پزشکی، تصویر مدرک یا لینک پروفایل'
            )
        
        return attrs

    def validate_referral_code(self, value):
        """اعتبارسنجی کد معرف"""
        if value:
            value = value.strip().upper()
            if not Profile.objects.filter(referral_code=value).exists():
                raise serializers.ValidationError('کد معرف وارد شده معتبر نیست.')
        return value

    def validate_auth_image(self, value):
        """اعتبارسنجی تصویر احراز هویت"""
        if value:
            # بررسی حجم فایل (حداکثر 5 مگابایت)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    'حجم تصویر نباید بیش از ۵ مگابایت باشد.'
                )
            
            # بررسی نوع فایل
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    'فقط فایل‌های JPG، JPEG و PNG مجاز هستند.'
                )
        
        return value
