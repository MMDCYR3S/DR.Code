"""
اپلیکیشن ordering — اوردرنویسی پزشکی
======================================

ساختار مدل‌ها:

  colors.py              → TailwindColor (enum 30 رنگ)

  order.py               → Order
  section.py             → OrderSection, SectionItem,
                           ItemCondition,
                           DrugSectionItem, DrugItemCondition
  item_note.py           → ItemNote   (جدول جداگانه توضیحات آیتم/Section)
  emergency_disposition.py → EmergencyDisposition, EmergencyNode
  dynamic_fields.py          → DynamicFieldGroup, DynamicFieldSubGroup, DynamicFieldItem
  order_image.py         → OrderImage
  order_video.py         → OrderVideo
"""

from .colors import TailwindColor

from .order import Order

from .section import (
    OrderSection,
    SectionItem,
    ItemCondition,
    DrugSectionItem,
    DrugItemCondition,
)

from .item_note import ItemNote

from .emergency_disposition import EmergencyDisposition, EmergencyNode

from .dynamic_fields import DynamicFieldGroup, DynamicFieldSubGroup, DynamicFieldItem

from .order_image import OrderImage
from .order_video import OrderVideo

__all__ = [
    # رنگ‌ها
    "TailwindColor",

    # Order اصلی
    "Order",

    # Section‌ها و آیتم‌ها
    "OrderSection",
    "SectionItem",
    "ItemCondition",
    "DrugSectionItem",
    "DrugItemCondition",

    # توضیحات جداگانه
    "ItemNote",

    # تعیین تکلیف اورژانس
    "EmergencyDisposition",
    "EmergencyNode",

    # فیلدهای پویا
    "DynamicFieldGroup",
    "DynamicFieldSubGroup",
    "DynamicFieldItem",

    # مدیا
    "OrderImage",
    "OrderVideo",
]