"""
services/order_service.py
==========================
سرویس مدیریت Order.

رویکرد:
  - OrderService فقط مسئول Order (ایجاد، ویرایش، حذف، لیست) است.
  - مدیریت Section/Item/Condition به SectionSyncService واگذار شده.
  - SectionSyncService یک متد یکپارچه دارد که همه تغییرات را یکجا ذخیره می‌کند.
"""

from __future__ import annotations

import logging
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from typing import List, Dict, Any, Optional

from apps.prescriptions.models import PrescriptionCategory, Drug
from apps.ordering.models import (
    Order,
    OrderSection,
    SectionItem,
    DrugSectionItem,
    Condition,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  ORDER SERVICE
# ═══════════════════════════════════════════════════════════════════════════

class OrderService:
    """مدیریت Order — فقط عملیات خود Order."""

    @staticmethod
    def get_order_list(filters: Optional[Dict[str, Any]] = None) -> List[Order]:
        queryset = Order.objects.select_related('category').all()
        if filters:
            queryset = queryset.filter(**filters)
        return list(queryset)

    @staticmethod
    def get_order_detail(order_id: int) -> Dict[str, Any]:
        order = get_object_or_404(
            Order.objects.select_related('category').prefetch_related(
                'sections__items__conditions',
                'sections__drug_items__conditions',
                'sections__drug_items__drug',
            ),
            id=order_id,
        )

        sections_data = []
        for section in order.sections.all():
            items_data = [
                {
                    'id': item.id,
                    'text': item.text,
                    'notes': item.notes,
                    'order_index': item.order_index,
                    'conditions': [
                        {'id': c.id, 'text': c.text, 'order_index': c.order_index}
                        for c in item.conditions.all()
                    ],
                    'created_at': item.created_at,
                    'updated_at': item.updated_at,
                }
                for item in section.items.all()
            ]
            drug_items_data = [
                {
                    'id': di.id,
                    'drug': {'id': di.drug.id, 'title': di.drug.title},
                    'notes': di.notes,
                    'order_index': di.order_index,
                    'conditions': [
                        {'id': c.id, 'text': c.text, 'order_index': c.order_index}
                        for c in di.conditions.all()
                    ],
                    'created_at': di.created_at,
                    'updated_at': di.updated_at,
                }
                for di in section.drug_items.all()
            ]
            sections_data.append({
                'id': section.id,
                'title': section.title,
                'notes': section.notes,
                'is_drug_section': section.is_drug_section,
                'order_index': section.order_index,
                'color': section.color,
                'items': items_data,
                'drug_items': drug_items_data,
                'created_at': section.created_at,
                'updated_at': section.updated_at,
            })

        return {
            'id': order.id,
            'name': order.name,
            'imp': order.imp,
            'condition': order.condition,
            'diet': order.diet,
            'action': order.action,
            'position': order.position,
            'notes': order.notes,
            'category': {'id': order.category.id, 'name': order.category.name},
            'color': order.color,
            'sections': sections_data,
            'created_at': order.created_at,
            'updated_at': order.updated_at,
            'shamsi_created_at': order.shamsi_created_at,
            'shamsi_updated_at': order.shamsi_updated_at,
        }

    @staticmethod
    @transaction.atomic
    def create_order(data: Dict[str, Any]) -> Order:
        """
        ایجاد Order.

        data keys:
            name, imp, condition, diet, action, position,
            notes (opt), category_id, color (opt)
        """
        category = get_object_or_404(PrescriptionCategory, id=data['category_id'])
        return Order.objects.create(
            name=data['name'],
            imp=data['imp'],
            condition=data['condition'],
            diet=data['diet'],
            action=data['action'],
            position=data['position'],
            notes=data.get('notes', ''),
            category=category,
            color=data.get('color', ''),
        )

    @staticmethod
    @transaction.atomic
    def update_order(order_id: int, data: Dict[str, Any]) -> Order:
        order = get_object_or_404(Order, id=order_id)
        fields = ['name', 'imp', 'condition', 'diet', 'action', 'position', 'notes', 'color']
        for field in fields:
            if field in data:
                setattr(order, field, data[field])
        if 'category_id' in data:
            order.category = get_object_or_404(PrescriptionCategory, id=data['category_id'])
        order.save()
        return order

    @staticmethod
    @transaction.atomic
    def delete_order(order_id: int) -> None:
        order = get_object_or_404(Order, id=order_id)
        order.delete()


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION SYNC SERVICE  —  یکپارچه
# ═══════════════════════════════════════════════════════════════════════════

class SectionSyncService:
    """
    ذخیره‌سازی یکپارچه Section/Item/Condition برای یک Order.

    فلو:
        FE یک آرایه sections ارسال می‌کند.
        هر section دارای items، drug_items و conditions است.
        این سرویس:
          1. سکشن‌های موجود را ویرایش یا جدید می‌سازد.
          2. آیتم‌های حذف‌شده را پاک می‌کند.
          3. Condition ها را با temp_id ↔ real_id map می‌کند.
          4. سکشن‌هایی که در payload نیستند را حذف می‌کند.
        همه چیز در یک تراکنش اتمیک انجام می‌شود.
    """

    @staticmethod
    @transaction.atomic
    def sync(order_id: int, sections_payload: List[Dict[str, Any]]) -> Order:
        """
        ورودی: order_id و لیست sections.

        ساختار هر section:
        {
            "id": int | null,          # null = جدید
            "temp_id": str | null,
            "title": str,
            "notes": str,
            "color": str,
            "is_drug_section": bool,
            "order_index": int,
            "items": [
                {
                    "id": int | null,
                    "temp_id": str | null,
                    "text": str,
                    "notes": str,
                    "order_index": int
                }
            ],
            "drug_items": [
                {
                    "id": int | null,
                    "temp_id": str | null,
                    "drug_id": int,
                    "notes": str,
                    "order_index": int
                }
            ],
            "conditions": [
                {
                    "id": int | null,
                    "temp_id": str | null,
                    "text": str,
                    "order_index": int,
                    "item_temp_ids": [str, ...],       # temp_id یا real_id آیتم‌های مرتبط
                    "drug_item_temp_ids": [str, ...]
                }
            ]
        }
        """
        order = get_object_or_404(Order, id=order_id)
        surviving_section_ids: set[int] = set()

        for sec_data in sections_payload:
            section = SectionSyncService._upsert_section(order, sec_data)
            surviving_section_ids.add(section.id)

            # ─── items ───
            item_id_map: Dict[str, int] = {}   # temp_id / str(real_id) → real db id
            surviving_item_ids: set[int] = set()

            for item_data in sec_data.get('items', []):
                item = SectionSyncService._upsert_item(section, item_data)
                surviving_item_ids.add(item.id)
                SectionSyncService._register_id_map(item_id_map, item_data, item.id)

            # ─── drug_items ───
            drug_item_id_map: Dict[str, int] = {}
            surviving_drug_item_ids: set[int] = set()

            for di_data in sec_data.get('drug_items', []):
                di = SectionSyncService._upsert_drug_item(section, di_data)
                surviving_drug_item_ids.add(di.id)
                SectionSyncService._register_id_map(drug_item_id_map, di_data, di.id)

            # ─── حذف موارد از دست رفته ───
            SectionItem.objects.filter(section=section).exclude(
                id__in=surviving_item_ids
            ).delete()
            DrugSectionItem.objects.filter(section=section).exclude(
                id__in=surviving_drug_item_ids
            ).delete()

            # ─── conditions ───
            surviving_condition_ids: set[int] = set()

            for cond_data in sec_data.get('conditions', []):
                cond = SectionSyncService._upsert_condition(
                    section, cond_data, item_id_map, drug_item_id_map
                )
                surviving_condition_ids.add(cond.id)

            # حذف condition هایی که دیگر در payload نیستند
            SectionSyncService._cleanup_conditions(
                section, surviving_condition_ids
            )

        # ─── حذف سکشن‌هایی که در payload نیستند ───
        OrderSection.objects.filter(order=order).exclude(
            id__in=surviving_section_ids
        ).delete()

        return order

    # ──────────────────────────────────────────────
    #  PRIVATE HELPERS
    # ──────────────────────────────────────────────

    @staticmethod
    def _upsert_section(order: Order, data: dict) -> OrderSection:
        section_id = data.get('id')
        defaults = {
            'title': data.get('title', ''),
            'notes': data.get('notes', ''),
            'is_drug_section': data.get('is_drug_section', False),
            'order_index': data.get('order_index', 0),
            'color': data.get('color', ''),
        }
        if section_id:
            section = get_object_or_404(OrderSection, id=section_id, order=order)
            for k, v in defaults.items():
                setattr(section, k, v)
            section.save()
        else:
            section = OrderSection.objects.create(order=order, **defaults)
        return section

    @staticmethod
    def _upsert_item(section: OrderSection, data: dict) -> SectionItem:
        item_id = data.get('id')
        defaults = {
            'text': data.get('text', ''),
            'notes': data.get('notes', ''),
            'order_index': data.get('order_index', 0),
        }
        if item_id:
            item = get_object_or_404(SectionItem, id=item_id, section=section)
            for k, v in defaults.items():
                setattr(item, k, v)
            item.save()
        else:
            item = SectionItem.objects.create(section=section, **defaults)
        return item

    @staticmethod
    def _upsert_drug_item(section: OrderSection, data: dict) -> DrugSectionItem:
        di_id = data.get('id')
        drug = get_object_or_404(Drug, id=data['drug_id'])
        defaults = {
            'drug': drug,
            'notes': data.get('notes', ''),
            'order_index': data.get('order_index', 0),
        }
        if di_id:
            di = get_object_or_404(DrugSectionItem, id=di_id, section=section)
            for k, v in defaults.items():
                setattr(di, k, v)
            di.save()
        else:
            di = DrugSectionItem.objects.create(section=section, **defaults)
        return di

    @staticmethod
    def _upsert_condition(
        section: OrderSection,
        data: dict,
        item_id_map: Dict[str, int],
        drug_item_id_map: Dict[str, int],
    ) -> Condition:
        cond_id = data.get('id')
        defaults = {
            'text': data.get('text', ''),
            'order_index': data.get('order_index', 0),
        }
        if cond_id:
            cond = get_object_or_404(Condition, id=cond_id)
            for k, v in defaults.items():
                setattr(cond, k, v)
            cond.save()
        else:
            cond = Condition.objects.create(**defaults)

        # ─── اتصال به آیتم‌های متنی ───
        real_item_ids = SectionSyncService._resolve_ids(
            data.get('item_temp_ids', []), item_id_map
        )
        # فقط آیتم‌هایی که به این section تعلق دارند
        valid_items = SectionItem.objects.filter(
            section=section, id__in=real_item_ids
        )
        cond.section_items.set(valid_items)

        # ─── اتصال به آیتم‌های دارویی ───
        real_drug_ids = SectionSyncService._resolve_ids(
            data.get('drug_item_temp_ids', []), drug_item_id_map
        )
        valid_drug_items = DrugSectionItem.objects.filter(
            section=section, id__in=real_drug_ids
        )
        cond.drug_items.set(valid_drug_items)

        return cond

    @staticmethod
    def _cleanup_conditions(section: OrderSection, surviving_ids: set[int]) -> None:
        """
        حذف Condition هایی که فقط به این section وابسته بودند و در payload نیستند.
        """
        related_conditions = Condition.objects.filter(
            Q(section_items__section=section) | Q(drug_items__section=section)
        ).distinct()

        for cond in related_conditions:
            if cond.id in surviving_ids:
                continue
            # جدا کردن از این section
            cond.section_items.remove(*cond.section_items.filter(section=section))
            cond.drug_items.remove(*cond.drug_items.filter(section=section))
            # اگر کلاً بی‌ربط شد، حذف کن
            if not cond.section_items.exists() and not cond.drug_items.exists():
                cond.delete()

    @staticmethod
    def _register_id_map(id_map: Dict[str, int], data: dict, real_id: int) -> None:
        """ثبت mapping از temp_id / str(real_id) به real db id."""
        if data.get('temp_id'):
            id_map[str(data['temp_id'])] = real_id
        if data.get('id'):
            id_map[str(data['id'])] = real_id

    @staticmethod
    def _resolve_ids(raw_ids: List[str], id_map: Dict[str, int]) -> List[int]:
        """تبدیل لیست temp/real id به لیست int."""
        result = []
        for raw in raw_ids:
            raw_str = str(raw)
            if raw_str in id_map:
                result.append(id_map[raw_str])
            elif raw_str.isdigit():
                result.append(int(raw_str))
        return result