# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.core.cache import cache

import jdatetime

from apps.subscriptions.models import SubscriptionStatusChoicesModel

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where phone number is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, phone_number, password, **extra_fields):
        """
        Create and save a User with the given phone number and password.
        """
        if not phone_number:
            raise ValueError(_('The Phone Number must be set'))
            
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        """
        Create and save a SuperUser with the given phone number and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
            
        return self.create_user(phone_number, password, **extra_fields)

# ============= User Model ============= #
class User(AbstractUser):
    """مدل کاربر سفارشی"""
    
    # فیلدهای اصلی
    first_name = models.CharField('نام', max_length=30)
    last_name = models.CharField('نام خانوادگی', max_length=30)
    email = models.EmailField('ایمیل', unique=True)
    
    saved_prescriptions = models.ManyToManyField(
        'prescriptions.Prescription',
        related_name='savers',
        blank=True,
        verbose_name='نسخه‌های ذخیره‌شده'
    )
    
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',
        message="شماره تلفن باید با 09 شروع شده و 11 رقم باشد."
    )
    phone_number = models.CharField(
        'شماره تلفن همراه',
        validators=[phone_regex],
        max_length=11,
        unique=True
    )
    is_phone_verified = models.BooleanField('تایید شماره تلفن', default=False)
    
    date_joined = models.DateTimeField('تاریخ ثبت‌نام', default=timezone.now)
    is_active = models.BooleanField('فعال', default=True)
    
    active_jti = models.CharField(max_length=255, null=True, blank=True, unique=True, db_index=True)
    last_login_ip = models.GenericIPAddressField('آی پی آخرین ورود', blank=True, null=True)
    last_login_device = models.CharField('دستگاه آخرین ورود', max_length=255, blank=True, null=True)
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        db_table = 'accounts_user'
        
    @property
    def shamsi_date_joined(self):
        if self.date_joined is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.date_joined)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.phone_number}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        """Override save method to generate unique username"""
        if not self.username:
            self.username = self.phone_number
        super().save(*args, **kwargs)
        
    def has_active_membership(self):
        """
        بررسی اینکه آیا کاربر حداقل یک اشتراک فعال (از هر نوعی) دارد یا خیر.
        با کش برای بهینه‌سازی.
        """
        if self.is_staff or self.is_superuser:
            return True
        
        cache_key = f"user_{self.id}_has_active_membership"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        has_active = self.subscriptions.filter(
            status=SubscriptionStatusChoicesModel.active,
            end_date__gte=timezone.now()
        ).exists()
        
        # کش برای 5 دقیقه
        cache.set(cache_key, has_active, 300)
        return has_active

    def has_feature_access(self, feature_type):
        """
        بررسی اینکه آیا کاربر به یک فیچر خاص دسترسی دارد یا خیر.
        
        Args:
            feature_type: یکی از مقادیر FeatureType (مثلا FeatureType.PRESCRIPTION_ACCESS)
        
        Returns:
            bool: True اگر دسترسی داشته باشد، False در غیر این صورت
        """
        if self.is_staff or self.is_superuser:
            return True
        
        cache_key = f"user_{self.id}_feature_{feature_type}"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
            
        has_access = self.subscriptions.filter(
            status=SubscriptionStatusChoicesModel.active,
            end_date__gte=timezone.now(),
            plan__membership__features__feature_type=feature_type,
            plan__membership__features__is_active=True
        ).exists()
        
        # کش برای 5 دقیقه
        cache.set(cache_key, has_access, 300)
        return has_access
    
    def get_active_features(self):
        """
        لیست تمام فیچرهایی که کاربر به آن‌ها دسترسی دارد را برمی‌گرداند.
        
        Returns:
            QuerySet: لیست Feature هایی که کاربر دسترسی دارد
        """
        if self.is_staff or self.is_superuser:
            from apps.subscriptions.models import Feature
            return Feature.objects.filter(is_active=True)
        
        cache_key = f"user_{self.id}_active_features"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        from apps.subscriptions.models import Feature
        
        features = Feature.objects.filter(
            memberships__plans__subscriptions__user=self,
            memberships__plans__subscriptions__status=SubscriptionStatusChoicesModel.active,
            memberships__plans__subscriptions__end_date__gte=timezone.now(),
            is_active=True
        ).distinct()
        
        # کش برای 5 دقیقه
        cache.set(cache_key, features, 300)
        return features
    
    def get_feature_status_dict(self):
        """
        دیکشنری از وضعیت دسترسی به هر فیچر را برمی‌گرداند.
        
        Returns:
            dict: {'prescription_access': True, 'ordering_access': False, ...}
        """
        from apps.subscriptions.models import FeatureType
        
        return {
            feature_type: self.has_feature_access(feature_type)
            for feature_type, _ in FeatureType.choices
        }
    
    def clear_feature_cache(self):
        """
        کش مربوط به فیچرها و اشتراک کاربر را پاک می‌کند.
        باید بعد از خرید یا انقضای اشتراک فراخوانی شود.
        """
        from apps.subscriptions.models import FeatureType
        
        cache.delete(f"user_{self.id}_has_active_membership")
        cache.delete(f"user_{self.id}_active_features")
        
        for feature_type, _ in FeatureType.choices:
            cache.delete(f"user_{self.id}_feature_{feature_type}")
