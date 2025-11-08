import os
import random
import logging
import jdatetime

from django.dispatch import receiver
from django.db import models, transaction
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from .prescription import Prescription

# ========== Helper: Random Number Generator ==========
def generate_random_number(length=6):
    """تولید عدد تصادفی با طول دلخواه (مثلاً ۶ رقمی)"""
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

# ========== Helper: Dynamic Upload Path ==========
def get_prescription_image_path(instance, filename):
    """
    ساخت مسیر و نام فایل به‌صورت:
    prescriptions/images/user_<id>/<username>_<id>_<rand>.<ext>
    """
    # دسترسی به کاربر از طریق نسخه
    user = instance.prescription.user
    username = user.username
    user_id = user.id

    # پسوند فایل
    ext = filename.split('.')[-1].lower()

    # عدد رندوم برای جلوگیری از تداخل نام‌ها
    random_number = generate_random_number()

    # نام جدید فایل
    new_filename = f"image_{random_number}.{ext}"

    # مسیر نهایی
    return os.path.join("prescriptions", "images", f"user_{user_id}", new_filename)

# ========= Prescription Image Model ========= #
class PrescriptionImage(models.Model):
    """
    مدل برای آپلود تصاویر مربوط به یک نسخه.
    هر نسخه می‌تواند چندین تصویر داشته باشد.
    """
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="نسخه مرجع"
    )
    image = models.ImageField(upload_to=get_prescription_image_path, verbose_name="فایل تصویر")
    caption = models.CharField(max_length=255, blank=True, verbose_name="کپشن تصویر")
    is_compressed = models.BooleanField(default=False, verbose_name="فشرده شده؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ساخت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='زمان بروزرسانی')
    
    @property
    def shamsi_created_at(self):
        if self.created_at is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    @property
    def shamsi_updated_at(self):
        if self.updated_at is None:
            return "—"
            
        jdate = jdatetime.datetime.fromgregorian(datetime=self.updated_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")


    def __str__(self):
        return f"تصویر برای نسخه «{self.prescription.title}»"

    def save(self, *args, **kwargs):
        """
        ذخیره‌ی سفارشی:
        - مسیر آپلود سفارشی دارد
        - بعد از ذخیره، تسک فشرده‌سازی را در صف قرار می‌دهد
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)