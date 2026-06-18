# apps/subscriptions/models.py
import jdatetime
from slugify import slugify
from django.db import models

class FeatureType(models.TextChoices):
    PRESCRIPTION_ACCESS = "prescription_access", "دسترسی به نسخه‌های پریمیوم"
    ORDERING = "ordering_access", "دسترسی به اوردرهای پزشکی"

class Feature(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام ویژگی")
    slug = models.SlugField(unique=True, verbose_name="شناسه یکتا", editable=False)
    feature_type = models.CharField(
        max_length=50,
        choices=FeatureType.choices,
        verbose_name="نوع فیچر",
        default=FeatureType.PRESCRIPTION_ACCESS
    )
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        ordering = ['feature_type', 'name']
        verbose_name = "ویژگی"
        verbose_name_plural = "ویژگی‌ها"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def shamsi_created_at(self):
        if not self.created_at:
            return "—"
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    def __str__(self):
        return f"{self.get_feature_type_display()} - {self.name}"


class Membership(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name="نام نوع اشتراک")
    slug = models.SlugField(unique=True, blank=True, editable=False)
    features = models.ManyToManyField(
        Feature, 
        blank=True, 
        related_name="memberships", 
        verbose_name="ویژگی‌ها و دسترسی‌ها"
    )
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    
    class Meta:
        ordering = ['title']
        verbose_name = "نوع اشتراک"
        verbose_name_plural = "انواع اشتراک"

    @property
    def shamsi_created_at(self):
        if not self.created_at:
            return "—"
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
