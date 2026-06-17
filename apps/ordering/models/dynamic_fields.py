from django.db import models
import jdatetime

from django_ckeditor_5.fields import CKEditor5Field

from .colors import TailwindColor


class DynamicFieldGroup(models.Model):
    order = models.ForeignKey(
        'ordering.Order',
        on_delete=models.CASCADE,
        related_name='dynamic_field_groups'
    )
    title = models.CharField(max_length=200, verbose_name="عنوان گروه")
    order_index = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    color = models.CharField(
        max_length=30, choices=TailwindColor.choices, blank=True, verbose_name="رنگ گروه"
    )
    notes = models.TextField(blank=True, verbose_name="توضیحات کلی")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "گروه فیلد پویا"
        verbose_name_plural = "گروه‌های فیلد پویا"
        ordering = ["order_index"]

    def __str__(self):
        return self.title

    @property
    def shamsi_created_at(self):
        if not self.created_at:
            return "—"
        return jdatetime.datetime.fromgregorian(datetime=self.created_at).strftime("%Y/%m/%d - %H:%M")

    @property
    def shamsi_updated_at(self):
        if not self.updated_at:
            return "—"
        return jdatetime.datetime.fromgregorian(datetime=self.updated_at).strftime("%Y/%m/%d - %H:%M")


class DynamicFieldNode(models.Model):
    """
    گره درختی پیش‌بالینی — مشابه EmergencyNode.
    ساختار self-referential برای درخت چندسطحی.
    """
    group = models.ForeignKey(
        DynamicFieldGroup,
        on_delete=models.CASCADE,
        related_name="nodes",
        verbose_name="گروه مرجع"
    )
    parent = models.ForeignKey(
        "self",
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name="گره والد"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان گره")
    content = CKEditor5Field(
        blank=True,
        verbose_name="محتوا",
        config_name='extends'
    )
    order_index = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    color = models.CharField(
        max_length=30, choices=TailwindColor.choices, blank=True, verbose_name="رنگ گره"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "گره فیلد پویا"
        verbose_name_plural = "گره‌های فیلد پویا"
        ordering = ["order_index"]

    def __str__(self):
        return self.title

    @property
    def is_root(self):
        return self.parent_id is None

    @property
    def shamsi_created_at(self):
        if not self.created_at:
            return "—"
        return jdatetime.datetime.fromgregorian(datetime=self.created_at).strftime("%Y/%m/%d - %H:%M")

    @property
    def shamsi_updated_at(self):
        if not self.updated_at:
            return "—"
        return jdatetime.datetime.fromgregorian(datetime=self.updated_at).strftime("%Y/%m/%d - %H:%M")
