from django.db import models
from slugify import slugify

class Category(models.Model):
    """
    مدل دسته‌بندی نسخه‌های پزشکی.
    هر نسخه به یک دسته‌بندی تعلق دارد.
    """
    title = models.CharField(max_length=100, unique=True, verbose_name="نام دسته‌بندی")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="اسلاگ (آدرس)")
    color_code = models.CharField(
        max_length=7,
        help_text="کد هگزادسیمال رنگ، مانند #FF5733",
        verbose_name="کد رنگ"
    )

    class Meta:
        ordering = ['name']
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
