"""
views/order_extended_views.py
==============================
ویوهای مرتبط با:
  - DynamicFieldSyncService  (پیش‌بالینی)
  - EmergencySyncService     (تعیین تکلیف اورژانسی)
  - MediaService             (فایل‌های پیوست)
  - صفحه ترکیبی Order (partial با 4 بخش)
"""

from __future__ import annotations

import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from apps.ordering.models import Order, DynamicFieldGroup, EmergencyDisposition
from apps.ordering.services.dynamic_field_sync_service import DynamicFieldSyncService
from apps.ordering.services.emergency_sync_service import EmergencySyncService
from apps.ordering.services.media_service import MediaService
from ...forms import OrderForm

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  صفحه اصلی — 4 بخشی
# ═══════════════════════════════════════════════════════════════════════════

class OrderExtendedFormView(LoginRequiredMixin, TemplateView):
    """
    صفحه ترکیبی اوردر با 4 بخش مجزا:
      1. اطلاعات پایه Order     (همیشه فعال)
      2. پیش‌بالینی             (DynamicFieldGroup — بعد از ذخیره Order)
      3. تعیین تکلیف اورژانسی  (EmergencyDisposition — بعد از ذخیره Order)
      4. فایل‌های پیوست         (Media — بعد از ذخیره Order)
    """
    template_name = "dashboard/ordering/order_extended_form.html"

    def post(self, request, *args, **kwargs):
        """POST برای ویرایش اطلاعات پایه Order از تب اول."""
        order_id = self.kwargs.get("pk")
        if not order_id:
            return redirect("dashboard:ordering:order_create")
        order = get_object_or_404(Order, pk=order_id)
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'اوردر "{order.name}" بروزرسانی شد.')
            return redirect("dashboard:ordering:order_extended_form", pk=order_id)
        ctx = self._build_context(order_id=order_id, form_instance=form)
        return self.render_to_response(ctx)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order_id = self.kwargs.get("pk")
        ctx.update(self._build_context(order_id=order_id))
        return ctx

    def _build_context(self, order_id=None, form_instance=None):
        order = None
        dynamic_groups = []
        emergency_disposition = None
        media = {"images": [], "videos": []}

        if order_id:
            order = get_object_or_404(Order, pk=order_id)
            dynamic_groups = list(DynamicFieldSyncService.get_groups(order_id))
            try:
                emergency_disposition = EmergencySyncService.get_for_order(order_id)
            except Exception:
                emergency_disposition = None
            try:
                media = MediaService.get_media(order_id)
            except Exception:
                pass

        if form_instance is not None:
            form = form_instance
        elif order:
            form = OrderForm(instance=order)
        else:
            form = OrderForm()

        return {
            "object": order,
            "form": form,
            "dynamic_groups": dynamic_groups,
            "emergency_disposition": emergency_disposition,
            "media_images": media.get("images", []),
            "media_videos": media.get("videos", []),
            "tailwind_colors": _get_tailwind_colors(),
        }


# ═══════════════════════════════════════════════════════════════════════════
#  DynamicField Views
# ═══════════════════════════════════════════════════════════════════════════

class DynamicFieldSyncView(LoginRequiredMixin, View):
    """
    POST /orders/<order_id>/dynamic-fields/sync/
    ذخیره یکجا تمام گروه‌های پویا برای یک Order.
    """

    def post(self, request, order_id: int):
        try:
            payload = json.loads(request.body)
            groups = payload.get("groups", [])
            DynamicFieldSyncService.sync(order_id, groups)
            return JsonResponse({"success": True, "message": "فیلدهای پویا ذخیره شدند."})
        except Exception as e:
            logger.exception("DynamicFieldSyncView error")
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class DynamicFieldGroupDetailView(LoginRequiredMixin, View):
    """
    GET  /orders/<order_id>/dynamic-fields/
        → دریافت تمام گروه‌های یک Order به صورت JSON

    DELETE /orders/dynamic-fields/group/<group_id>/
        → حذف یک گروه
    """

    def get(self, request, order_id: int):
        try:
            groups = DynamicFieldSyncService.get_groups(order_id)
            data = _serialize_groups(groups)
            return JsonResponse({"success": True, "groups": data})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class DynamicFieldGroupDeleteView(LoginRequiredMixin, View):
    def post(self, request, group_id: int):
        try:
            DynamicFieldSyncService.delete_group(group_id)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class DynamicFieldSubGroupDeleteView(LoginRequiredMixin, View):
    def post(self, request, subgroup_id: int):
        try:
            DynamicFieldSyncService.delete_subgroup(subgroup_id)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class DynamicFieldItemDeleteView(LoginRequiredMixin, View):
    def post(self, request, item_id: int):
        try:
            DynamicFieldSyncService.delete_item(item_id)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


# ═══════════════════════════════════════════════════════════════════════════
#  Emergency Disposition Views
# ═══════════════════════════════════════════════════════════════════════════

