from django.db import models
from slugify import slugify

import jdatetime

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

