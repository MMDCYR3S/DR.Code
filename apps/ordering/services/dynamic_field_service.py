"""
services/dynamic_field_service.py
==================================
سرویس مدیریت DynamicFieldGroup و زیرمجموعه‌های آن.

این گروه‌ها مستقل از Order هستند و به‌عنوان «قالب» ذخیره می‌شوند.
در زمان ساخت Order، سرویس مربوطه این قالب‌ها را به Order لینک می‌کند.

عملیات پوشش‌داده‌شده:
  - ایجاد گروه کامل (Group + SubGroups + Items) در یک تراکنش
  - بازیابی گروه با تمام زیرساختار
  - ویرایش گروه / زیرگروه / آیتم
  - حذف گروه (cascade خودکار زیرگروه‌ها و آیتم‌ها)
  - فهرست تمام گروه‌های موجود (برای انتخاب در هنگام ساخت Order)
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import QuerySet
from django.core.exceptions import ValidationError

from apps.ordering.models import (
    DynamicFieldGroup,
    DynamicFieldSubGroup,
    DynamicFieldItem,
)


# ══════════════════════════════════════════════════════════════════════════════
#  ساختارهای ورودی (plain dict — بدون نیاز به dataclass خارجی)
# ══════════════════════════════════════════════════════════════════════════════
#
#  create_group(data) انتظار دارد:
#  {
#      "title": str,
#      "order_index": int,          # اختیاری، پیش‌فرض 0
#      "color": str,                # اختیاری، یکی از TailwindColor
#      "subgroups": [               # اختیاری
#          {
#              "title": str,
#              "order_index": int,  # اختیاری
#              "items": [           # اختیاری
#                  {"key": str, "value": str, "order_index": int}
#              ]
#          }
#      ]
#  }
#
# ══════════════════════════════════════════════════════════════════════════════


class DynamicFieldService:

    # ──────────────────────────── Create ────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_group(data: dict) -> DynamicFieldGroup:
        """
        ایجاد یک DynamicFieldGroup کامل به همراه SubGroup‌ها و Item‌ها.
        تمام عملیات در یک تراکنش انجام می‌شود.
        """
        subgroups_data = data.pop("subgroups", [])

        group = DynamicFieldGroup.objects.create(
            title=data["title"],
            order_index=data.get("order_index", 0),
            color=data.get("color", ""),
        )

        for sg_data in subgroups_data:
            DynamicFieldService._create_subgroup(group, sg_data)

        return group

    @staticmethod
    def _create_subgroup(
        group: DynamicFieldGroup, sg_data: dict
    ) -> DynamicFieldSubGroup:
        items_data = sg_data.pop("items", [])

        subgroup = DynamicFieldSubGroup.objects.create(
            group=group,
            title=sg_data["title"],
            order_index=sg_data.get("order_index", 0),
        )

        for item_data in items_data:
            DynamicFieldService._create_item(subgroup, item_data)

        return subgroup

    @staticmethod
    def _create_item(
        subgroup: DynamicFieldSubGroup, item_data: dict
    ) -> DynamicFieldItem:
        return DynamicFieldItem.objects.create(
            subgroup=subgroup,
            key=item_data["key"],
            value=item_data["value"],
            order_index=item_data.get("order_index", 0),
        )

    # ──────────────────────────── Read ──────────────────────────────────────

    @staticmethod
    def get_group(group_id: int) -> DynamicFieldGroup:
        """بازیابی گروه با prefetch کامل زیرساختار."""
        try:
            return (
                DynamicFieldGroup.objects
                .prefetch_related("subgroups__items")
                .get(pk=group_id)
            )
        except DynamicFieldGroup.DoesNotExist:
            raise ValidationError(f"DynamicFieldGroup با id={group_id} یافت نشد.")

    @staticmethod
    def list_groups() -> QuerySet[DynamicFieldGroup]:
        """
        فهرست تمام گروه‌های موجود — برای نمایش در فرم ساخت Order.
        prefetch کامل انجام می‌شود تا در سریالایزر N+1 نداشته باشیم.
        """
        return (
            DynamicFieldGroup.objects
            .prefetch_related("subgroups__items")
            .order_by("order_index")
        )

    # ──────────────────────────── Update ────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def update_group(group_id: int, data: dict) -> DynamicFieldGroup:
        """
        ویرایش فیلدهای سطح اول گروه (title, order_index, color).
        برای ویرایش زیرگروه یا آیتم از متدهای جداگانه استفاده شود.
        """
        group = DynamicFieldService.get_group(group_id)

        group.title = data.get("title", group.title)
        group.order_index = data.get("order_index", group.order_index)
        group.color = data.get("color", group.color)
        group.save(update_fields=["title", "order_index", "color", "updated_at"])

        return group

    @staticmethod
    @transaction.atomic
    def update_subgroup(subgroup_id: int, data: dict) -> DynamicFieldSubGroup:
        try:
            subgroup = DynamicFieldSubGroup.objects.get(pk=subgroup_id)
        except DynamicFieldSubGroup.DoesNotExist:
            raise ValidationError(f"DynamicFieldSubGroup با id={subgroup_id} یافت نشد.")

        subgroup.title = data.get("title", subgroup.title)
        subgroup.order_index = data.get("order_index", subgroup.order_index)
        subgroup.save(update_fields=["title", "order_index", "updated_at"])

        return subgroup

    @staticmethod
    @transaction.atomic
    def update_item(item_id: int, data: dict) -> DynamicFieldItem:
        try:
            item = DynamicFieldItem.objects.get(pk=item_id)
        except DynamicFieldItem.DoesNotExist:
            raise ValidationError(f"DynamicFieldItem با id={item_id} یافت نشد.")

        item.key = data.get("key", item.key)
        item.value = data.get("value", item.value)
        item.order_index = data.get("order_index", item.order_index)
        item.save(update_fields=["key", "value", "order_index", "updated_at"])

        return item

    # ──────────────────────────── Add nested ────────────────────────────────

    @staticmethod
    @transaction.atomic
    def add_subgroup(group_id: int, data: dict) -> DynamicFieldSubGroup:
        """اضافه کردن زیرگروه جدید به گروه موجود."""
        group = DynamicFieldService.get_group(group_id)
        return DynamicFieldService._create_subgroup(group, data)

    @staticmethod
    @transaction.atomic
    def add_item(subgroup_id: int, data: dict) -> DynamicFieldItem:
        """اضافه کردن آیتم جدید به زیرگروه موجود."""
        try:
            subgroup = DynamicFieldSubGroup.objects.get(pk=subgroup_id)
        except DynamicFieldSubGroup.DoesNotExist:
            raise ValidationError(f"DynamicFieldSubGroup با id={subgroup_id} یافت نشد.")
        return DynamicFieldService._create_item(subgroup, data)

    # ──────────────────────────── Delete ────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def delete_group(group_id: int) -> None:
        """حذف گروه — زیرگروه‌ها و آیتم‌ها به‌صورت cascade حذف می‌شوند."""
        deleted, _ = DynamicFieldGroup.objects.filter(pk=group_id).delete()
        if not deleted:
            raise ValidationError(f"DynamicFieldGroup با id={group_id} یافت نشد.")

    @staticmethod
    @transaction.atomic
    def delete_subgroup(subgroup_id: int) -> None:
        deleted, _ = DynamicFieldSubGroup.objects.filter(pk=subgroup_id).delete()
        if not deleted:
            raise ValidationError(f"DynamicFieldSubGroup با id={subgroup_id} یافت نشد.")

    @staticmethod
    @transaction.atomic
    def delete_item(item_id: int) -> None:
        deleted, _ = DynamicFieldItem.objects.filter(pk=item_id).delete()
        if not deleted:
            raise ValidationError(f"DynamicFieldItem با id={item_id} یافت نشد.")
