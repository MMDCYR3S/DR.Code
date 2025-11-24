from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid

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
    
    # اضافه کردن validator برای شماره تلفن
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
    
    # تاریخ ثبت‌نام
    date_joined = models.DateTimeField('تاریخ ثبت‌نام', default=timezone.now)
    
    # وضعیت فعال/غیرفعال
    is_active = models.BooleanField('فعال', default=True)
    
    active_jti = models.CharField(max_length=255, null=True, blank=True, unique=True, db_index=True)
    # آخرین ورود
    last_login_ip = models.GenericIPAddressField('آی پی آخرین ورود', blank=True, null=True)
    last_login_device = models.CharField('دستگاه آخرین ورود', max_length=255, blank=True, null=True)
    
    # استفاده از phone_number به عنوان username
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']
    
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
            # تولید username یکتا بر اساس phone_number
            self.username = self.phone_number
        super().save(*args, **kwargs)
        
    def has_active_membership(self):
        """
        بررسی بهینه برای اینکه کاربر اشتراک فعال دارد یا نه.
        """
        
        if self.is_staff or self.is_superuser:
            return True
        
        return self.subscriptions.filter(
            status=SubscriptionStatusChoicesModel.active.value,
            end_date__gte=timezone.now()
        ).exists()
            