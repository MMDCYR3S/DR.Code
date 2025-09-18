from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.core.validators import FileExtensionValidator
from django.dispatch import receiver

import uuid

User = get_user_model()

# ========== Auth Status Choices ========== #
class AuthStatusChoices(models.TextChoices):
    """ وضعیت احراز هویت کاربران """
    PENDING = "PENDING", _("در انتظار تایید")
    APPROVED = "APPROVED", _("تایید شده")
    REJECTED = "REJECTED", _("رد شده")

# ========== Get Auth Document Path  ========== #
def get_auth_document_path(instance, filename):
    """ تابعی برای تولید مسیر آپلود مدارک به صورت اختصاصی برای هر کاربر """
    return f'auth/documents/user_{instance.profile.user.id}/{filename}'

# ========== Authentication Document ========== #
class AuthenticationDocument(models.Model):
    """ مدلی برای نگهداری مدارک ارسالی جهت احراز هویت """
    profile = models.ForeignKey(
        'Profile', 
        on_delete=models.CASCADE, 
        related_name='documents',
        verbose_name=_("پروفایل")
    )
    file = models.FileField(
        upload_to=get_auth_document_path,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf'])],
        verbose_name=_("فایل مدرک")
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("زمان بارگذاری"))

    def __str__(self):
        return f"مدرک برای {self.profile.user.full_name}"

    class Meta:
        verbose_name = _("مدرک هویتی")
        verbose_name_plural = _("مدارک هویتی")

# ========== Profile Model ========== #
class Profile(models.Model):
    """
    مدل پروفایل برای نگهداری اطلاعات تکمیلی و وضعیت احراز هویت کاربران.
    """ 

    ROLE_CHOICES = [
        ('visitor', 'بازدیدکننده'),
        ('regular', 'کاربر عادی'),
        ('premium', 'کاربر ویژه'),
        ('admin', 'ادمین'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("کاربر")
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='visitor'
    )
    profile_image = models.ImageField(
        upload_to="profiles/images/",
        null=True,
        blank=True,
        help_text='عکس پروفایل کاربر',
        verbose_name=_("تصویر پروفایل")
    )
    medical_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("کد نظام پزشکی / دانشجویی")
    )
    
    auth_link = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("لینک پروفایل نظام پزشکی")
    )
    auth_status = models.CharField(
        max_length=10,
        choices=AuthStatusChoices.choices,
        default=AuthStatusChoices.PENDING.value,
        verbose_name=_("وضعیت احراز هویت")
    ) 
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("دلیل رد هویت")
    )
    referral_code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_("کد معرف")
    ) 
    referred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referred_users",
        verbose_name=_("معرفی شده توسط")
    )
    subscription_end_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاریخ ایجاد"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("تاریخ بروزرسانی"))

    def __str__(self):
        return f"پروفایل کاربری {self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4().hex[:8].upper()) 
        super().save(*args, **kwargs)
        
    def delete_profile_image(self):
        """حذف عکس پروفایل"""
        if self.profile_image:
            self.profile_image.delete(save=False)

# ========== User Profile Creation Signal ========== #
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    با ایجاد هر کاربر جدید، یک پروفایل خالی برای او به صورت خودکار ساخته می‌شود.
    """
    if created:
        Profile.objects.create(user=instance)

