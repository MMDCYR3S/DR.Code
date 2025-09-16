from django.db import models
from slugify import slugify

# ========== Membership Model ========== #
class Membership(models.Model):
    """
    نوع اشتراک را تعریف می‌کند. در حال حاضر فقط یک رکورد به نام "پریمیوم" خواهد داشت.
    """
    title = models.CharField(max_length=100, unique=True, verbose_name="نام نوع اشتراک")
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title