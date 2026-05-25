"""
services/emergency_service.py
================================
سرویس مدیریت EmergencyDisposition و EmergencyNode.

ویژگی کلیدی:
  - سرویس به‌صورت خودکار Order ساخته‌شده را پیدا می‌کند
  - ساختار درختی EmergencyNode با رویکرد recursive پشتیبانی می‌شود

ساختار ورودی create_for_order:
{
    "title": str,          # اختیاری
    "color": str,          # اختیاری
    "notes": str,          # اختیاری
    "nodes": [
        {
            "title": str,
            "content": str,         # HTML از CKEditor 5 — اختیاری
            "order_index": int,     # اختیاری
            "color": str,           # اختیاری
            "children": [           # زیرگره‌ها — recursive
                { ...همان ساختار... }
            ]
        }
    ]
}
"""

from __future__ import annotations

from django.db import transaction
from django.core.exceptions import ValidationError

from apps.ordering.models import Order, EmergencyDisposition, EmergencyNode


class EmergencyService:

    # ══════════════════════════════════════════════════════════════════════
    #  CREATE
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def create_for_order(order_id: int, data: dict) -> EmergencyDisposition:
        """
        ایجاد EmergencyDisposition برای یک Order موجود.
        اگر Order از قبل دارای EmergencyDisposition باشد، خطا می‌دهد.
        """
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            raise ValidationError(f"Order با id={order_id} یافت نشد.")

        if hasattr(order, "emergency_disposition"):
            raise ValidationError(
                f"Order با id={order_id} از قبل دارای تعیین تکلیف است. "
                "از متد update() استفاده کنید."
            )

        nodes_data = data.pop("nodes", [])

        disposition = EmergencyDisposition.objects.create(
            order=order,
            title=data.get("title", ""),
            color=data.get("color", ""),
            notes=data.get("notes", ""),
        )

        for node_data in nodes_data:
            EmergencyService._create_node(disposition, node_data, parent=None)

        return disposition

    # ══════════════════════════════════════════════════════════════════════
    #  UPDATE
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def update(disposition_id: int, data: dict) -> EmergencyDisposition:
        """
        ویرایش EmergencyDisposition.
        اگر "nodes" ارسال شود: تمام درخت پاک و از نو ساخته می‌شود.
        """
        try:
            disposition = EmergencyDisposition.objects.get(pk=disposition_id)
        except EmergencyDisposition.DoesNotExist:
            raise ValidationError(f"EmergencyDisposition با id={disposition_id} یافت نشد.")

        for field in ("title", "color", "notes"):
            if field in data:
                setattr(disposition, field, data[field])
        disposition.save()

        if "nodes" in data:
            disposition.nodes.all().delete()
            for node_data in data["nodes"]:
                EmergencyService._create_node(disposition, node_data, parent=None)

        return disposition

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

    # ══════════════════════════════════════════════════════════════════════
    #  READ
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_for_order(order_id: int) -> EmergencyDisposition:
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
    #  NODE OPERATIONS
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def add_node(
        disposition_id: int,
        data: dict,
        parent_id: int | None = None,
    ) -> EmergencyNode:
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

        return EmergencyService._create_node(disposition, data, parent=parent)

    @staticmethod
    @transaction.atomic
    def delete_node(node_id: int) -> None:
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
        children_data = data.pop("children", [])

        node = EmergencyNode.objects.create(
            disposition=disposition,
            parent=parent,
            title=data["title"],
            content=data.get("content", ""),
            order_index=data.get("order_index", 0),
            color=data.get("color", ""),
        )

        for child_data in children_data:
            EmergencyService._create_node(disposition, child_data, parent=node)

        return node