import json

from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.accounts.permissions import HasAdminAccessPermission
from apps.ordering.models import (
    Order,
    DynamicFieldGroup,
    EmergencyDisposition,
    OrderImage,
    OrderVideo,
)
from apps.ordering.services import (
    DynamicFieldService,
    OrderService,
    EmergencyService,
    MediaService,
)
from apps.prescriptions.models.category import PrescriptionCategory


# ═══════════════════════════════════════════════════════════════════════════════
# ██  HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def _service_error_response(e: Exception, message: str = "خطا در پردازش درخواست."):
    """تبدیل خطاهای سرویس به JsonResponse یکنواخت."""
    detail = str(e) if isinstance(e, ValidationError) else "خطای داخلی سرور."
    return JsonResponse({"success": False, "message": message, "error": detail}, status=400)


# ═══════════════════════════════════════════════════════════════════════════════
# ██  DYNAMIC FIELD — مرحله ۱ (مستقل از Order)
# ═══════════════════════════════════════════════════════════════════════════════

class DynamicFieldGroupListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    """
    نمایش لیست قالب‌های DynamicFieldGroup و مدیریت CRUD آن‌ها از طریق AJAX.
    این بخش مستقل از Order است — ادمین قالب‌ها را از اینجا می‌سازد.
    """
    model = DynamicFieldGroup
    template_name = "dashboard/ordering/dynamic_fields.html"
    context_object_name = "groups"

    def get_queryset(self):
        return DynamicFieldService.list_groups()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        groups_data = []
        for group in context["groups"]:
            subgroups = []
            for sg in group.subgroups.all():
                subgroups.append({
                    "id": sg.id,
                    "title": sg.title,
                    "order_index": sg.order_index,
                    "items": [
                        {
                            "id": item.id,
                            "key": item.key,
                            "value": item.value,
                            "order_index": item.order_index,
                        }
                        for item in sg.items.all()
                    ],
                })
            groups_data.append({
                "id": group.id,
                "title": group.title,
                "color": group.color,
                "order_index": group.order_index,
                "subgroups": subgroups,
                "created_at": group.shamsi_created_at,
                "updated_at": group.shamsi_updated_at,
            })

        context["groups_json"] = json.dumps(groups_data, ensure_ascii=False)
        return context


class DynamicFieldGroupCreateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ایجاد یک DynamicFieldGroup کامل (Group + SubGroups + Items) در یک درخواست."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "داده‌های ارسالی معتبر نیست."}, status=400)

        try:
            group = DynamicFieldService.create_group(data)
            return JsonResponse({
                "success": True,
                "message": "گروه با موفقیت ایجاد شد.",
                "group": {"id": group.id, "title": group.title},
            }, status=201)
        except Exception as e:
            return _service_error_response(e, "خطا در ایجاد گروه.")


class DynamicFieldGroupUpdateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ویرایش فیلدهای سطح اول گروه (title, color, order_index)."""

    def post(self, request, pk, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "داده‌های ارسالی معتبر نیست."}, status=400)

        try:
            group = DynamicFieldService.update_group(pk, data)
            return JsonResponse({
                "success": True,
                "message": "گروه با موفقیت ویرایش شد.",
                "group": {"id": group.id, "title": group.title},
            })
        except Exception as e:
            return _service_error_response(e, "خطا در ویرایش گروه.")


class DynamicFieldGroupDeleteView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """حذف گروه — زیرگروه‌ها و آیتم‌ها cascade حذف می‌شوند."""

    def post(self, request, pk, *args, **kwargs):
        try:
            DynamicFieldService.delete_group(pk)
            return JsonResponse({"success": True, "message": "گروه با موفقیت حذف شد."})
        except Exception as e:
            return _service_error_response(e, "خطا در حذف گروه.")


class DynamicFieldSubGroupCreateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """اضافه کردن زیرگروه به گروه موجود."""

    def post(self, request, pk, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "داده‌های ارسالی معتبر نیست."}, status=400)

        try:
            subgroup = DynamicFieldService.add_subgroup(pk, data)
            return JsonResponse({
                "success": True,
                "message": "زیرگروه با موفقیت ایجاد شد.",
                "subgroup": {"id": subgroup.id, "title": subgroup.title},
            }, status=201)
        except Exception as e:
            return _service_error_response(e, "خطا در ایجاد زیرگروه.")


class DynamicFieldItemCreateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """اضافه کردن آیتم key-value به زیرگروه موجود."""

    def post(self, request, pk, *args, **kwargs):
        """pk = subgroup_id"""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "داده‌های ارسالی معتبر نیست."}, status=400)

        try:
            item = DynamicFieldService.add_item(pk, data)
            return JsonResponse({
                "success": True,
                "message": "آیتم با موفقیت ایجاد شد.",
                "item": {"id": item.id, "key": item.key, "value": item.value},
            }, status=201)
        except Exception as e:
            return _service_error_response(e, "خطا در ایجاد آیتم.")


# ═══════════════════════════════════════════════════════════════════════════════
# ██  ORDER — مرحله ۲
# ═══════════════════════════════════════════════════════════════════════════════

class OrderListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    """
    نمایش لیست همه Orders.
    از اینجا به صفحه ساخت Order یا جزئیات هر Order می‌رود.
    """
    model = Order
    template_name = "dashboard/ordering/order_list.html"
    context_object_name = "orders"
    ordering = ["-created_at"]

    def get_queryset(self):
        return OrderService.list_orders()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            context["orders"] = Order.objects.filter(
                Q(imp__icontains=search_query) |
                Q(condition__icontains=search_query) |
                Q(category__title__icontains=search_query)
            ).select_related("category").order_by("-created_at")

        orders_data = [
            {
                "id": o.id,
                "imp": o.imp[:80],
                "category": o.category.title if o.category else "—",
                "color": o.color,
                "created_at": o.shamsi_created_at,
                "updated_at": o.shamsi_updated_at,
            }
            for o in context["orders"]
        ]
        context["orders_json"] = json.dumps(orders_data, ensure_ascii=False)
        return context


class OrderCreateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """
    مرحله ۲: ایجاد Order.

    GET  → فرم ایجاد Order به همراه لیست DynamicFieldGroup‌های موجود
    POST → ذخیره Order از طریق OrderService و redirect به مرحله ۳ (emergency)

    order_id از طریق URL به مراحل بعد منتقل می‌شود.
    """

    template_name = "dashboard/ordering/order_create.html"

    def get(self, request, *args, **kwargs):
        context = {
            "categories": PrescriptionCategory.objects.all(),
            "dynamic_field_groups": DynamicFieldService.list_groups(),
            "dynamic_field_groups_json": json.dumps(
                [
                    {
                        "id": g.id,
                        "title": g.title,
                        "color": g.color,
                        "subgroups": [
                            {
                                "id": sg.id,
                                "title": sg.title,
                                "items": [
                                    {"id": i.id, "key": i.key, "value": i.value}
                                    for i in sg.items.all()
                                ],
                            }
                            for sg in g.subgroups.all()
                        ],
                    }
                    for g in DynamicFieldService.list_groups()
                ],
                ensure_ascii=False,
            ),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "داده‌های ارسالی معتبر نیست."}, status=400)

        try:
            order = OrderService.create(data)
            return JsonResponse({
                "success": True,
                "message": "Order با موفقیت ایجاد شد.",
                "order_id": order.id,
                # URL مرحله بعد را برمی‌گردانیم تا JS redirect کند
                "next_url": f"/dashboard/ordering/{order.id}/emergency/",
            }, status=201)
        except ValidationError as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
        except Exception as e:
            return _service_error_response(e, "خطا در ایجاد Order.")


class OrderUpdateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ویرایش Order موجود."""

    template_name = "dashboard/ordering/order_update.html"

    def get(self, request, pk, *args, **kwargs):
        order = get_object_or_404(Order, pk=pk)
        context = {
            "order": order,
            "categories": PrescriptionCategory.objects.all(),
            "dynamic_field_groups": DynamicFieldService.list_groups(),
            "order_json": json.dumps({
                "id": order.id,
                "imp": order.imp,
                "condition": order.condition,
                "diet": order.diet,
                "action": order.action,
                "position": order.position,
                "notes": order.notes,
                "color": order.color,
                "category_id": order.category_id,
                "dynamic_field_group_ids": list(
                    order.dynamic_field_groups.values_list("id", flat=True)
                ),
            }, ensure_ascii=False),
        }
        return render(request, self.template_name, context)

    def post(self, request, pk, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "داده‌های ارسالی معتبر نیست."}, status=400)

        try:
            order = OrderService.update(pk, data)
            return JsonResponse({
                "success": True,
                "message": "Order با موفقیت ویرایش شد.",
                "order_id": order.id,
            })
        except ValidationError as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
        except Exception as e:
            return _service_error_response(e, "خطا در ویرایش Order.")


class OrderDeleteView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """حذف Order — تمام زیرمجموعه‌ها cascade حذف می‌شوند."""

    def post(self, request, pk, *args, **kwargs):
        try:
            OrderService.delete(pk)
            return JsonResponse({"success": True, "message": "Order با موفقیت حذف شد."})
        except Exception as e:
            return _service_error_response(e, "خطا در حذف Order.")


