from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone

# ----------------- Custom User Model -----------------
class User(AbstractUser):
    """
    مدل کاربر سفارشی فقط با فیلدهای ضروری.
    وضعیت "ویژه" بودن کاربر از طریق اشتراک فعال او مشخص می‌شود.
    """
    phone_number = models.CharField(max_length=12,
        unique=True,
        verbose_name="شماره تلفن",
        validators=[
            RegexValidator(
                regex=r'^\+?98?\d{10}$',
                message="شماره تلفن باید یک شماره معتبر باشد."
            )
        ]
    )
    REQUIRED_FIELDS = ['email', 'phone_number']

    @property
    def is_premium(self):
        """
        بررسی می‌کند که آیا کاربر اشتراک فعال دارد یا خیر.
        این یک property دینامیک است و در دیتابیس ذخیره نمی‌شود.
        """
        # با این کار، هر لحظه وضعیت اشتراک کاربر چک می‌شود.
        return self.subscriptions.filter(end_date__gt=timezone.now()).exists()

    def __str__(self):
        return self.username