# marketing/models.py
from django.db import models
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
        
import secrets
import string

# ========= Random Code Generator ========= #
def generate_random_code(length=8, max_attempt=100):
    """ یک کد تصادفی منحصر به فرد ایجاد می‌کند """
    characters = string.ascii_uppercase + string.digits
    for attempt in range(max_attempt):
        code = ''.join(secrets.choice(characters) for i in range(length))
        if not DiscountCode.objects.filter(code=code).exists():
            return code
    raise ValidationError("امکان ایجاد کد یکتا وجود ندارد. لطفاً دوباره تلاش کنید.")
# ========= Discount Code ========= #
class DiscountCode(models.Model):
    """
    مدل برای مدیریت کدهای تخفیف.
    """
    code = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True, 
        verbose_name="کد تخفیف"
    )
    discount_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="درصد تخفیف"
    )
    start_at = models.DateTimeField(null=True, blank=True, verbose_name="معتبر از تاریخ")
    end_at = models.DateTimeField(null=True, blank=True, verbose_name="معتبر تا تاریخ")
    max_usage = models.PositiveIntegerField(default=100, verbose_name="حداکثر تعداد استفاده")
    usage_count = models.PositiveIntegerField(default=0, editable=False, verbose_name="تعداد استفاده شده")
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    
    def __str__(self):
        return f"{self.code} ({self.discount_percent}%)"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_random_code()
            self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        
        if self.start_at and self.end_at and self.start_at > self.end_at:
            raise ValidationError("تاریخ شروع باید قبل از تاریخ پایان باشد")
        
        if self.usage_count > self.max_usage:
            raise ValidationError("تعداد استفاده نمی‌تواند بیشتر از حداکثر مجاز باشد.")

    @property
    def is_usable(self):
        """
        بررسی می‌کند آیا کد قابل استفاده است یا خیر.
        """
        now = timezone.now()
        
        if not self.is_active:
            return False
        if self.usage_count >= self.max_usage:
            return False
        if self.start_at and self.start_at > now:
            return False
        if self.end_at and self.end_at < now:
            return False
        
        return True
    
    @property
    def remaining_usage(self):
        """تعداد استفاده باقی‌مانده"""
        
        return max(0, self.max_usage - self.usage_count)
    
    @property
    def usage_percentage(self):
        """ درصد استفاده از کد """
        
        if self.max_usage == 0:
            return 0
        return (self.usage_count / self.max_usage) * 100
    
    def increment_usage(self):
        """افزایش تعداد استفاده (thread-safe)"""
        
        # بررسی قابلیت استفاده قبل از افزایش
        if not self.is_usable:
            raise ValidationError("این کد تخفیف قابل استفاده نیست.")
        
        # افزایش thread-safe
        updated_rows = DiscountCode.objects.filter(
            id=self.id,
            usage_count__lt=F('max_usage')  # اطمینان از عدم تجاوز از حد مجاز
        ).update(usage_count=F('usage_count') + 1)
        
        if updated_rows == 0:
            raise ValidationError("کد تخفیف دیگر قابل استفاده نیست.")
        
        # به‌روزرسانی instance فعلی
        self.refresh_from_db(fields=['usage_count'])
    