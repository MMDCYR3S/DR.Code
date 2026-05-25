from django.db import models
import jdatetime

from django_ckeditor_5.fields import CKEditor5Field

from .order import Order
from .colors import TailwindColor


class EmergencyDisposition(models.Model):
    """
    تعیین تکلیف در اورژانس.
    هر Order دقیقاً یک EmergencyDisposition دارد که خودش ظرف گره‌های درختی است.
    """

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="emergency_disposition",
        verbose_name="Order مرجع"
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="عنوان کلی",
        help_text="عنوان بخش تعیین تکلیف (اختیاری)"
    )
    color = models.CharField(
        max_length=30,
        choices=TailwindColor.choices,
        blank=True,
        verbose_name="رنگ گره",
        help_text="رنگ نمایشی این گره در رابط کاربری"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="توضیحات کلی تعیین تکلیف"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "تعیین تکلیف اورژانس"
        verbose_name_plural = "تعیین تکلیف‌های اورژانس"

    def __str__(self):
        return f"تعیین تکلیف — Order {self.order_id}"

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


# ─────────────────────────────────────────────────────────────────────────────


class EmergencyNode(models.Model):
    """
    گره‌های درختی تعیین تکلیف اورژانس.
    ساختار self-referential برای پشتیبانی از درخت چندسطحی.

    مثال:
        گره والد: "STEMI"
        گره فرزند: "بیماران کم‌خطر"
        گره فرزند: "اصل کلی"
    """

    disposition = models.ForeignKey(
        EmergencyDisposition,
        on_delete=models.CASCADE,
        related_name="nodes",
        verbose_name="تعیین تکلیف مرجع"
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name="گره والد",
        help_text="برای ایجاد ساختار درختی. خالی = گره ریشه"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان گره",
        help_text='مثال: "STEMI"، "اصل کلی"، "بیماران کم‌خطر"'
    )

    # ── محتوا با CKEditor 5 ──────────────────────────────────────────
    content = CKEditor5Field(
        blank=True,
        verbose_name="محتوا",
        help_text="محتوای اصلی این گره — با فرمت‌بندی غنی",
        config_name="default",
    )

    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )

    # رنگ‌بندی برای تعیین تکلیف
    color = models.CharField(
        max_length=30,
        choices=TailwindColor.choices,
        blank=True,
        verbose_name="رنگ گره",
        help_text="رنگ نمایشی این گره در رابط کاربری"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "گره تعیین تکلیف"
        verbose_name_plural = "گره‌های تعیین تکلیف"
        ordering = ["order_index"]

    def __str__(self):
        return self.title

    @property
    def is_root(self):
        return self.parent_id is None

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