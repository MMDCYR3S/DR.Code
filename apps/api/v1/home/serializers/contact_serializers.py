# api/v1/home/serializers.py

from rest_framework import serializers
from apps.home.models import Contact
import re
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError as DjangoValidationError

class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer برای ایجاد پیام تماس با ما
    """
    full_name = serializers.CharField(
        max_length=150,
        required=True,
        help_text="نام و نام خانوادگی"
    )
    email = serializers.EmailField(
        required=True,
        help_text="ایمیل برای پاسخ"
    )
    phone = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
        help_text="شماره تماس (اختیاری)"
    )
    subject = serializers.ChoiceField(
        choices=Contact.SUBJECT_CHOICES,
        required=True,
        help_text="موضوع پیام"
    )
    custom_subject = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text="موضوع سفارشی (در صورت انتخاب 'سایر موارد')"
    )
    message = serializers.CharField(
        style={'base_template': 'textarea.html'},
        required=True,
        help_text="متن پیام"
    )

    class Meta:
        model = Contact
        fields = [
            'full_name', 'email', 'phone', 'subject', 
            'custom_subject', 'message'
        ]

    def validate_full_name(self, value):
        """اعتبارسنجی نام و نام خانوادگی"""
        value = value.strip()
        
        if len(value) < 2:
            raise serializers.ValidationError("نام باید حداقل ۲ کاراکتر باشد.")
        
        if len(value) > 150:
            raise serializers.ValidationError("نام نباید بیشتر از ۱۵۰ کاراکتر باشد.")
        
        # بررسی فقط حروف فارسی، انگلیسی و فاصله
        if not re.match(r'^[a-zA-Zآ-ی\s]+$', value):
            raise serializers.ValidationError("نام فقط می‌تواند شامل حروف فارسی و انگلیسی باشد.")
        
        return value

    def validate_email(self, value):
        """اعتبارسنجی ایمیل"""
        if not value:
            raise serializers.ValidationError("ایمیل الزامی است.")
        
        # استفاده از validator داخلی جنگو
        validator = EmailValidator()
        try:
            validator(value)
        except DjangoValidationError:
            raise serializers.ValidationError("فرمت ایمیل صحیح نیست.")
        
        return value.lower().strip()

    def validate_phone(self, value):
        """اعتبارسنجی شماره تلفن"""
        if not value:  # اختیاری است
            return value
        
        # پاک کردن کاراکترهای اضافی
        phone_clean = re.sub(r'[\s\-\(\)]+', '', value)
        
        # بررسی فرمت شماره موبایل ایرانی
        if not re.match(r'^(\+98|0)?9\d{9}$', phone_clean):
            raise serializers.ValidationError("شماره تلفن معتبر وارد کنید. (مثال: 09123456789)")
        
        # استاندارد کردن فرمت
        if phone_clean.startswith('+98'):
            phone_clean = '0' + phone_clean[3:]
        elif phone_clean.startswith('98'):
            phone_clean = '0' + phone_clean[2:]
        elif not phone_clean.startswith('0'):
            phone_clean = '0' + phone_clean
        
        return phone_clean

    def validate_message(self, value):
        """اعتبارسنجی متن پیام"""
        value = value.strip()
        
        if len(value) < 10:
            raise serializers.ValidationError("پیام باید حداقل ۱۰ کاراکتر باشد.")
        
        if len(value) > 2000:
            raise serializers.ValidationError("پیام نباید بیشتر از ۲۰۰۰ کاراکتر باشد.")
        
        return value

    def validate(self, attrs):
        """اعتبارسنجی کل فرم"""
        # اگر موضوع "سایر موارد" انتخاب شده، موضوع سفارشی الزامی است
        if attrs.get('subject') == 'other':
            custom_subject = attrs.get('custom_subject', '').strip()
            if not custom_subject:
                raise serializers.ValidationError({
                    'custom_subject': 'برای موضوع "سایر موارد" باید موضوع سفارشی وارد کنید.'
                })
            
            if len(custom_subject) < 3:
                raise serializers.ValidationError({
                    'custom_subject': 'موضوع سفارشی باید حداقل ۳ کاراکتر باشد.'
                })
        
        return attrs

    def create(self, validated_data):
        """ایجاد پیام جدید"""
        # اگر کاربر وارد شده، آن را به پیام متصل کنیم
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        return super().create(validated_data)


class ContactListSerializer(serializers.ModelSerializer):
    """
    Serializer برای نمایش لیست پیام‌ها (برای ادمین)
    """
    subject_display = serializers.CharField(source='subject_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = [
            'id', 'full_name', 'email', 'phone', 'subject', 'subject_display',
            'custom_subject', 'message', 'status', 'status_display',
            'user_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_display(self, obj):
        """نمایش اطلاعات کاربر"""
        if obj.user:
            return {
                'id': obj.user.id,
                'phone_number': obj.user.phone_number,
                'full_name': obj.user.full_name
            }
        return None
