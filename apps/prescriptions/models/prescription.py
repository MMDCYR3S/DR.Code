import jdatetime
from slugify import slugify

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django_ckeditor_5.fields import CKEditor5Field

from .category import PrescriptionCategory


# ========= PRESCRIPTION ALIAS ========= #
class PrescriptionAlias(models.Model):
    """
    اسامی مختلف برای یک نسخه
    """
    prescription = models.ForeignKey(
        "Prescription",
        on_delete=models.CASCADE,
        related_name='aliases',
        verbose_name="نسخه"
    )
    name = models.CharField(
        max_length=200,
        verbose_name="نام جایگزین"
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="نام اصلی",
        help_text="آیا این نام اصلی نسخه است؟"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "نام جایگزین"
        verbose_name_plural = "نام‌های جایگزین"
        unique_together = ['prescription', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.prescription.title})"

    def save(self, *args, **kwargs):
        # اگر این نام اصلی تنظیم شد، بقیه رو غیر اصلی کن
        if self.is_primary:
            PrescriptionAlias.objects.filter(
                prescription=self.prescription
            ).update(is_primary=False)
        super().save(*args, **kwargs)

# ========= ACCESS CHOICES ========= #
class AccessChoices(models.TextChoices):
    """ انتخاب دسترسی نسخه """
    free = "FREE", ("رایگان")
    premium = "PREMIUM", ("ویژه")
class Prescription(models.Model):
    """
    مدل اصلی برای هر نسخه پزشکی.
    این مدل شامل اطلاعات کلی نسخه است.
    """
    user = models.ForeignKey("accounts.User", verbose_name=_(""), on_delete=models.CASCADE)
    category = models.ForeignKey(
        PrescriptionCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prescriptions',
        verbose_name="دسته‌بندی"
    )
    items = models.ManyToManyField(
        "Drug",
        through='PrescriptionDrug',
        related_name='prescriptions',
        verbose_name="اقلام دارویی"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان نسخه")
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    slug = models.SlugField(unique=True, allow_unicode=True, blank=True, verbose_name="اسلاگ (آدرس)")
    access_level = models.CharField(
        max_length=10,
        choices=AccessChoices.choices,
        default=AccessChoices.free.value,
        verbose_name='سطح دسترسی'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال',
        help_text='نسخه‌های غیرفعال نمایش داده نمی‌شوند'
    )
    detailed_description = CKEditor5Field('Text', config_name='extends', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    class Meta:
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        
    def get_category_color(self):
        """ دریافت رنگ دسته‌بندی """
        return self.category.color_code

    def get_primary_name(self):
        """نام اصلی نسخه را برمی‌گرداند"""
        primary_alias = self.aliases.filter(is_primary=True).first()
        return primary_alias.name if primary_alias else self.title
    
    def get_all_names(self):
        """تمام نام‌های نسخه را به صورت لیست برمی‌گرداند"""
        alias_names = list(self.aliases.values_list('name', flat=True))
        all_names = [self.title] + alias_names
        return list(set(all_names))  # حذف تکراری‌ها
    
    def get_all_names_string(self):
        """تمام نام‌ها را به صورت رشته با جداکننده کاما برمی‌گرداند"""
        return ", ".join(self.get_all_names())
    
    def add_alias(self, name, is_primary=False):
        """اضافه کردن نام جایگزین جدید"""
        alias, created = PrescriptionAlias.objects.get_or_create(
            prescription=self,
            name=name,
            defaults={'is_primary': is_primary}
        )
        return alias, created
    
    def has_alias(self, name):
        """بررسی اینکه آیا این نام در نام‌های جایگزین موجود است یا نه"""
        return self.aliases.filter(name__iexact=name).exists() or self.title.lower() == name.lower()
    
    @property
    def shamsi_created_at(self):
        if self.created_at is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    @property
    def shamsi_updated_at(self):
        if self.updated_at is None:
            return "—"
            
        jdate = jdatetime.datetime.fromgregorian(datetime=self.updated_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    def __str__(self):
        return self.title
