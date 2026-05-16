"""
services/order_service.py
==========================
سرویس مدیریت Order و تمام زیرمجموعه‌های مستقیم آن:
  - OrderSection
  - SectionItem + ItemCondition
  - DrugSectionItem + DrugItemCondition
  - ItemNote
  - اتصال DynamicFieldGroup‌ها (بدون ایجاد مجدد — فقط lینک)

جریان ایجاد Order در UI:
  مرحله ۱ — DynamicFieldService.list_groups()  → نمایش گروه‌های موجود
  مرحله ۲ — OrderService.create(data)          → ساخت Order + اتصال گروه‌ها
  مرحله ۳ — EmergencyDispositionService        → تعیین تکلیف (فایل جداگانه)
  مرحله ۴ — MediaService                       → آپلود تصویر/ویدیو

ساختار ورودی create:
{
    "category_id": int,                  # اجباری
    "imp": str,
    "condition": str,
    "diet": str,
    "action": str,
    "position": str,
    "notes": str,                        # اختیاری
    "color": str,                        # اختیاری

    "dynamic_field_group_ids": [int],    # اختیاری — IDs از DynamicFieldGroup‌های موجود
                                         # سرویس خودش آن‌ها را لینک می‌کند

    "sections": [                        # اختیاری
        {
            "title": str,
            "notes": str,               # اختیاری
            "is_drug_section": bool,    # پیش‌فرض False
            "order_index": int,         # اختیاری
            "color": str,              # اختیاری

            "items": [                  # اگر is_drug_section=False
                {
                    "text": str,
                    "notes": str,       # اختیاری
                    "order_index": int, # اختیاری
                    "conditions": [
                        {"text": str, "order_index": int}
                    ],
                    "notes_table": [    # ItemNote‌های سطح آیتم
                        {"text": str, "order_index": int}
                    ]
                }
            ],

            "drug_items": [             # اگر is_drug_section=True
                {
                    "drug_id": int,
                    "notes": str,       # اختیاری
                    "order_index": int, # اختیاری
                    "conditions": [
                        {"text": str, "order_index": int}
                    ]
                }
            ],

            "notes_table": [            # ItemNote‌های سطح Section
                {"text": str, "order_index": int}
            ]
        }
    ]
}
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import QuerySet
from django.core.exceptions import ValidationError

from apps.ordering.models import (
    Order,
    OrderSection,
    SectionItem,
    ItemCondition,
    DrugSectionItem,
    DrugItemCondition,
    ItemNote,
    DynamicFieldGroup,
)
from apps.prescriptions.models.category import PrescriptionCategory


class OrderService:

    # ══════════════════════════════════════════════════════════════════════
    #  CREATE
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def create(data: dict) -> Order:
        """
        ایجاد یک Order کامل در یک تراکنش اتمی.

        گام‌ها:
          1. اعتبارسنجی و ساخت Order
          2. اتصال DynamicFieldGroup‌های انتخاب‌شده (لینک — بدون ایجاد مجدد)
          3. ساخت Section‌ها + Items + Conditions + Notes
        """
        # ── 1. اعتبارسنجی category ──────────────────────────────────────
        category_id = data.get("category_id")
        if not category_id:
            raise ValidationError("فیلد category_id اجباری است.")

        try:
            category = PrescriptionCategory.objects.get(pk=category_id)
        except PrescriptionCategory.DoesNotExist:
            raise ValidationError(f"دسته‌بندی با id={category_id} یافت نشد.")

        # ── 2. ساخت Order ───────────────────────────────────────────────
        order = Order.objects.create(
            category=category,
            imp=data["imp"],
            condition=data["condition"],
            diet=data["diet"],
            action=data["action"],
            position=data["position"],
            notes=data.get("notes", ""),
            color=data.get("color", ""),
        )

        # ── 3. اتصال DynamicFieldGroup‌ها ───────────────────────────────
        group_ids = data.get("dynamic_field_group_ids", [])
        if group_ids:
            OrderService._attach_dynamic_field_groups(order, group_ids)

        # ── 4. ساخت Section‌ها ───────────────────────────────────────────
        sections_data = data.get("sections", [])
        for section_data in sections_data:
            OrderService._create_section(order, section_data)

        return order

    # ══════════════════════════════════════════════════════════════════════
    #  UPDATE
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def update(order_id: int, data: dict) -> Order:
        """
        ویرایش Order.

        استراتژی برای زیرمجموعه‌ها:
          - اگر "sections" در data ارسال نشده باشد: Section‌ها دست‌نخورده می‌مانند.
          - اگر "sections" ارسال شده باشد: Section‌های قدیمی حذف و جدید ساخته می‌شوند.
            (رویکرد replace-all — ساده و بدون باگ‌های sync)

          - برای dynamic_field_group_ids: رویکرد set() — گروه‌های جدید جایگزین می‌شوند.
        """
        order = OrderService.get_order(order_id)

        # ── فیلدهای اصلی ────────────────────────────────────────────────
        if "category_id" in data:
            try:
                order.category = PrescriptionCategory.objects.get(pk=data["category_id"])
            except PrescriptionCategory.DoesNotExist:
                raise ValidationError(f"دسته‌بندی با id={data['category_id']} یافت نشد.")

        for field in ("imp", "condition", "diet", "action", "position", "notes", "color"):
            if field in data:
                setattr(order, field, data[field])

        order.save()

        # ── DynamicFieldGroup‌ها ─────────────────────────────────────────
        if "dynamic_field_group_ids" in data:
            OrderService._attach_dynamic_field_groups(order, data["dynamic_field_group_ids"])

        # ── Section‌ها ───────────────────────────────────────────────────
        if "sections" in data:
            order.sections.all().delete()   # cascade آیتم‌ها و notes را هم حذف می‌کند
            for section_data in data["sections"]:
                OrderService._create_section(order, section_data)

        return order

    # ══════════════════════════════════════════════════════════════════════
    #  READ
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_order(order_id: int) -> Order:
        """بازیابی Order با prefetch کامل برای جلوگیری از N+1."""
        try:
            return (
                Order.objects
                .select_related("category")
                .prefetch_related(
                    "dynamic_field_groups__subgroups__items",
                    "sections__items__conditions",
                    "sections__items__notes_table",
                    "sections__drug_items__conditions",
                    "sections__notes_table",
                    "images",
                    "videos",
                )
                .get(pk=order_id)
            )
        except Order.DoesNotExist:
            raise ValidationError(f"Order با id={order_id} یافت نشد.")

    @staticmethod
    def list_orders(**filters) -> QuerySet[Order]:
        """فهرست Orders با فیلتر دلخواه (مثلاً category_id=5)."""
        return (
            Order.objects
            .select_related("category")
            .prefetch_related("dynamic_field_groups")
            .filter(**filters)
            .order_by("-created_at")
        )

    # ══════════════════════════════════════════════════════════════════════
    #  DELETE
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def delete(order_id: int) -> None:
        deleted, _ = Order.objects.filter(pk=order_id).delete()
        if not deleted:
            raise ValidationError(f"Order با id={order_id} یافت نشد.")

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION-LEVEL PATCH (ویرایش بدون replace-all)
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def add_section(order_id: int, section_data: dict) -> OrderSection:
        """اضافه کردن یک Section جدید به Order موجود."""
        order = OrderService.get_order(order_id)
        return OrderService._create_section(order, section_data)

    @staticmethod
    @transaction.atomic
    def update_section(section_id: int, data: dict) -> OrderSection:
        try:
            section = OrderSection.objects.get(pk=section_id)
        except OrderSection.DoesNotExist:
            raise ValidationError(f"Section با id={section_id} یافت نشد.")

        for field in ("title", "notes", "is_drug_section", "order_index", "color"):
            if field in data:
                setattr(section, field, data[field])
        section.save()
        return section

    @staticmethod
    @transaction.atomic
    def delete_section(section_id: int) -> None:
        deleted, _ = OrderSection.objects.filter(pk=section_id).delete()
        if not deleted:
            raise ValidationError(f"Section با id={section_id} یافت نشد.")

    # ══════════════════════════════════════════════════════════════════════
    #  PRIVATE HELPERS
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _attach_dynamic_field_groups(order: Order, group_ids: list[int]) -> None:
        """
        اتصال DynamicFieldGroup‌های موجود به Order از طریق M2M.
        گروه‌هایی که در DB وجود ندارند نادیده گرفته می‌شوند (با log).
        """
        existing_ids = set(
            DynamicFieldGroup.objects
            .filter(pk__in=group_ids)
            .values_list("pk", flat=True)
        )
        missing = set(group_ids) - existing_ids
        if missing:
            raise ValidationError(
                f"DynamicFieldGroup‌های زیر یافت نشدند: {missing}"
            )
        order.dynamic_field_groups.set(existing_ids)

    @staticmethod
    def _create_section(order: Order, data: dict) -> OrderSection:
        notes_table_data = data.pop("notes_table", [])
        items_data = data.pop("items", [])
        drug_items_data = data.pop("drug_items", [])

        section = OrderSection.objects.create(
            order=order,
            title=data["title"],
            notes=data.get("notes", ""),
            is_drug_section=data.get("is_drug_section", False),
            order_index=data.get("order_index", 0),
            color=data.get("color", ""),
        )

        # notes در سطح Section
        for note_data in notes_table_data:
            ItemNote.objects.create(
                section=section,
                text=note_data["text"],
                order_index=note_data.get("order_index", 0),
            )

        # آیتم‌های متنی
        for item_data in items_data:
            OrderService._create_section_item(section, item_data)

        # آیتم‌های دارویی
        for drug_data in drug_items_data:
            OrderService._create_drug_item(section, drug_data)

        return section

    @staticmethod
    def _create_section_item(section: OrderSection, data: dict) -> SectionItem:
        conditions_data = data.pop("conditions", [])
        notes_table_data = data.pop("notes_table", [])

        item = SectionItem.objects.create(
            section=section,
            text=data["text"],
            notes=data.get("notes", ""),
            order_index=data.get("order_index", 0),
        )

        for cond_data in conditions_data:
            ItemCondition.objects.create(
                item=item,
                text=cond_data["text"],
                order_index=cond_data.get("order_index", 0),
            )

        for note_data in notes_table_data:
            ItemNote.objects.create(
                item=item,
                text=note_data["text"],
                order_index=note_data.get("order_index", 0),
            )

        return item

    @staticmethod
    def _create_drug_item(section: OrderSection, data: dict) -> DrugSectionItem:
        conditions_data = data.pop("conditions", [])

        drug_item = DrugSectionItem.objects.create(
            section=section,
            drug_id=data["drug_id"],
            notes=data.get("notes", ""),
            order_index=data.get("order_index", 0),
        )

        for cond_data in conditions_data:
            DrugItemCondition.objects.create(
                drug_item=drug_item,
                text=cond_data["text"],
                order_index=cond_data.get("order_index", 0),
            )

        return drug_item
