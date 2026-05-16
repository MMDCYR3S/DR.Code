from django.db import models
import jdatetime

from .section import OrderSection, SectionItem


class ItemNote(models.Model):
    """
    جدول جداگانه برای توضیحات هر آیتم یا Section.

    منطق:
    - اگر item مقدار داشته باشد و section خالی باشد:
      این توضیح مربوط به آن آیتم خاص است.
    - اگر section مقدار داشته باشد و item خالی باشد:
      این توضیح مربوط به کل Section است (نه آیتم‌های داخلش).

    این ساختار اجازه می‌دهد یک Section نیازمند توضیح باشد
    بدون اینکه توضیح به آیتم‌های داخلش نسبت داده شود.
    """

    section = models.ForeignKey(
        OrderSection,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notes_table",
        verbose_name="Section مرجع",
        help_text="در صورت انتخاب بدون آیتم، این توضیح به کل Section تعلق دارد"
    )
    item = models.ForeignKey(
        SectionItem,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notes_table",
        verbose_name="آیتم مرجع",
        help_text="در صورت انتخاب، این توضیح فقط به این آیتم تعلق دارد"
    )
    text = models.TextField(verbose_name="متن توضیح")
    order_index = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ساخت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان بروزرسانی")

    class Meta:
        verbose_name = "توضیح آیتم / Section"
        verbose_name_plural = "توضیحات آیتم‌ها / Sectionها"
        ordering = ["order_index"]
        constraints = [
            # حداقل یکی از دو فیلد باید مقدار داشته باشد
            models.CheckConstraint(
                check=(
                    models.Q(item__isnull=False) |
                    models.Q(section__isnull=False)
                ),
                name="item_note_must_have_item_or_section"
            )
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.item and not self.section:
            raise ValidationError(
                "باید حداقل یکی از فیلدهای «آیتم» یا «Section» انتخاب شود."
            )

    def __str__(self):
        if self.item:
            return f"توضیح آیتم: {self.item.text[:50]}"
        return f"توضیح Section: {self.section.title}"

    @property
    def is_section_level(self):
        """آیا این توضیح در سطح Section است (نه آیتم)؟"""
        return self.section_id is not None and self.item_id is None

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