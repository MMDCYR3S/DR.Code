from django.db import models
from .prescription import Prescription

import jdatetime


class Drug(models.Model):
    """
    مدل برای هر داروی تعریف شده در یک نسخه.
    هر نسخه می‌تواند شامل چندین دارو باشد.
    """
    title = models.CharField(max_length=150, verbose_name="نام دارو", unique=True)
    code = models.CharField(max_length=50, blank=True, verbose_name="کد دارو")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ساخت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='زمان بروزرسانی')

    def __str__(self):
        return f"داروی «{self.title}»"
    
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


class PrescriptionDrug(models.Model):
    """
    مدل میانی برای تعریف جزئیات یک دارو در یک نسخه خاص
    """
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        verbose_name="نسخه مرجع"
    )
    drug = models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        verbose_name="داروی انتخابی"
    )
    dosage = models.CharField(max_length=200, verbose_name="دوز و نحوه مصرف")
    amount = models.IntegerField(default=1, verbose_name="مقدار دارو")
    instructions = models.TextField(blank=True, verbose_name="توضیحات کوتاه دارو")
    is_combination = models.BooleanField(
        default=False,
        verbose_name='جزء داروی ترکیبی است؟',
        help_text='این گزینه را برای داروهایی که باید با هم ترکیب شوند، فعال کنید'
    )
    is_substitute = models.BooleanField(
        default=False,
        verbose_name='داروی جایگزین',
        help_text='این گزینه را برای داروهایی که می‌توانند با یکدیگر جایگزین شوند، فعال کنید'
    )
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    group_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="شماره گروه دارویی",
        help_text="برای گروه‌بندی داروها در یک نسخه استفاده می‌شود"
    )

    class Meta:
        ordering = ['order']
        
    def get_truncated_instructions(self, length=50):
        """ توضیحات کوتاه شده """
        if not self.instructions:
            return ''
        return self.instructions[:length] + '...' if len(self.instructions) > length else self.instructions

    def __str__(self):
        group_info = f" (گروه {self.group_number})" if self.group_number else ""
        return f"داروی «{self.drug.title}» در نسخه «{self.prescription.title}»{group_info}"