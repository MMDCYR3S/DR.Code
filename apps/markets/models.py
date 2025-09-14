# marketing/models.py
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
        
import secrets
import string

# ========= Random Code Generator ========= #
def generate_random_code(length=8):
    """ یک کد تصادفی منحصر به فرد ایجاد می‌کند """
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(characters) for i in range(length))
        if not DiscountCode.objects.filter(code=code).exists():
            return code
        
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
        super().save(*args, **kwargs)

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
    