class OrderDetailView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """نمایش کامل یک Order به همراه تمام زیرمجموعه‌ها."""

    template_name = "dashboard/ordering/order_detail.html"

    def get(self, request, pk, *args, **kwargs):
        try:
            order = OrderService.get_order(pk)
        except ValidationError:
            return JsonResponse({"success": False, "message": "Order یافت نشد."}, status=404)

        # بررسی اینکه تعیین تکلیف دارد یا نه
        has_emergency = hasattr(order, "emergency_disposition")
        media = MediaService.get_media(pk)

        context = {
            "order": order,
            "has_emergency": has_emergency,
            "images": media["images"],
            "videos": media["videos"],
        }
        return render(request, self.template_name, context)


class OrderSearchView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """جستجوی Orders بر اساس imp / condition / category."""

    def get(self, request, *args, **kwargs):
        q = request.GET.get("q", "").strip()

        qs = Order.objects.select_related("category")
        if q:
            qs = qs.filter(
                Q(imp__icontains=q) |
                Q(condition__icontains=q) |
                Q(category__title__icontains=q)
            )
        qs = qs.order_by("-created_at")

        data = [
            {
                "id": o.id,
                "imp": o.imp[:80],
                "category": o.category.title if o.category else "—",
                "color": o.color,
                "created_at": o.shamsi_created_at,
            }
            for o in qs
        ]
        return JsonResponse({"success": True, "orders": data, "count": len(data)})


# ═══════════════════════════════════════════════════════════════════════════════
# ██  EMERGENCY DISPOSITION — مرحله ۳
# ═══════════════════════════════════════════════════════════════════════════════

class EmergencyCreateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """
    مرحله ۳: تعیین تکلیف اورژانس.

    GET  → فرم ساخت تعیین تکلیف — order_id از URL می‌آید
    POST → ذخیره از طریق EmergencyService و redirect به مرحله ۴ (media)

    اگر Order از قبل disposition داشته باشد، به صفحه ویرایش redirect می‌شود.
    """

    template_name = "dashboard/ordering/emergency_create.html"

    def get(self, request, pk, *args, **kwargs):
        order = get_object_or_404(Order, pk=pk)

        # اگر قبلاً ساخته شده → redirect به update
        if hasattr(order, "emergency_disposition"):
            return redirect("ordering:emergency_update", pk=pk)

        context = {"order": order, "order_id": pk}
        return render(request, self.template_name, context)

    def post(self, request, pk, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "داده‌های ارسالی معتبر نیست."}, status=400)

        try:
            EmergencyService.create_for_order(pk, data)
            return JsonResponse({
                "success": True,
                "message": "تعیین تکلیف با موفقیت ثبت شد.",
                "next_url": f"/dashboard/ordering/{pk}/media/",
            }, status=201)
        except ValidationError as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
        except Exception as e:
            return _service_error_response(e, "خطا در ثبت تعیین تکلیف.")


class EmergencyUpdateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ویرایش تعیین تکلیف اورژانس موجود."""

    template_name = "dashboard/ordering/emergency_update.html"

    def get(self, request, pk, *args, **kwargs):
        order = get_object_or_404(Order, pk=pk)
        try:
            disposition = EmergencyService.get_for_order(pk)
        except ValidationError:
            return redirect("ordering:emergency_create", pk=pk)

        context = {
            "order": order,
            "disposition": disposition,
            "disposition_json": json.dumps({
                "id": disposition.id,
                "title": disposition.title,
                "color": disposition.color,
                "notes": disposition.notes,
                "nodes": _serialize_nodes(disposition.nodes.filter(parent__isnull=True)),
            }, ensure_ascii=False),
        }
        return render(request, self.template_name, context)

    def post(self, request, pk, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "داده‌های ارسالی معتبر نیست."}, status=400)

        try:
            disposition = EmergencyService.get_for_order(pk)
            EmergencyService.update(disposition.id, data)
            return JsonResponse({"success": True, "message": "تعیین تکلیف با موفقیت ویرایش شد."})
        except ValidationError as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
        except Exception as e:
            return _service_error_response(e, "خطا در ویرایش تعیین تکلیف.")


class EmergencyDeleteView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """حذف تعیین تکلیف — گره‌ها cascade حذف می‌شوند."""

    def post(self, request, pk, *args, **kwargs):
        try:
            disposition = EmergencyService.get_for_order(pk)
            EmergencyService.delete(disposition.id)
            return JsonResponse({"success": True, "message": "تعیین تکلیف با موفقیت حذف شد."})
        except ValidationError as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
        except Exception as e:
            return _service_error_response(e, "خطا در حذف تعیین تکلیف.")


# ═══════════════════════════════════════════════════════════════════════════════
# ██  MEDIA — مرحله ۴
# ═══════════════════════════════════════════════════════════════════════════════

class MediaView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """
    مرحله ۴: مدیریت Media (تصاویر + ویدیوها) برای یک Order.

    GET  → صفحه آپلود media — order_id از URL می‌آید
    """

    template_name = "dashboard/ordering/media.html"

    def get(self, request, pk, *args, **kwargs):
        order = get_object_or_404(Order, pk=pk)
        media = MediaService.get_media(pk)
        context = {
            "order": order,
            "images": media["images"],
            "videos": media["videos"],
        }
        return render(request, self.template_name, context)


class MediaImageUploadView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """آپلود یک یا چند تصویر به Order."""

    def post(self, request, pk, *args, **kwargs):
        files = request.FILES.getlist("images")
        if not files:
            return JsonResponse({"success": False, "message": "هیچ فایلی ارسال نشده."}, status=400)

        try:
            captions = request.POST.getlist("captions")
            images = MediaService.add_images_bulk(pk, files, captions)
            return JsonResponse({
                "success": True,
                "message": f"{len(images)} تصویر با موفقیت آپلود شد.",
                "images": [
                    {
                        "id": img.id,
                        "caption": img.caption,
                        "url": img.image.url,
                        "order_index": img.order_index,
                    }
                    for img in images
                ],
            }, status=201)
        except Exception as e:
            return _service_error_response(e, "خطا در آپلود تصویر.")


class MediaImageUpdateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ویرایش caption یا ترتیب تصویر."""

    def post(self, request, pk, image_id, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "داده‌های ارسالی معتبر نیست."}, status=400)

        try:
            image = MediaService.update_image(image_id, data)
            return JsonResponse({
                "success": True,
                "message": "تصویر با موفقیت ویرایش شد.",
                "image": {"id": image.id, "caption": image.caption},
            })
        except Exception as e:
            return _service_error_response(e, "خطا در ویرایش تصویر.")


class MediaImageDeleteView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """حذف تصویر و فایل فیزیکی آن."""

    def post(self, request, pk, image_id, *args, **kwargs):
        try:
            MediaService.delete_image(image_id)
            return JsonResponse({"success": True, "message": "تصویر با موفقیت حذف شد."})
        except Exception as e:
            return _service_error_response(e, "خطا در حذف تصویر.")


class MediaVideoCreateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """اضافه کردن لینک ویدیو (Embed URL) به Order."""

    def post(self, request, pk, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "داده‌های ارسالی معتبر نیست."}, status=400)

        try:
            video = MediaService.add_video(pk, data)
            return JsonResponse({
                "success": True,
                "message": "ویدیو با موفقیت اضافه شد.",
                "video": {
                    "id": video.id,
                    "title": video.title,
                    "video_url": video.video_url,
                    "order_index": video.order_index,
                },
            }, status=201)
        except ValidationError as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
        except Exception as e:
            return _service_error_response(e, "خطا در افزودن ویدیو.")


class MediaVideoUpdateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ویرایش عنوان / URL / ترتیب ویدیو."""

    def post(self, request, pk, video_id, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "داده‌های ارسالی معتبر نیست."}, status=400)

        try:
            video = MediaService.update_video(video_id, data)
            return JsonResponse({
                "success": True,
                "message": "ویدیو با موفقیت ویرایش شد.",
                "video": {"id": video.id, "title": video.title},
            })
        except Exception as e:
            return _service_error_response(e, "خطا در ویرایش ویدیو.")


class MediaVideoDeleteView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """حذف ویدیو."""

    def post(self, request, pk, video_id, *args, **kwargs):
        try:
            MediaService.delete_video(video_id)
            return JsonResponse({"success": True, "message": "ویدیو با موفقیت حذف شد."})
        except Exception as e:
            return _service_error_response(e, "خطا در حذف ویدیو.")


# ═══════════════════════════════════════════════════════════════════════════════
# ██  PRIVATE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _serialize_nodes(nodes_qs) -> list:
    """سریال‌سازی recursive درخت EmergencyNode برای JSON."""
    result = []
    for node in nodes_qs:
        result.append({
            "id": node.id,
            "title": node.title,
            "content": node.content,
            "internal_notes": node.internal_notes,
            "color": node.color,
            "order_index": node.order_index,
            "children": _serialize_nodes(node.children.all()),
        })
    return result