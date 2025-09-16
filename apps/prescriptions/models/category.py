from django.db import models
from slugify import slugify

class PrescriptionCategory(models.Model):
    """
    مدل دسته‌بندی نسخه‌های پزشکی.
    هر نسخه به یک دسته‌بندی تعلق دارد.
    """
    title = models.CharField(max_length=100, unique=True, verbose_name="نام دسته‌بندی")
    slug = models.SlugField(unique=True, allow_unicode=True, blank=True, verbose_name="اسلاگ (آدرس)")
    color_code = models.CharField(
        max_length=20,
        help_text="کد هگزادسیمال رنگ، مانند #FF5733",
        verbose_name="کد رنگ"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ساخت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='زمان بروزرسانی')

    class Meta:
        ordering = ['title']
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
