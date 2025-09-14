from django.db import models
from django.contrib.auth import get_user_model

import secrets
import string

User = get_user_model()

# ======= Random Code Generator ======= #
def generate_referral_code(length=7):
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(characters) for i in range(length))
        if not Profile.objects.filter(referral_code=code).exists():
            return code

# ======= Profile Model ======= #
class Profile(models.Model):
    """
    این مدل بدون تغییر باقی می‌ماند و برای احراز هویت استفاده می‌شود.
    """
    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار تایید'
        VERIFIED = 'VERIFIED', 'تایید شده'
        REJECTED = 'REJECTED', 'رد شده'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="کاربر"
    )
    image = models.ImageField(verbose_name="تصویر پروفایل", upload_to="profile_images/")
    medical_id_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="کد نظام پزشکی")
    student_id_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="کد دانشجویی")
    verification_document = models.ImageField(upload_to='verifications/', verbose_name="مدرک احراز هویت")
    medical_profile_link = models.URLField(blank=True, null=True, verbose_name="لینک پروفایل نظام پزشکی")
    verification_status = models.CharField(
        max_length=10,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        verbose_name="وضعیت تایید"
    )

    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True, verbose_name="کد معرف")
    referred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        verbose_name="معرف"
    )

    def __str__(self):
        return f"پروفایل کاربری {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.referral_code:
            self.referral_code = generate_referral_code()
        return super().save(*args, **kwargs)