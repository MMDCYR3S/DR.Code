from django.db import models

from .membership import Membership

# ========= Plan Model ========= #
class Plan(models.Model):
    """
    بسته‌های قابل خرید را تعریف می‌کند (مثلا: بسته ۱ ماهه برای اشتراک پریمیوم).
    """
    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name='plans',
        verbose_name="برای کدام نوع اشتراک؟"
    )
    name = models.CharField(max_length=100, verbose_name="نام بسته")
    duration_days = models.PositiveIntegerField(verbose_name="مدت زمان (به روز)")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="قیمت (تومان)")
    is_active = models.BooleanField(default=True, verbose_name="بسته فعال است؟")

    class Meta:
        # جلوگیری از تعریف دو بسته با مدت زمان یکسان برای یک نوع اشتراک
        unique_together = ('membership', 'duration_days') 
        ordering = ['duration_days']

    def __str__(self):
        return f"{self.membership.name} - {self.name}"