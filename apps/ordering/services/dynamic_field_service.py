"""
services/dynamic_field_service.py
==================================
سرویس مدیریت DynamicFieldGroup و زیرمجموعه‌های آن.

تغییر رویکرد: گروه‌ها دیگر مستقل نیستند.
هر DynamicFieldGroup باید به یک Order تعلق داشته باشد (ForeignKey).

عملیات پوشش‌داده‌شده:
  - ایجاد گروه برای یک Order خاص
  - دریافت لیست گروه‌های یک Order
  - بازیابی گروه با تمام زیرساختار
  - ویرایش گروه / زیرگروه / آیتم
  - حذف گروه (cascade خودکار زیرگروه‌ها و آیتم‌ها)
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import QuerySet
from django.core.exceptions import ValidationError

from apps.ordering.models import (
    Order,
    DynamicFieldGroup,
    DynamicFieldSubGroup,
    DynamicFieldItem,
)


class DynamicFieldService:

    # ══════════════════════════════════════════════════════════════════════
    #  CREATE — ساخت گروه برای یک Order خاص
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def create_group_for_order(order_id: int, data: dict) -> DynamicFieldGroup:
        """
        ایجاد یک DynamicFieldGroup کامل برای یک Order خاص.
        
        ساختار: Group → SubGroups → Items
        
        Args:
            order_id: شناسه Order که گروه به آن تعلق دارد
            data: دیکشنری شامل:
                - title: عنوان گروه
                - order_index: ترتیب نمایش (اختیاری)
                - color: رنگ گروه (اختیاری)
                - subgroups: لیست زیرگروه‌ها (اختیاری)
        
        Returns:
            DynamicFieldGroup ساخته‌شده
        """
        # اعتبارسنجی Order
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            raise ValidationError(f"Order با id={order_id} یافت نشد.")

        subgroups_data = data.pop("subgroups", [])

        # ساخت گروه
        group = DynamicFieldGroup.objects.create(
            order=order,
            title=data["title"],
            order_index=data.get("order_index", 0),
            color=data.get("color", ""),
        )

        # ساخت زیرگروه‌ها
        for sg_data in subgroups_data:
            DynamicFieldService._create_subgroup(group, sg_data)

        return group

    @staticmethod
    def _create_subgroup(
        group: DynamicFieldGroup, sg_data: dict
    ) -> DynamicFieldSubGroup:
        """ساخت یک زیرگروه برای گروه."""
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
        """ساخت یک آیتم KEY-VALUE برای زیرگروه."""
        return DynamicFieldItem.objects.create(
            subgroup=subgroup,
            key=item_data["key"],
            value=item_data["value"],
            order_index=item_data.get("order_index", 0),
        )

    # ══════════════════════════════════════════════════════════════════════
    #  READ — دریافت گروه‌ها
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_group(group_id: int) -> DynamicFieldGroup:
        """
        بازیابی یک گروه با prefetch کامل زیرساختار.
        
        Args:
            group_id: شناسه گروه
        
        Returns:
            DynamicFieldGroup با تمام زیرگروه‌ها و آیتم‌ها
        """
        try:
            return (
                DynamicFieldGroup.objects
                .select_related("order")
                .prefetch_related("subgroups__items")
                .get(pk=group_id)
            )
        except DynamicFieldGroup.DoesNotExist:
            raise ValidationError(f"DynamicFieldGroup با id={group_id} یافت نشد.")

    @staticmethod
    def get_groups_by_order(order_id: int) -> QuerySet[DynamicFieldGroup]:
        """
        دریافت لیست تمام گروه‌های یک Order خاص.
        
        این متد برای نمایش گروه‌های پویای یک Order استفاده می‌شود.
        
        Args:
            order_id: شناسه Order
        
        Returns:
            QuerySet از DynamicFieldGroup‌ها با prefetch کامل
        """
        # اعتبارسنجی Order
        if not Order.objects.filter(pk=order_id).exists():
            raise ValidationError(f"Order با id={order_id} یافت نشد.")

        return (
            DynamicFieldGroup.objects
            .filter(order_id=order_id)
            .prefetch_related("subgroups__items")
            .order_by("order_index")
        )

    # ══════════════════════════════════════════════════════════════════════
    #  UPDATE — ویرایش گروه‌ها
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def update_group(group_id: int, data: dict) -> DynamicFieldGroup:
        """
        ویرایش فیلدهای سطح اول گروه (title, order_index, color).
        
        نکته: Order قابل تغییر نیست (برای تغییر Order باید گروه حذف و دوباره ساخته شود).
        """
        group = DynamicFieldService.get_group(group_id)

        if "title" in data:
            group.title = data["title"]
        if "order_index" in data:
            group.order_index = data["order_index"]
        if "color" in data:
            group.color = data["color"]

        group.save(update_fields=["title", "order_index", "color", "updated_at"])
        return group

    @staticmethod
    @transaction.atomic
    def update_subgroup(subgroup_id: int, data: dict) -> DynamicFieldSubGroup:
        """ویرایش زیرگروه."""
        try:
            subgroup = DynamicFieldSubGroup.objects.get(pk=subgroup_id)
        except DynamicFieldSubGroup.DoesNotExist:
            raise ValidationError(f"DynamicFieldSubGroup با id={subgroup_id} یافت نشد.")

        if "title" in data:
            subgroup.title = data["title"]
        if "order_index" in data:
            subgroup.order_index = data["order_index"]

        subgroup.save(update_fields=["title", "order_index", "updated_at"])
        return subgroup

    @staticmethod
    @transaction.atomic
    def update_item(item_id: int, data: dict) -> DynamicFieldItem:
        """ویرایش آیتم KEY-VALUE."""
        try:
            item = DynamicFieldItem.objects.get(pk=item_id)
        except DynamicFieldItem.DoesNotExist:
            raise ValidationError(f"DynamicFieldItem با id={item_id} یافت نشد.")

        if "key" in data:
            item.key = data["key"]
        if "value" in data:
            item.value = data["value"]
        if "order_index" in data:
            item.order_index = data["order_index"]

        item.save(update_fields=["key", "value", "order_index", "updated_at"])
        return item

    # ══════════════════════════════════════════════════════════════════════
    #  ADD NESTED — اضافه کردن زیرگروه یا آیتم به گروه موجود
    # ══════════════════════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════════════════════
    #  DELETE — حذف گروه‌ها
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def delete_group(group_id: int) -> None:
        """
        حذف گروه — زیرگروه‌ها و آیتم‌ها به‌صورت cascade حذف می‌شوند.
        
        نکته: Order حذف نمی‌شود، فقط گروه از Order جدا می‌شود.
        """
        deleted, _ = DynamicFieldGroup.objects.filter(pk=group_id).delete()
        if not deleted:
            raise ValidationError(f"DynamicFieldGroup با id={group_id} یافت نشد.")

    @staticmethod
    @transaction.atomic
    def delete_subgroup(subgroup_id: int) -> None:
        """حذف زیرگروه — آیتم‌ها به‌صورت cascade حذف می‌شوند."""
        deleted, _ = DynamicFieldSubGroup.objects.filter(pk=subgroup_id).delete()
        if not deleted:
            raise ValidationError(f"DynamicFieldSubGroup با id={subgroup_id} یافت نشد.")

    @staticmethod
    @transaction.atomic
    def delete_item(item_id: int) -> None:
        """حذف آیتم."""
        deleted, _ = DynamicFieldItem.objects.filter(pk=item_id).delete()
        if not deleted:
            raise ValidationError(f"DynamicFieldItem با id={item_id} یافت نشد.")
