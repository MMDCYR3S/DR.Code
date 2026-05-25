"""
services/emergency_sync_service.py
=====================================
سرویس یکپارچه مدیریت EmergencyDisposition و EmergencyNode.

رویکرد: دقیقاً شبیه SectionSyncService — یک متد sync که
همه چیز را در یک تراکنش اتمیک ذخیره می‌کند.

جریان:
  1. OrderService.create_order() → Order ساخته می‌شود
  2. EmergencySyncService.sync(order_id, data) →
     disposition و تمام گره‌های درختی یکجا ذخیره می‌شوند

ساختار ورودی sync:
{
    "title": str,          # اختیاری
    "color": str,          # اختیاری
    "notes": str,          # اختیاری
    "nodes": [
        {
            "id": int | null,
            "title": str,
            "content": str,            # HTML از CKEditor 5
            "order_index": int,        # اختیاری
            "color": str,             # اختیاری
            "children": [              # recursive
                { ...همان ساختار... }
            ]
        }
    ]
}
"""

from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from typing import Dict, Any

from apps.ordering.models import Order, EmergencyDisposition, EmergencyNode


class EmergencySyncService:
    """
    ذخیره‌سازی یکپارچه EmergencyDisposition / EmergencyNode برای یک Order.

    فلو:
        FE داده تعیین تکلیف را ارسال می‌کند.
        این سرویس:
          1. اگر Disposition وجود ندارد، می‌سازد؛ وگرنه ویرایش می‌کند.
          2. تمام درخت گره‌های قدیمی را پاک می‌کند.
          3. درخت جدید را به‌صورت recursive می‌سازد.
        همه چیز در یک تراکنش اتمیک انجام می‌شود.
    """

    # ══════════════════════════════════════════════════════════════════════
    #  SYNC — ذخیره یکجا
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def sync(order_id: int, data: Dict[str, Any]) -> EmergencyDisposition:
        """
        ورودی: order_id و دیکشنری داده تعیین تکلیف.

        اگر Order از قبل Disposition داشت، ویرایش می‌کند.
        اگر نداشت، می‌سازد.
        درخت گره‌ها همیشه از نو ساخته می‌شود (replace strategy).
        """
        order = get_object_or_404(Order, id=order_id)

        # upsert Disposition
        disposition, _ = EmergencyDisposition.objects.get_or_create(
            order=order,
            defaults={
                "title": data.get("title", ""),
                "color": data.get("color", ""),
                "notes": data.get("notes", ""),
            }
        )

        # ویرایش فیلدهای Disposition
        for field in ("title", "color", "notes"):
            if field in data:
                setattr(disposition, field, data[field])
        disposition.save()

        # بازسازی کامل درخت
        disposition.nodes.all().delete()
        for node_data in data.get("nodes", []):
            EmergencySyncService._create_node(disposition, node_data, parent=None)

        return disposition

    # ══════════════════════════════════════════════════════════════════════
    #  READ — دریافت
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_for_order(order_id: int) -> EmergencyDisposition:
        """
        بازیابی تعیین تکلیف با درخت کامل گره‌ها برای یک Order.
        اگر وجود نداشته باشد، خطا می‌دهد.
        """
        try:
            return (
                EmergencyDisposition.objects
                .prefetch_related("nodes__children__children")
                .get(order_id=order_id)
            )
        except EmergencyDisposition.DoesNotExist:
            raise ValidationError(
                f"تعیین تکلیف برای Order با id={order_id} یافت نشد."
            )

    @staticmethod
    def get(disposition_id: int) -> EmergencyDisposition:
        try:
            return (
                EmergencyDisposition.objects
                .prefetch_related("nodes__children__children")
                .get(pk=disposition_id)
            )
        except EmergencyDisposition.DoesNotExist:
            raise ValidationError(f"EmergencyDisposition با id={disposition_id} یافت نشد.")

    # ══════════════════════════════════════════════════════════════════════
    #  NODE OPERATIONS — عملیات تکی گره
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def add_node(
        disposition_id: int,
        data: dict,
        parent_id: int | None = None,
    ) -> EmergencyNode:
        """اضافه کردن گره جدید به تعیین تکلیف موجود."""
        try:
            disposition = EmergencyDisposition.objects.get(pk=disposition_id)
        except EmergencyDisposition.DoesNotExist:
            raise ValidationError(f"EmergencyDisposition با id={disposition_id} یافت نشد.")

        parent = None
        if parent_id is not None:
            try:
                parent = EmergencyNode.objects.get(pk=parent_id, disposition=disposition)
            except EmergencyNode.DoesNotExist:
                raise ValidationError(f"گره والد با id={parent_id} در این تعیین تکلیف یافت نشد.")

        return EmergencySyncService._create_node(disposition, data, parent=parent)

    @staticmethod
    @transaction.atomic
    def update_node(node_id: int, data: dict) -> EmergencyNode:
        try:
            node = EmergencyNode.objects.get(pk=node_id)
        except EmergencyNode.DoesNotExist:
            raise ValidationError(f"EmergencyNode با id={node_id} یافت نشد.")

        for field in ("title", "content", "order_index", "color"):
            if field in data:
                setattr(node, field, data[field])
        node.save()
        return node

    @staticmethod
    @transaction.atomic
    def delete_node(node_id: int) -> None:
        """حذف گره — فرزندان نیز به‌صورت cascade حذف می‌شوند."""
        deleted, _ = EmergencyNode.objects.filter(pk=node_id).delete()
        if not deleted:
            raise ValidationError(f"EmergencyNode با id={node_id} یافت نشد.")

    @staticmethod
    @transaction.atomic
    def delete(disposition_id: int) -> None:
        deleted, _ = EmergencyDisposition.objects.filter(pk=disposition_id).delete()
        if not deleted:
            raise ValidationError(f"EmergencyDisposition با id={disposition_id} یافت نشد.")

    # ══════════════════════════════════════════════════════════════════════
    #  PRIVATE HELPERS
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _create_node(
        disposition: EmergencyDisposition,
        data: dict,
        parent: EmergencyNode | None,
    ) -> EmergencyNode:
        """ساخت گره به‌صورت recursive — فرزندان را هم می‌سازد."""
        children_data = data.pop("children", [])

        node = EmergencyNode.objects.create(
            disposition=disposition,
            parent=parent,
            title=data.get("title", ""),
            content=data.get("content", ""),
            order_index=data.get("order_index", 0),
            color=data.get("color", ""),
        )

        for child_data in children_data:
            EmergencySyncService._create_node(disposition, child_data, parent=node)

        return node