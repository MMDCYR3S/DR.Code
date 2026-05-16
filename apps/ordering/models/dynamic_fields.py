from django.db import models
import jdatetime

from .colors import TailwindColor


class DynamicFieldGroup(models.Model):
    """
    گروه‌های فیلد پویا — مستقل از Order.

    این مدل اکنون یک «قالب» (Template) مستقل است.
    هر Order از طریق ManyToManyField به چند DynamicFieldGroup
    می‌تواند اشاره کند.

    ادمین می‌تواند هر تعداد گروه با هر عنوان دلخواه اضافه کند:
        مثال: «تشخیص افتراقی»، «تعاریف»، «ارزیابی»، «پیشینه بیمار» و ...

    ساختار سه‌سطحی:
        DynamicFieldGroup → DynamicFieldSubGroup → DynamicFieldItem (KEY-VALUE)

    رابطه با Order:
        Order.dynamic_field_groups  (ManyToMany — تعریف‌شده در order.py)
    """

    title = models.CharField(
        max_length=200,
        verbose_name="عنوان گروه",
        help_text='مثال: «تشخیص افتراقی»، «تعاریف»، «ارزیابی»'
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش پیش‌فرض"
    )
    color = models.CharField(
        max_length=30,
        choices=TailwindColor.choices,
        blank=True,
        verbose_name="رنگ گروه",
        help_text="رنگ نمایشی این گروه در رابط کاربری"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "گروه فیلد پویا"
        verbose_name_plural = "گروه‌های فیلد پویا"
        ordering = ["order_index"]

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


# ─────────────────────────────────────────────────────────────────────────────


class DynamicFieldSubGroup(models.Model):
    """
    زیرگروه داخل یک DynamicFieldGroup.
    هر گروه می‌تواند چندین زیرگروه داشته باشد.
    مثال: زیر گروه «تشخیص افتراقی» → «STEMI»، «NSTEMI»
    """

    group = models.ForeignKey(
        DynamicFieldGroup,
        on_delete=models.CASCADE,
        related_name="subgroups",
        verbose_name="گروه مرجع"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان زیرگروه"
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "زیرگروه فیلد پویا"
        verbose_name_plural = "زیرگروه‌های فیلد پویا"
        ordering = ["order_index"]

    def __str__(self):
        return f"{self.title} ← {self.group.title}"

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


class DynamicFieldItem(models.Model):
    """
    آیتم KEY-VALUE داخل یک زیرگروه.
    هر زیرگروه شامل یک یا چند جفت KEY-VALUE است.
    مثال: کلید «علت» — مقدار «ایسکمی میوکارد»
    """

    subgroup = models.ForeignKey(
        DynamicFieldSubGroup,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="زیرگروه مرجع"
    )
    key = models.CharField(
        max_length=200,
        verbose_name="کلید (Key)"
    )
    value = models.TextField(
        verbose_name="مقدار (Value)"
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "آیتم فیلد پویا"
        verbose_name_plural = "آیتم‌های فیلد پویا"
        ordering = ["order_index"]

    def __str__(self):
        return f"{self.key}: {self.value[:60]}"

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