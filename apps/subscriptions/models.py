from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import jdatetime
from slugify import slugify


# ========== Membership Model ========== #
class Membership(models.Model):
    """
    نوع اشتراک را تعریف می‌کند. در حال حاضر فقط یک رکورد به نام "پریمیوم" خواهد داشت.
    """
    title = models.CharField(max_length=100, unique=True, verbose_name="نام نوع اشتراک")
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    
    @property
    def shamsi_created_at(self):
        if self.created_at is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    class Meta:
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

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
    
    class Meta:
        app_label = 'subscriptions'
    
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
        app_label = 'subscriptions'
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