class EmergencySyncView(LoginRequiredMixin, View):
    """
    POST /orders/<order_id>/emergency/sync/
    ذخیره یکجا تعیین تکلیف اورژانسی برای یک Order.
    """

    def post(self, request, order_id: int):
        try:
            payload = json.loads(request.body)
            EmergencySyncService.sync(order_id, payload)
            return JsonResponse({"success": True, "message": "تعیین تکلیف ذخیره شد."})
        except Exception as e:
            logger.exception("EmergencySyncView error")
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class EmergencyDetailView(LoginRequiredMixin, View):
    """
    GET /orders/<order_id>/emergency/
    دریافت تعیین تکلیف یک Order به صورت JSON.
    """

    def get(self, request, order_id: int):
        try:
            disposition = EmergencySyncService.get_for_order(order_id)
            data = _serialize_disposition(disposition)
            return JsonResponse({"success": True, "disposition": data})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=404)


class EmergencyNodeDeleteView(LoginRequiredMixin, View):
    def post(self, request, node_id: int):
        try:
            EmergencySyncService.delete_node(node_id)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class EmergencyDeleteView(LoginRequiredMixin, View):
    def post(self, request, disposition_id: int):
        try:
            EmergencySyncService.delete(disposition_id)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


# ═══════════════════════════════════════════════════════════════════════════
#  Media Views
# ═══════════════════════════════════════════════════════════════════════════

class MediaAddImageView(LoginRequiredMixin, View):
    """POST /orders/<order_id>/media/image/add/"""

    def post(self, request, order_id: int):
        try:
            image_file = request.FILES.get("image")
            if not image_file:
                return JsonResponse({"success": False, "error": "فایل تصویر ارسال نشده."}, status=400)

            data = {
                "caption": request.POST.get("caption", ""),
                "order_index": int(request.POST.get("order_index", 0)),
            }
            image = MediaService.add_image(order_id, image_file, data)
            return JsonResponse({
                "success": True,
                "image": {
                    "id": image.id,
                    "url": image.image.url if image.image else "",
                    "caption": image.caption,
                    "order_index": image.order_index,
                }
            })
        except Exception as e:
            logger.exception("MediaAddImageView error")
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class MediaAddImageBulkView(LoginRequiredMixin, View):
    """POST /orders/<order_id>/media/images/bulk/"""

    def post(self, request, order_id: int):
        try:
            files = request.FILES.getlist("images")
            captions = request.POST.getlist("captions")
            images = MediaService.add_images_bulk(order_id, files, captions)
            return JsonResponse({
                "success": True,
                "images": [
                    {"id": img.id, "url": img.image.url if img.image else "", "caption": img.caption}
                    for img in images
                ]
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class MediaUpdateImageView(LoginRequiredMixin, View):
    """POST /orders/media/image/<image_id>/update/"""

    def post(self, request, image_id: int):
        try:
            payload = json.loads(request.body)
            image = MediaService.update_image(image_id, payload)
            return JsonResponse({"success": True, "caption": image.caption})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class MediaDeleteImageView(LoginRequiredMixin, View):
    """POST /orders/media/image/<image_id>/delete/"""

    def post(self, request, image_id: int):
        try:
            MediaService.delete_image(image_id)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class MediaAddVideoView(LoginRequiredMixin, View):
    """POST /orders/<order_id>/media/video/add/"""

    def post(self, request, order_id: int):
        try:
            payload = json.loads(request.body)
            video = MediaService.add_video(order_id, payload)
            return JsonResponse({
                "success": True,
                "video": {
                    "id": video.id,
                    "video_url": video.video_url,
                    "title": video.title,
                    "description": video.description,
                    "order_index": video.order_index,
                }
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class MediaUpdateVideoView(LoginRequiredMixin, View):
    """POST /orders/media/video/<video_id>/update/"""

    def post(self, request, video_id: int):
        try:
            payload = json.loads(request.body)
            video = MediaService.update_video(video_id, payload)
            return JsonResponse({"success": True, "title": video.title})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class MediaDeleteVideoView(LoginRequiredMixin, View):
    """POST /orders/media/video/<video_id>/delete/"""

    def post(self, request, video_id: int):
        try:
            MediaService.delete_video(video_id)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _get_tailwind_colors():
    from apps.ordering.models.colors import TailwindColor
    return TailwindColor.choices


def _serialize_groups(groups) -> list:
    result = []
    for g in groups:
        subgroups = []
        for sg in g.subgroups.all():
            items = [
                {"id": it.id, "key": it.key, "value": it.value, "order_index": it.order_index}
                for it in sg.items.all()
            ]
            subgroups.append({
                "id": sg.id,
                "title": sg.title,
                "order_index": sg.order_index,
                "items": items,
            })
        result.append({
            "id": g.id,
            "title": g.title,
            "order_index": g.order_index,
            "color": g.color,
            "subgroups": subgroups,
        })
    return result


def _serialize_disposition(disposition) -> dict:
    def serialize_node(node):
        return {
            "id": node.id,
            "title": node.title,
            "content": node.content,
            "internal_notes": node.internal_notes,
            "order_index": node.order_index,
            "color": node.color,
            "children": [serialize_node(c) for c in node.children.all()],
        }

    root_nodes = [n for n in disposition.nodes.all() if n.parent_id is None]
    return {
        "id": disposition.id,
        "title": disposition.title,
        "color": disposition.color,
        "notes": disposition.notes,
        "nodes": [serialize_node(n) for n in root_nodes],
    }