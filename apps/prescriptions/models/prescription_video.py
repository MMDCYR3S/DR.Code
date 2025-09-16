from django.db import models

from .prescription import Prescription

# ========= Prescription Video Model ========= #
class PrescriptionVideo(models.Model):
    """
    مدل برای افزودن ویدیوهای مربوط به یک نسخه.
    هر نسخه می‌تواند چندین ویدیو داشته باشد.
    """
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name="نسخه مرجع"
    )
    video_url = models.URLField(verbose_name="لینک ویدیو (آپارات)")
    title = models.CharField(max_length=255, blank=True, verbose_name="عنوان ویدیو")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ساخت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='زمان بروزرسانی')

    def __str__(self):
        return f"ویدیو برای نسخه «{self.prescription.title}»"