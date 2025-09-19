from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import FileExtensionValidator
from apps.accounts.models import Profile
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


# ============= Authentication Serializer ============= #
class AuthenticationSerializer(serializers.Serializer):
    """سریالایزر احراز هویت پزشکی"""
    
    medical_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=50,
        help_text='کد نظام پزشکی یا کد دانشجویی'
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
    
    documents = serializers.ListField(
        child = serializers.FileField(
            allow_empty_file=False,
            validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf'])]
        ),
        required=True,
        help_text="تصاویر مربوط به احراز هویت"
    )

    def validate(self, attrs):
        """اعتبارسنجی کلی - حداقل یکی از فیلدها باید پر باشد"""
        medical_code = attrs.get('medical_code', '').strip()
        documents = attrs.get('documents')
        auth_link = attrs.get('auth_link', '').strip()
        
        if not any([medical_code, documents, auth_link]):
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

    def validate_documents(self, value):
        """اعتبارسنجی هر فایل در لیست مدارک ارسالی"""
        for file in value:
            if file.size > 2 * 1024 * 1024:
                raise serializers.ValidationError(
                    f'حجم فایل "{file.name}" نباید بیش از 2 مگابایت باشد.'
                )

            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
            if file.content_type not in allowed_types:
                raise serializers.ValidationError(
                    f'فرمت فایل "{file.name}" مجاز نیست. فقط فایل‌های JPG, PNG, PDF پشتیبانی می‌شوند.'
                )
        return value
