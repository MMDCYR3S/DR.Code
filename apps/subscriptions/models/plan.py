from django.db import models

from .membership import Membership

import jdatetime

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
    price = models.IntegerField(default=0, verbose_name="قیمت (ریال)")
    is_active = models.BooleanField(default=True, verbose_name="بسته فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد") 
    
    @property
    def shamsi_created_at(self):
        if self.created_at is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")



    class Meta:
        # جلوگیری از تعریف دو بسته با مدت زمان یکسان برای یک نوع اشتراک
        unique_together = ('membership', 'duration_days') 
        ordering = ['duration_days']
        
    @property
    def duration_months(self):
        """محاسبه تعداد ماه بر اساس روزها"""
        return round(self.duration_days / 30)

    def __str__(self):
        return f"{self.membership.title} - {self.name}"