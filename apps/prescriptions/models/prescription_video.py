from django.db import models

from .prescription import Prescription

import jdatetime

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
        return f"ویدیو برای نسخه «{self.prescription.title}»"