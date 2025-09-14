from django.db import models
from django.utils import timezone
from django.conf import settings
        
from .plan import Plan

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
    start_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ شروع")
    end_date = models.DateTimeField(verbose_name="تاریخ انقضا")

    class Meta:
        verbose_name = "اشتراک کاربر"
        verbose_name_plural = "اشتراک‌های کاربران"
        ordering = ['-end_date']

    @property
    def is_active(self):
        """
        به صورت دینامیک وضعیت فعال بودن اشتراک را برمی‌گرداند.
        """
        return self.end_date > timezone.now()

    def __str__(self):
        return f"اشتراک {self.user.username} برای پلن {self.plan.name}"
