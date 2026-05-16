"""
services/media_service.py
==========================
سرویس مدیریت Media (تصاویر و ویدیوها) برای Order.

این سرویس به‌صورت مستقل در مرحله آخر UI اجرا می‌شود.
Order از قبل ساخته شده و media به آن اضافه می‌شود.

عملیات:
  - اضافه کردن تصویر(ها) به Order موجود
  - اضافه کردن ویدیو به Order موجود
  - ویرایش caption / عنوان / ترتیب
  - حذف تصویر / ویدیو
  - بازیابی تمام media یک Order
"""

from __future__ import annotations

from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.ordering.models import Order, OrderImage, OrderVideo


class MediaService:

    # ══════════════════════════════════════════════════════════════════════
    #  IMAGE
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def add_image(order_id: int, image_file: InMemoryUploadedFile, data: dict = None) -> OrderImage:
        """
        اضافه کردن یک تصویر به Order موجود.
        فشرده‌سازی از طریق Celery task به‌صورت async انجام می‌شود
        (منطق در OrderImage.save() تعریف شده).
        """
        data = data or {}
        order = MediaService._get_order(order_id)

        image = OrderImage(
            order=order,
            caption=data.get("caption", ""),
            order_index=data.get("order_index", 0),
        )
        image.image = image_file
        image.save()  # Celery task فشرده‌سازی اینجا صف می‌شود

        return image

    @staticmethod
    @transaction.atomic
    def add_images_bulk(order_id: int, image_files: list, captions: list = None) -> list[OrderImage]:
        """
        آپلود چند تصویر به‌صورت یکجا.
        captions لیستی از رشته است؛ اگر کمتر از تعداد فایل‌ها باشد، بقیه خالی می‌شوند.
        """
        captions = captions or []
        order = MediaService._get_order(order_id)
        created = []

        for idx, image_file in enumerate(image_files):
            image = OrderImage(
                order=order,
                caption=captions[idx] if idx < len(captions) else "",
                order_index=idx,
            )
            image.image = image_file
            image.save()
            created.append(image)

        return created

    @staticmethod
    @transaction.atomic
    def update_image(image_id: int, data: dict) -> OrderImage:
        try:
            image = OrderImage.objects.get(pk=image_id)
        except OrderImage.DoesNotExist:
            raise ValidationError(f"تصویر با id={image_id} یافت نشد.")

        for field in ("caption", "order_index"):
            if field in data:
                setattr(image, field, data[field])
        image.save(update_fields=["caption", "order_index", "updated_at"])
        return image

    @staticmethod
    @transaction.atomic
    def delete_image(image_id: int) -> None:
        try:
            image = OrderImage.objects.get(pk=image_id)
        except OrderImage.DoesNotExist:
            raise ValidationError(f"تصویر با id={image_id} یافت نشد.")

        # حذف فایل فیزیکی از storage
        if image.image:
            image.image.delete(save=False)
        image.delete()

    # ══════════════════════════════════════════════════════════════════════
    #  VIDEO
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    @transaction.atomic
    def add_video(order_id: int, data: dict) -> OrderVideo:
        """
        اضافه کردن لینک ویدیو (Embed URL) به Order.
        فایل ویدیویی روی سرور ذخیره نمی‌شود.
        """
        order = MediaService._get_order(order_id)

        if not data.get("video_url"):
            raise ValidationError("فیلد video_url اجباری است.")

        return OrderVideo.objects.create(
            order=order,
            video_url=data["video_url"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            order_index=data.get("order_index", 0),
        )

    @staticmethod
    @transaction.atomic
    def update_video(video_id: int, data: dict) -> OrderVideo:
        try:
            video = OrderVideo.objects.get(pk=video_id)
        except OrderVideo.DoesNotExist:
            raise ValidationError(f"ویدیو با id={video_id} یافت نشد.")

        for field in ("video_url", "title", "description", "order_index"):
            if field in data:
                setattr(video, field, data[field])
        video.save()
        return video

    @staticmethod
    @transaction.atomic
    def delete_video(video_id: int) -> None:
        deleted, _ = OrderVideo.objects.filter(pk=video_id).delete()
        if not deleted:
            raise ValidationError(f"ویدیو با id={video_id} یافت نشد.")

    # ══════════════════════════════════════════════════════════════════════
    #  READ
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_media(order_id: int) -> dict:
        """
        بازیابی تمام media یک Order به‌صورت یکجا.
        خروجی: {"images": QuerySet, "videos": QuerySet}
        """
        order = MediaService._get_order(order_id)
        return {
            "images": order.images.order_by("order_index"),
            "videos": order.videos.order_by("order_index"),
        }

    # ══════════════════════════════════════════════════════════════════════
    #  PRIVATE
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _get_order(order_id: int) -> Order:
        try:
            return Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            raise ValidationError(f"Order با id={order_id} یافت نشد.")
