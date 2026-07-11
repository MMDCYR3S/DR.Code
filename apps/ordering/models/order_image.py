import os
import random
from venv import logger
import jdatetime

from django.db import models, transaction

from .order import Order
from apps.prescriptions.tasks import compress_prescription_image


# ========== Helper: Random Number Generator ==========
def generate_random_number(length=6):
    """تولید عدد تصادفی با طول دلخواه (مثلاً ۶ رقمی)"""
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


# ========== Helper: Dynamic Upload Path ==========
def get_order_image_path(instance, filename):
    """
    ساخت مسیر و نام فایل به‌صورت:
    orders/images/order_<id>/<rand>.<ext>
    """
    ext = filename.split('.')[-1].lower()
    random_number = generate_random_number()
    new_filename = f"image_{random_number}.{ext}"
    return os.path.join("orders", "images", f"order_{instance.order_id}", new_filename)


# ========= Order Image Model ========= #
class OrderImage(models.Model):
    """
    مدل برای آپلود تصاویر مربوط به یک Order.
    هر Order می‌تواند چندین تصویر داشته باشد.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Order مرجع"
    )
    image = models.ImageField(
        upload_to=get_order_image_path,
        verbose_name="فایل تصویر"
    )
    caption = models.CharField(max_length=255, blank=True, verbose_name="کپشن تصویر")
    is_compressed = models.BooleanField(default=False, verbose_name="فشرده شده؟")
    order_index = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ساخت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='زمان بروزرسانی')

    class Meta:
        verbose_name = "تصویر Order"
        verbose_name_plural = "تصاویر Order"
        ordering = ["order_index"]

    def __str__(self):
        return f"تصویر برای Order «{self.order_id}»"

    def save(self, *args, **kwargs):
        """
        ذخیره‌ی سفارشی:
        - مسیر آپلود سفارشی دارد
        - بعد از ذخیره، تسک فشرده‌سازی را در صف قرار می‌دهد
        """
        super().save(*args, **kwargs)

        if self.image and not self.is_compressed:
            def run_compression():
                try:
                    from apps.prescriptions.tasks import compress_prescription_image
                    compress_prescription_image.delay(self.id)
                except Exception as e:
                    pass
            transaction.on_commit(run_compression)

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
