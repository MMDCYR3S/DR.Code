import jdatetime
import logging

from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .prescription import Prescription

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
    image = models.ImageField(upload_to='prescriptions/images/', verbose_name="فایل تصویر")
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
        """Override save برای فشرده‌سازی"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if self.image and not self.is_compressed:
            print(f"Calling compression from save() for image {self.id}")
            
            from apps.prescriptions.tasks import compress_prescription_image
            from django.db import transaction
            
            def run_compression():
                print(f"Task.delay({self.id})")
                compress_prescription_image.delay(self.id)
            
            transaction.on_commit(run_compression)
