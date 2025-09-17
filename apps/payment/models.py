# payments/models.py
from django.db import models
from django.conf import settings
from apps.subscriptions.models import Subscription

import uuid

# ======== Payment Status ======== #
class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'در انتظار پرداخت'
    COMPLETED = 'COMPLETED', 'تکمیل شده'
    FAILED = 'FAILED', 'ناموفق'
    CANCELLED = 'CANCELLED', 'لغو شده'

# ======== Payment Model ======== #
class Payment(models.Model):
    """
    مدل برای ثبت تمام تراکنش‌های مالی.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="شناسه تراکنش"
    )

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
    status = models.CharField(
        max_length=12,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="وضعیت پرداخت"
    )
    
    # ======= اطلاعات مالی ======= #
    amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="مبلغ (ریال)")
    discount_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        verbose_name="مبلغ تخفیف (ریال)"
    )
    final_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        verbose_name="مبلغ نهایی (ریال)"
    )
    
    authority = models.CharField(max_length=255, unique=True, verbose_name="کد رهگیری درگاه")
    ref_id = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        verbose_name="شماره مرجع تراکنش"
    )
    
    # ====== اطلاعات امنیتی از کاربر ====== #
    user_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name="آی‌پی کاربر"
    )
    user_agent = models.TextField(
        null=True, 
        blank=True,
        verbose_name="اطلاعات مرورگر"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد تراکنش")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ پرداخت")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['authority']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"پرداخت به مبلغ {self.amount} توسط {self.user.username} ({self.status})"
    
    @property
    def is_successful(self):
        return self.status == PaymentStatus.COMPLETED

    @property  
    def is_pending(self):
        return self.status == PaymentStatus.PENDING
    
    def save(self, *args, **kwargs):
        """ محاسبه مبلغ نهایی """
        if not self.final_amount:
            self.final_amount = self.amount - self.discount_amount
        super().save(*args, **kwargs)