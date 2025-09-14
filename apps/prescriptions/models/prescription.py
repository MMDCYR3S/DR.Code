from django.db import models
from .category import Category
from slugify import slugify

class Prescription(models.Model):
    """
    مدل اصلی برای هر نسخه پزشکی.
    این مدل شامل اطلاعات کلی نسخه است.
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prescriptions',
        verbose_name="دسته‌بندی"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان نسخه")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="اسلاگ (آدرس)")
    is_premium = models.BooleanField(default=True, verbose_name="نسخه ویژه است؟")
    detailed_description = models.TextField(blank=True, null=True, verbose_name="توضیحات تکمیلی (صفحه مجزا)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
