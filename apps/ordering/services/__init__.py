"""
ordering/services
=================
لایه سرویس اپلیکیشن ordering.

چهار سرویس مستقل — هر کدام مسئول یک مرحله از UI:

  مرحله ۱ — DynamicFieldService
      مدیریت قالب‌های DynamicFieldGroup (مستقل از Order).
      در UI قبل از ساخت Order نمایش داده می‌شود تا کاربر گروه‌ها را انتخاب کند.

  مرحله ۲ — OrderService
      ایجاد و ویرایش Order به همراه:
        - اتصال DynamicFieldGroup‌های انتخاب‌شده
        - Section‌ها، Items، Conditions، Notes

  مرحله ۳ — EmergencyService
      تعیین تکلیف اورژانس.
      Order را از id شناسایی می‌کند — کاربر نیازی به انتخاب مجدد ندارد.

  مرحله ۴ — MediaService
      آپلود تصویر و افزودن لینک ویدیو به Order ساخته‌شده.
"""

from .dynamic_field_service import DynamicFieldService
from .order_service import OrderService
from .emergency_service import EmergencyService
from .media_service import MediaService

__all__ = [
    "DynamicFieldService",
    "OrderService",
    "EmergencyService",
    "MediaService",
]