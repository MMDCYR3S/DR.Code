from django.db import models
import jdatetime

from .order import Order
from .colors import TailwindColor


class OrderSection(models.Model):
    """
    زیرمجموعه‌های پویای هر Order.
    هر Order می‌تواند چندین Section داشته باشد.
    هفت Section پیش‌فرض در زمان نصب اولیه از طریق data migration ثبت می‌شوند.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="Order مرجع"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان Section",
        help_text='مثال: "Monitoring & nursing"، "Drugs"، "Imaging"'
    )
    notes = models.TextField(
        blank=True,
        verbose_name="توضیحات کلی Section",
        help_text="توضیحاتی که به کل Section مربوط است، نه به یک آیتم خاص"
    )
    is_drug_section = models.BooleanField(
        default=False,
        verbose_name="بخش داروهاست؟",
        help_text="در صورت فعال بودن، امکان انتخاب دارو از بانک داروهای موجود فعال می‌شود"
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )

    # ─────────────────────────── رنگ‌بندی ────────────────────────────────
    color = models.CharField(
        max_length=30,
        choices=TailwindColor.choices,
        blank=True,
        verbose_name="رنگ Section",
        help_text="رنگ نمایشی این Section در رابط کاربری"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        ordering = ["order_index"]

    def __str__(self):
        return f"{self.title} (Order: {self.order_id})"

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


class SectionItem(models.Model):
    """
    آیتم‌های هر Section.
    هر Section شامل یک یا چند آیتم (عنوان/Value) است.
    هر آیتم می‌تواند توضیحات اختصاصی و شرط‌های مربوط به خود را داشته باشد.
    """

    section = models.ForeignKey(
        OrderSection,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Section مرجع"
    )
    text = models.TextField(
        verbose_name="متن آیتم",
        help_text='مثال: "Heart Monitoring, Pulse Oxymetry"، "Tab ASA 325mg po stat"'
    )
    notes = models.TextField(
        blank=True,
        verbose_name="توضیحات اختصاصی آیتم",
        help_text="توضیحاتی که فقط به این آیتم مربوط است"
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "آیتم Section"
        verbose_name_plural = "آیتم‌های Section"
        ordering = ["order_index"]

    def __str__(self):
        return f"{self.text[:80]} — {self.section.title}"

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


class ItemCondition(models.Model):
    """
    شرط‌های هر SectionItem یا DrugSectionItem.
    مثال: "if SBP≥90, PR≥60" برای Tab Metoral
    """

    item = models.ForeignKey(
        SectionItem,
        on_delete=models.CASCADE,
        related_name="conditions",
        verbose_name="آیتم مرجع"
    )
    text = models.TextField(
        verbose_name="متن شرط",
        help_text='مثال: "if SBP≥90, PR≥60"، "در صورت تهوع"'
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")

    class Meta:
        verbose_name = "شرط آیتم"
        verbose_name_plural = "شرط‌های آیتم"
        ordering = ["order_index"]

    def __str__(self):
        return f"شرط: {self.text[:80]}"


# ─────────────────────────────────────────────────────────────────────────────


class DrugSectionItem(models.Model):
    """
    اتصال دارو به یک Section با is_drug_section=True.
    از بانک داروهای موجود در سیستم نسخه‌نویسی استفاده می‌کند.
    """
    from apps.prescriptions.models.drug import Drug

    section = models.ForeignKey(
        OrderSection,
        on_delete=models.CASCADE,
        related_name="drug_items",
        verbose_name="Section مرجع"
    )
    drug = models.ForeignKey(
        "prescriptions.Drug",
        on_delete=models.CASCADE,
        related_name="order_drug_items",
        verbose_name="داروی انتخابی"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="توضیحات اضافی دارو در این Order",
        help_text='مثال: "در صورت مصرف قبلی آسپرین: 80mg داده شود"'
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "دارو در Section"
        verbose_name_plural = "داروهای Section"
        ordering = ["order_index"]

    def __str__(self):
        return f"داروی «{self.drug.title}» در Section «{self.section.title}»"


class DrugItemCondition(models.Model):
    """
    شرط‌های اختصاصی برای DrugSectionItem.
    مثال: "در صورت تهوع" برای یک داروی خاص در Order
    """

    drug_item = models.ForeignKey(
        DrugSectionItem,
        on_delete=models.CASCADE,
        related_name="conditions",
        verbose_name="دارو در Section"
    )
    text = models.TextField(
        verbose_name="متن شرط",
        help_text='مثال: "if SBP≥90, PR≥60"، "در صورت تهوع"'
    )
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")

    class Meta:
        verbose_name = "شرط دارو"
        verbose_name_plural = "شرط‌های دارو"
        ordering = ["order_index"]

    def __str__(self):
        return f"شرط دارو: {self.text[:80]}"