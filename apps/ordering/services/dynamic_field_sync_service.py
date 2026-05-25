"""
services/dynamic_field_sync_service.py
========================================
سرویس یکپارچه مدیریت DynamicFieldGroup و زیرمجموعه‌های آن.

رویکرد: دقیقاً شبیه SectionSyncService — یک متد sync که
همه چیز را در یک تراکنش اتمیک ذخیره می‌کند.

جریان:
  1. OrderService.create_order() → Order ساخته می‌شود
  2. DynamicFieldSyncService.sync(order_id, groups_payload) →
     تمام گروه‌ها، زیرگروه‌ها و آیتم‌ها یکجا ذخیره می‌شوند

ساختار ورودی sync:
[
    {
        "id": int | null,          # null = جدید
        "title": str,
        "order_index": int,
        "color": str,              # اختیاری
        "subgroups": [
            {
                "id": int | null,
                "title": str,
                "order_index": int,
                "items": [
                    {
                        "id": int | null,
                        "key": str,
                        "value": str,
                        "order_index": int
                    }
                ]
            }
        ]
    }
]
"""

from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from typing import List, Dict, Any

from apps.ordering.models import (
    Order,
    DynamicFieldGroup,
    DynamicFieldSubGroup,
    DynamicFieldItem,
)


class DynamicFieldSyncService:
    """
    ذخیره‌سازی یکپارچه DynamicFieldGroup / SubGroup / Item برای یک Order.

    فلو:
        FE یک آرایه groups ارسال می‌کند.
        این سرویس:
          1. گروه‌های موجود را ویرایش یا جدید می‌سازد.
          2. زیرگروه‌های حذف‌شده را پاک می‌کند.
          3. آیتم‌های حذف‌شده را پاک می‌کند.
          4. گروه‌هایی که در payload نیستند را حذف می‌کند.
        همه چیز در یک تراکنش اتمیک انجام می‌شود.
    """

    # ══════════════════════════════════════════════════════════════════════
    #  SYNC — ذخیره یکجا
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def sync(order_id: int, groups_payload: List[Dict[str, Any]]) -> Order:
        """
        ورودی: order_id و لیست groups.

        ساختار هر group:
        {
            "id": int | null,
            "title": str,
            "order_index": int,        # اختیاری، پیش‌فرض 0
            "color": str,              # اختیاری
            "subgroups": [ ... ]       # اختیاری
        }
        """
        order = get_object_or_404(Order, id=order_id)
        surviving_group_ids: set[int] = set()

        for group_data in groups_payload:
            group = DynamicFieldSyncService._upsert_group(order, group_data)
            surviving_group_ids.add(group.id)

            surviving_subgroup_ids: set[int] = set()

            for sg_data in group_data.get("subgroups", []):
                subgroup = DynamicFieldSyncService._upsert_subgroup(group, sg_data)
                surviving_subgroup_ids.add(subgroup.id)

                surviving_item_ids: set[int] = set()

                for item_data in sg_data.get("items", []):
                    item = DynamicFieldSyncService._upsert_item(subgroup, item_data)
                    surviving_item_ids.add(item.id)

                # حذف آیتم‌هایی که در payload نیستند
                DynamicFieldItem.objects.filter(subgroup=subgroup).exclude(
                    id__in=surviving_item_ids
                ).delete()

            # حذف زیرگروه‌هایی که در payload نیستند (cascade آیتم‌هایشان را هم حذف می‌کند)
            DynamicFieldSubGroup.objects.filter(group=group).exclude(
                id__in=surviving_subgroup_ids
            ).delete()

        # حذف گروه‌هایی که در payload نیستند
        DynamicFieldGroup.objects.filter(order=order).exclude(
            id__in=surviving_group_ids
        ).delete()

        return order

    # ══════════════════════════════════════════════════════════════════════
    #  READ — دریافت گروه‌ها
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_groups(order_id: int) -> QuerySet[DynamicFieldGroup]:
        """دریافت تمام گروه‌های یک Order با prefetch کامل."""
        if not Order.objects.filter(pk=order_id).exists():
            raise ValidationError(f"Order با id={order_id} یافت نشد.")
        return (
            DynamicFieldGroup.objects
            .filter(order_id=order_id)
            .prefetch_related("subgroups__items")
            .order_by("order_index")
        )

    @staticmethod
    def get_group(group_id: int) -> DynamicFieldGroup:
        """بازیابی یک گروه با prefetch کامل."""
        try:
            return (
                DynamicFieldGroup.objects
                .select_related("order")
                .prefetch_related("subgroups__items")
                .get(pk=group_id)
            )
        except DynamicFieldGroup.DoesNotExist:
            raise ValidationError(f"DynamicFieldGroup با id={group_id} یافت نشد.")

    # ══════════════════════════════════════════════════════════════════════
    #  DELETE
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def delete_group(group_id: int) -> None:
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

    # ══════════════════════════════════════════════════════════════════════
    #  PRIVATE HELPERS
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _upsert_group(order: Order, data: dict) -> DynamicFieldGroup:
        group_id = data.get("id")
        defaults = {
            "title": data.get("title", ""),
            "order_index": data.get("order_index", 0),
            "color": data.get("color", ""),
        }
        if group_id:
            group = get_object_or_404(DynamicFieldGroup, id=group_id, order=order)
            for k, v in defaults.items():
                setattr(group, k, v)
            group.save()
        else:
            group = DynamicFieldGroup.objects.create(order=order, **defaults)
        return group

    @staticmethod
    def _upsert_subgroup(group: DynamicFieldGroup, data: dict) -> DynamicFieldSubGroup:
        sg_id = data.get("id")
        defaults = {
            "title": data.get("title", ""),
            "order_index": data.get("order_index", 0),
        }
        if sg_id:
            subgroup = get_object_or_404(DynamicFieldSubGroup, id=sg_id, group=group)
            for k, v in defaults.items():
                setattr(subgroup, k, v)
            subgroup.save()
        else:
            subgroup = DynamicFieldSubGroup.objects.create(group=group, **defaults)
        return subgroup

    @staticmethod
    def _upsert_item(subgroup: DynamicFieldSubGroup, data: dict) -> DynamicFieldItem:
        item_id = data.get("id")
        defaults = {
            "key": data.get("key", ""),
            "value": data.get("value", ""),
            "order_index": data.get("order_index", 0),
        }
        if item_id:
            item = get_object_or_404(DynamicFieldItem, id=item_id, subgroup=subgroup)
            for k, v in defaults.items():
                setattr(item, k, v)
            item.save()
        else:
            item = DynamicFieldItem.objects.create(subgroup=subgroup, **defaults)
        return item