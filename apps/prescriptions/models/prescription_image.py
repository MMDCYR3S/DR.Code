from django.db import models

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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ساخت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='زمان بروزرسانی')

    def __str__(self):
        return f"تصویر برای نسخه «{self.prescription.title}»"