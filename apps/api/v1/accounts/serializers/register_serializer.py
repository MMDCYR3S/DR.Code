from rest_framework import serializers

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.accounts.models import User, Profile

# ========== User Registration Serializer ========== #
class UserRegisterSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای مرحله اول ثبت‌نام.
    اطلاعات پایه کاربر را دریافت کرده و یک کاربر غیرفعال ایجاد می‌کند.
    """
    
    password2 = serializers.CharField(style={"input_type": "password"}, write_only=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "password", "password2"]
        extra_kwargs = {
            "password": {"write_only": True, "validators": [validate_password]},
        }
        
    def validate(self, attrs):
        """ تطابق رمز عبور و تکرار آن """
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "رمزهای عبور وارد شده با یکدیگر تطابق ندارند."})
        return attrs
    
    def create(self, validated_data):
        """ حذف تکرار رمز عبور و ایجاد کاربر """
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user

# ============== User Profile Verification Serializer ============== #
class UserProfileVerificationSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای مرحله دوم ثبت‌نام (احراز هویت).
    مدارک کاربر را دریافت کرده و پروفایل او را به‌روزرسانی می‌کند.
    """
    
    class Meta:
        model = Profile
        fields = ["medical_code", "auth_image", "auth_link"]
        
    def validate(self, attrs):
        """ بر اساس مستند، کاربر باید حداقل یکی از این فیلدها را پر کند. """
        if not any(attrs.values()):
            raise serializers.ValidationError(
                "برای احراز هویت، لطفاً حداقل یکی از فیلدهای کد نظام پزشکی، تصویر مدرک یا لینک پروفایل را ارسال کنید."
            )
        return attrs
    
    def update(self, instance, validated_data):
        """
        مستند اشاره می‌کند که کاربر در این مرحله هنوز "در انتظار تایید" است.
        وضعیت auth_status به صورت پیش‌فرض PENDING است و نیازی به تغییر ندارد.
        """
        instance.medical_code = validated_data.get('medical_code', instance.medical_code)
        instance.auth_image = validated_data.get('auth_image', instance.auth_image)
        instance.auth_link = validated_data.get('auth_link', instance.auth_link)
        instance.save()
        return instance
    