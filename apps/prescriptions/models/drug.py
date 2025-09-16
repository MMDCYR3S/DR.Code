from django.db import models
from .prescription import Prescription

class PrescriptionDrug(models.Model):
    """
    مدل برای هر داروی تعریف شده در یک نسخه.
    هر نسخه می‌تواند شامل چندین دارو باشد.
    """
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='drugs',
        verbose_name="نسخه مرجع"
    )
    title = models.CharField(max_length=150, verbose_name="نام دارو")
    code = models.CharField(max_length=50, blank=True, verbose_name="کد دارو")
    dosage = models.CharField(max_length=200, verbose_name="دوز و نحوه مصرف")
    amount = models.IntegerField(default=0, verbose_name="مقدار دارو")
    instructions = models.TextField(blank=True, verbose_name="توضیحات کوتاه دارو")
    is_combination = models.BooleanField(
        default=False,
        verbose_name='دارویی ترکیبی',
        help_text='آیا این دارو جزء گروه داروهای ترکیبی است؟'
    )
    combination_group = models.CharField(
        max_length=50,
        blank=True,
        help_text="برای گروه‌بندی بصری داروها با رنگ یکسان (مثلا: antibiotics-group)",
        verbose_name="گروه دارویی"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ساخت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='زمان بروزرسانی')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"داروی «{self.title}» در نسخه «{self.prescription.title}»"
    
    def get_truncated_instructions(self, length=50):
        """ توضیحات کوتاه شده """
        if not self.instructions:
            return ''
        return self.instructions[:length] + '...' if len(self.instructions) > length else self.instructions
