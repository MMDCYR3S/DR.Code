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

from .order import Order, AccessChoices

from .section import (
    OrderSection,
    SectionItem,
    DrugSectionItem,
    Condition,
)

from .emergency_disposition import EmergencyDisposition, EmergencyNode

from .dynamic_fields import DynamicFieldGroup, DynamicFieldNode

from .order_image import OrderImage
from .order_video import OrderVideo

__all__ = [
    # رنگ‌ها
    "TailwindColor",

    # Order اصلی
    "Order",
    "AccessChoices",

    # Section‌ها و آیتم‌ها
    "OrderSection",
    "SectionItem",
    "DrugSectionItem",
    "Condition",

    # تعیین تکلیف اورژانس
    "EmergencyDisposition",
    "EmergencyNode",

    # فیلدهای پویا
    "DynamicFieldGroup",
    "DynamicFieldNode",

    # مدیا
    "OrderImage",
    "OrderVideo",
]