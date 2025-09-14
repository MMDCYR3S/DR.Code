from django.db import models
from django.conf import settings
from slugify import slugify

# ========== Membership Model ========== #
class Membership(models.Model):
    """
    نوع اشتراک را تعریف می‌کند. در حال حاضر فقط یک رکورد به نام "پریمیوم" خواهد داشت.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="نام نوع اشتراک")
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name