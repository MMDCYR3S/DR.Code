from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where phone number is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, phone_number, password, **extra_fields):
        """
        Create and save a User with the given phone number and password.
        """
        if not phone_number:
            raise ValueError(_('The Phone Number must be set'))
        
        # Normalize email if it exists
        if 'email' in extra_fields and extra_fields['email']:
            extra_fields['email'] = self.normalize_email(extra_fields['email'])
            
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        """
        Create and save a SuperUser with the given phone number and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
            
        return self.create_user(phone_number, password, **extra_fields)

# ----------------- Custom User Model -----------------
class User(AbstractUser):
    """
    مدل کاربر سفارشی که با شماره تماس به جای نام کاربری احراز هویت می‌شود.
    """
    username = None

    email = models.EmailField(_("email address"), unique=True)
    phone_number = models.CharField(
        _("phone number"),
        max_length=11,
        validators=[RegexValidator(regex=r'^\d{11}$', message=_("شماره تماس باید ۱۱ رقم باشد."))],
        unique=True,
        help_text=_("شماره تماس برای ورود به سیستم استفاده می‌شود."),
    )

    is_premium = models.BooleanField(default=False, verbose_name=_("کاربر ویژه"))

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.get_full_name() or self.phone_number