import jdatetime

from django.db import models

from .order import Order


# ========= Order Video Model ========= #
class OrderVideo(models.Model):
    """
    مدل برای افزودن ویدیوهای مربوط به یک Order.
    هر Order می‌تواند چندین ویدیو داشته باشد.
    هیچ فایل ویدیویی در سرور ذخیره نمی‌شود؛ فقط لینک Embed.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name="Order مرجع"
    )
    video_url = models.URLField(
        verbose_name="لینک ویدیو (آپارات)",
        help_text="لینک embed از آپارات، یوتیوب و سایر پلتفرم‌ها"
    )
    title = models.CharField(max_length=255, blank=True, verbose_name="عنوان ویدیو")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    order_index = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ساخت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='زمان بروزرسانی')

    class Meta:
        verbose_name = "ویدیو Order"
        verbose_name_plural = "ویدیوهای Order"
        ordering = ["order_index"]

    def __str__(self):
        return f"ویدیو برای Order «{self.order_id}»"

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
