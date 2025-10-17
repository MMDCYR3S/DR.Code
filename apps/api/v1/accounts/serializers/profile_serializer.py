import re

from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.prescriptions.models import Prescription
from apps.accounts.models import Profile
from apps.questions.models import Question

User = get_user_model()

# ============= PROFILE SERIALIZER ============= #
class ProfileSerializer(serializers.ModelSerializer):
    """سریالایزر نمایش پروفایل"""
    
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    auth_status_display = serializers.CharField(source='get_auth_status_display', read_only=True)
    
    class Meta:
        model = Profile
        fields = (
            'user_full_name', 'user_phone', 'role', 'medical_code',
            'auth_status', 'auth_status_display', 'rejection_reason',
            'subscription_end_date', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'role', 'auth_status', 'rejection_reason', 
            'subscription_end_date', 'created_at', 'updated_at'
        )

# =============== UPDATE PROFILE SERIALIZER =============== #
class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Serializer برای بروزرسانی اطلاعات پروفایل
    """
    first_name = serializers.CharField(
        max_length=150,
        required=False,
        help_text="نام"
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        help_text="نام خانوادگی"
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="ایمیل"
    )
    phone_number = serializers.CharField(
        max_length=11,
        required=False,
        help_text="شماره تلفن همراه"
    )
    password = serializers.CharField(
        max_length=128,
        required=False,
        help_text="رمز عبور"
    )
    profile_image = serializers.ImageField(
        required=False,
        help_text="عکس پروفایل"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number','profile_image', "password"]

    def validate_first_name(self, value):
        """اعتبارسنجی نام"""
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError("نام باید حداقل ۲ کاراکتر باشد.")
        
        # بررسی فقط حروف فارسی و انگلیسی
        if value and not re.match(r'^[a-zA-Zآ-ی\s]+$', value.strip()):
            raise serializers.ValidationError("نام فقط می‌تواند شامل حروف فارسی و انگلیسی باشد.")
        
        return value.strip() if value else value

    def validate_last_name(self, value):
        """اعتبارسنجی نام خانوادگی"""
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError("نام خانوادگی باید حداقل ۲ کاراکتر باشد.")
        
        # بررسی فقط حروف فارسی و انگلیسی
        if value and not re.match(r'^[a-zA-Zآ-ی\s]+$', value.strip()):
            raise serializers.ValidationError("نام خانوادگی فقط می‌تواند شامل حروف فارسی و انگلیسی باشد.")
        
        return value.strip() if value else value

    def validate_email(self, value):
        """اعتبارسنجی ایمیل"""
        if not value:  # اگر خالی باشد مشکلی نیست
            return value
        
        # بررسی تکراری نبودن ایمیل
        user = self.context.get('request').user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("این ایمیل قبلاً استفاده شده است.")
        
        return value

    def validate_profile_image(self, value):
        """اعتبارسنجی عکس پروفایل"""
        if not value:
            return value
        
        # بررسی اندازه فایل (حداکثر 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("حجم عکس نباید بیشتر از ۵ مگابایت باشد.")
        
        # بررسی فرمت فایل
        allowed_formats = ['image/jpeg', 'image/png', 'image/jpg']
        if value.content_type not in allowed_formats:
            raise serializers.ValidationError("فرمت عکس باید JPG، JPEG یا PNG باشد.")
        
        # بررسی ابعاد تصویر
        from PIL import Image
        try:
            img = Image.open(value)
            width, height = img.size
            
            # حداقل ابعاد
            if width < 100 or height < 100:
                raise serializers.ValidationError("ابعاد عکس باید حداقل ۱۰۰×۱۰۰ پیکسل باشد.")
            
            # حداکثر ابعاد
            if width > 2000 or height > 2000:
                raise serializers.ValidationError("ابعاد عکس نباید بیشتر از ۲۰۰۰×۲۰۰۰ پیکسل باشد.")
                
        except Exception as e:
            raise serializers.ValidationError("فایل آپلود شده معتبر نیست.")
        
        return value

    def update(self, instance, validated_data):
        """بروزرسانی اطلاعات کاربر"""
        # فیلدهای مربوط به User model
        user_fields = ['first_name', 'last_name', 'email', 'phone_number', 'password']
        profile_fields = ['profile_image']
        
        updated_fields = []
        
        # بروزرسانی فیلدهای User
        for field in user_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
                updated_fields.append(field)
        
        # بروزرسانی فیلدهای Profile
        profile_data = {}
        for field in profile_fields:
            if field in validated_data:
                profile_data[field] = validated_data[field]
                updated_fields.append(field)
        
        # ذخیره User
        if any(field in validated_data for field in user_fields):
            instance.save(update_fields=[f for f in user_fields if f in validated_data])
        
        # ذخیره Profile
        if profile_data:
            profile = instance.profile
            for field, value in profile_data.items():
                setattr(profile, field, value)
            profile.save(update_fields=list(profile_data.keys()))
        
        return instance

# ========== SAVED PRESCRIPTION LIST SERIALIZER ========== #
class SavedPrescriptionListSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای نمایش لیست نسخه‌های ذخیره‌شده توسط کاربر، شامل لینک جزئیات.
    """
    category_title = serializers.CharField(source='category.title', read_only=True)
    detail_url = serializers.HyperlinkedIdentityField(
        view_name='api:v1:prescriptions_api:prescription-detail',
        lookup_field='slug'
    )
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'title', 'slug', 'category_title',
            'access_level',  'detail_url'
        ]
        
# ========== QUESTION LIST SERIALIZER ========== #
class QuestionListSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای نمایش سوالاتی که کاربر پرسیده و جواب هایی که دریافت کرده
    """
    
    prescription_title = serializers.StringRelatedField(source="prescription.title", read_only=True)
    category_title = serializers.StringRelatedField(source="prescription.category.title", read_only=True)
    answerer_name = serializers.CharField(source="answered_by.full_name", read_only=True)
    
    class Meta:
        model = Question
        fields = ["prescription_title", "category_title", "question_text", "answerer_name", "answer_text", "answered_at"]
