from django.db import models

from .prescription import Prescription

import jdatetime

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