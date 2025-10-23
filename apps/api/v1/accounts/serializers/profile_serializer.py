import re
from PIL import Image

from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.prescriptions.models import Prescription
from apps.accounts.models import Profile
from apps.questions.models import Question
from apps.prescriptions.models import Prescription

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
        
    def to_representation(self, instance):
        """تبدیل تاریخ پایان اشتراک به تعداد روز باقی‌مانده"""
        data = super().to_representation(instance)
        if instance.subscription_end_date:
            remaining = instance.subscription_end_date - timezone.now()
            data['subscription_end_date'] = max(remaining.days, 0)
        else:
            data['subscription_end_date'] = None
        return data
        

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
    # <<< تغییر: چون این یک آپدیت جزئی (PATCH) است، بهتر است این فیلد الزامی نباشد
    phone_number = serializers.CharField(
        required=False, 
        max_length=11,
        help_text="شماره تلفن"
    )
    # <<< تغییر: افزودن write_only=True برای امنیت
    password = serializers.CharField(
        max_length=128,
        required=False,
        write_only=True,
        allow_blank=True,
        help_text="در صورت تمایل به تغییر، رمز عبور جدید را وارد کنید. در غیر این صورت، آن را خالی بگذارید."
    )
    profile_image = serializers.ImageField(
        required=False,
        help_text="عکس پروفایل",
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_image', 'password']
        extra_kwargs = {
            'phone_number': {'validators': []}, # اگر ولیدیتور یونیک در مدل دارید، اینجا غیرفعالش کنید تا در آپدیت خطا ندهد
        }

    # ... (متدهای validate شما بدون تغییر باقی می‌مانند) ...
    def validate_first_name(self, value):
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError("نام باید حداقل ۲ کاراکتر باشد.")
        if value and not re.match(r'^[a-zA-Zآ-ی\s]+$', value.strip()):
            raise serializers.ValidationError("نام فقط می‌تواند شامل حروف فارسی و انگلیسی باشد.")
        return value.strip() if value else value

    def validate_last_name(self, value):
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError("نام خانوادگی باید حداقل ۲ کاراکتر باشد.")
        if value and not re.match(r'^[a-zA-Zآ-ی\s]+$', value.strip()):
            raise serializers.ValidationError("نام خانوادگی فقط می‌تواند شامل حروف فارسی و انگلیسی باشد.")
        return value.strip() if value else value

    def validate_email(self, value):
        if not value:
            return value
        user = self.context.get('request').user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("این ایمیل قبلاً استفاده شده است.")
        return value

    def validate_profile_image(self, value):
        if not value:
            return value
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("حجم عکس نباید بیشتر از ۵ مگابایت باشد.")
        allowed_formats = ['image/jpeg', 'image/png', 'image/jpg']
        if value.content_type not in allowed_formats:
            raise serializers.ValidationError("فرمت عکس باید JPG، JPEG یا PNG باشد.")
        try:
            img = Image.open(value)
            width, height = img.size
            if width < 100 or height < 100:
                raise serializers.ValidationError("ابعاد عکس باید حداقل ۱۰۰×۱۰۰ پیکسل باشد.")
            if width > 2000 or height > 2000:
                raise serializers.ValidationError("ابعاد عکس نباید بیشتر از ۲۰۰۰×۲۰۰۰ پیکسل باشد.")
        except Exception:
            raise serializers.ValidationError("فایل آپلود شده معتبر نیست.")
        return value

    # <<< تغییر اصلی: بازنویسی کامل متد update
    def update(self, instance, validated_data):
        """بروزرسانی اطلاعات کاربر و پروفایل او"""
        

        profile_image_data = validated_data.pop('profile_image', None)
        password = validated_data.pop('password', None)
        
        instance = super().update(instance, validated_data)
        
        if password:
            instance.set_password(password)
            instance.save(update_fields=['password'])

        # بروزرسانی عکس پروفایل در مدل Profile
        if profile_image_data is not None:
            profile = instance.profile
            profile.profile_image = profile_image_data
            profile.save(update_fields=['profile_image'])

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
    prescription_url = serializers.SerializerMethodField()
    class Meta:
        model = Question
        fields = ["prescription_title", "category_title", "question_text", "answerer_name", "answer_text", "answered_at", 'prescription_url',]
        
    def get_prescription_url(self, obj):
        """ایجاد hyperlink به جزئیات نسخه مربوط به اعلان"""
        if not obj.prescription:
            return None

        request = self.context.get('request')
        url = reverse('prescriptions:prescription_detail', kwargs={'slug': obj.prescription.slug})
        return request.build_absolute_uri(url) if request else url
