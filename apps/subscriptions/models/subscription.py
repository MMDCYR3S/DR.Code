from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
        
from .plan import Plan

import jdatetime

# ========= Subscription Status Choices Model ========= # 
class SubscriptionStatusChoicesModel(models.TextChoices):
    """ وضعیت اشتراک کاربر """
    pending = "PENDING", _("در انتظار پرداخت")
    active = "ACTIVE", _("فعال")
    expired = "EXPIRED", _("منقضی‌شده")
    canceled = "CANCELED", _("لغو شده")

# ========= Subscription Model ========= #
class Subscription(models.Model):
    """
    مدل برای ثبت اشتراک هر کاربر.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="کاربر"
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name="پلن"
    )
    payment_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        verbose_name="مبلغ پرداختی (ریال)",
        help_text="مبلغ واقعی که کاربر پرداخت کرده (بعد از تخفیف)"
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatusChoicesModel.choices,
        default=SubscriptionStatusChoicesModel.pending.value,
        verbose_name="وضعیت اشتراک"
    )
    
    start_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ شروع")
    end_date = models.DateTimeField(verbose_name="تاریخ انقضا")
    
    @property
    def shamsi_start_date(self):
        if self.start_date is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.start_date)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    @property
    def shamsi_end_date(self):
        if self.end_date is None:
            return "—"
            
        jdate = jdatetime.datetime.fromgregorian(datetime=self.end_date)
        return jdate.strftime("%Y/%m/%d - %H:%M")


    class Meta:
        verbose_name = "اشتراک کاربر"
        verbose_name_plural = "اشتراک‌های کاربران"
        ordering = ['-end_date']
        indexes = [ 
            models.Index(fields=['user', '-end_date']),
            models.Index(fields=['end_date', 'status']),
        ]

    @property
    def is_active(self):
        """
        به صورت دینامیک وضعیت فعال بودن اشتراک را برمی‌گرداند.
        """
        return self.end_date > timezone.now() and self.status == SubscriptionStatusChoicesModel.active

    @property
    def days_remaining(self):
        """محاسبه روزهای باقی‌مانده تا انقضا"""
        if self.is_active:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    def save(self, *args, **kwargs):
        """بروزرسانی خودکار status بر اساس تاریخ انقضا"""
        if self.end_date <= timezone.now() and self.status == SubscriptionStatusChoicesModel.active:
            self.status = SubscriptionStatusChoicesModel.expired
        super().save(*args, **kwargs)

    def __str__(self):
        return f"اشتراک {self.user.username} برای پلن {self.plan.name}"
