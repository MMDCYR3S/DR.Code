# payments/models.py
from django.db import models
from django.conf import settings
from subscriptions.models import Subscription

# ======== Payment Status ======== #
class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'در انتظار پرداخت'
    COMPLETED = 'COMPLETED', 'تکمیل شده'
    FAILED = 'FAILED', 'ناموفق'

# ======== Payment Model ======== #
class Payment(models.Model):
    """
    مدل برای ثبت تمام تراکنش‌های مالی.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments',
        verbose_name="کاربر"
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name="اشتراک مربوطه"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="مبلغ (تومان)")
    status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="وضعیت پرداخت"
    )
    authority = models.CharField(max_length=255, unique=True, verbose_name="کد رهگیری درگاه")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد تراکنش")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"پرداخت به مبلغ {self.amount} توسط {self.user.username} ({self.status})"