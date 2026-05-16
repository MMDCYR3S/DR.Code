from django.db import models
import jdatetime

from apps.prescriptions.models.category import PrescriptionCategory
from .colors import TailwindColor


class Order(models.Model):
    """
    مدل اصلی اوردر پزشکی.

    تغییرات نسبت به نسخه قبلی:
      - فیلد category اجباری شد (null=False, blank=False)
      - اضافه شد: dynamic_field_groups (ManyToMany → DynamicFieldGroup)
        این رابطه معکوس وابستگی قبلی است:
        Order «دارای» چند DynamicFieldGroup است،
        نه اینکه DynamicFieldGroup به Order وابسته باشد.
        این‌طور یک DynamicFieldGroup می‌تواند قبل از Order وجود داشته باشد
        و بعد از ساخت Order به آن متصل شود.
    """

    # ─────────────────────────── فیلدهای ثابت ───────────────────────────
    imp = models.TextField(
        verbose_name="Impression / تشخیص اصلی",
        help_text="تشخیص اصلی پزشک"
    )
    condition = models.TextField(
        verbose_name="Condition / وضعیت بیمار",
        help_text="وضعیت فعلی بیمار"
    )
    diet = models.TextField(
        verbose_name="Diet / رژیم غذایی",
        help_text="رژیم غذایی تجویزشده"
    )
    action = models.TextField(
        verbose_name="Action / اقدام",
        help_text="اقدامات درمانی لازم"
    )
    position = models.TextField(
        verbose_name="Position / وضعیت قرارگیری",
        help_text="وضعیت قرارگیری بیمار"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="توضیحات کلی Order",
        help_text="توضیحات تکمیلی (مثلاً شرح وضعیت Condition)"
    )

    # ─────────────────────────── دسته‌بندی (اجباری) ──────────────────────
    category = models.ForeignKey(
        PrescriptionCategory,
        on_delete=models.PROTECT,           # حذف Category اگر Order داشته باشد مجاز نیست
        related_name="orders",
        verbose_name="دسته‌بندی",
        help_text="دسته‌بندی اجباری است — هر Order حتماً باید دسته داشته باشد"
    )

    # ─────────────────────────── فیلدهای پویا (قالب) ────────────────────
    dynamic_field_groups = models.ManyToManyField(
        "ordering.DynamicFieldGroup",
        blank=True,
        related_name="orders",
        verbose_name="گروه‌های فیلد پویا",
        help_text=(
            "گروه‌های DynamicField که به این Order متصل هستند. "
            "این گروه‌ها مستقل از Order وجود دارند و فقط لینک می‌شوند."
        )
    )

    # ─────────────────────────── رنگ‌بندی ────────────────────────────────
    color = models.CharField(
        max_length=30,
        choices=TailwindColor.choices,
        blank=True,
        verbose_name="رنگ Order",
        help_text="رنگ نمایشی این Order در رابط کاربری"
    )

    # ─────────────────────────── زمان‌بندی ───────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order [{self.category}]: {self.imp[:60]}"

    # ─────────────────────────── تاریخ شمسی ──────────────────────────────
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