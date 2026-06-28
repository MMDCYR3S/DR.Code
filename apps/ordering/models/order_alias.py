from django.db import models
from django.utils.translation import gettext_lazy as _

class OrderAlias(models.Model):
    """
    اسامی مختلف برای یک Order
    """
    order = models.ForeignKey(
        "ordering.Order",
        on_delete=models.CASCADE,
        related_name="aliases",
        verbose_name="اوردر",
    )
    name = models.CharField(
        max_length=200,
        verbose_name="نام جایگزین",
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="نام اصلی",
        help_text="آیا این نام اصلی Order است؟",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "نام جایگزین"
        verbose_name_plural = "نام‌های جایگزین"
        unique_together = ["order", "name"]

    def __str__(self):
        return f"{self.name} ({self.order.name})"

    def save(self, *args, **kwargs):
        if self.is_primary:
            OrderAlias.objects.filter(order=self.order).update(is_primary=False)
        super().save(*args, **kwargs)
