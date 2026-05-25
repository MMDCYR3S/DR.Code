import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.ordering.models import Order
from apps.ordering.services.order_service import OrderService, SectionSyncService
from apps.accounts.permissions import HasAdminAccessPermission, IsTokenJtiActive
from ...forms import OrderFilterForm, OrderForm

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════
#  ORDER LIST
# ════════════════════════════════════════════════════════
class OrderListView(
    LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView
):
    model = Order
    template_name = 'dashboard/ordering/orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        queryset = Order.objects.select_related('category').all()
        form = OrderFilterForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            category = form.cleaned_data.get('category')
            color = form.cleaned_data.get('color')
            sort_by = form.cleaned_data.get('sort_by')

            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(imp__icontains=search) |
                    Q(condition__icontains=search) |
                    Q(diet__icontains=search) |
                    Q(action__icontains=search) |
                    Q(position__icontains=search) |
                    Q(notes__icontains=search)
                ).distinct()
            if category:
                queryset = queryset.filter(category=category)
            if color:
                queryset = queryset.filter(color=color)
            queryset = queryset.order_by(sort_by) if sort_by else queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders_with_color = [
            {
                'object': order,
                'category_color': (
                    f'bg-{order.category.color_code}-500'
                    if order.category and order.category.color_code
                    else 'bg-slate-500'
                ),
                'category_title': order.category.title if order.category else 'No Category',
                'order_color': f'bg-{order.color}-500' if order.color else 'bg-gray-500',
            }
            for order in context['orders']
        ]
        context['filter_form'] = OrderFilterForm(self.request.GET)
        context['orders_data'] = orders_with_color
        return context


# ════════════════════════════════════════════════════════
#  ORDER CREATE
# ════════════════════════════════════════════════════════
class OrderCreateView(
    LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, CreateView
):
    """
    POST /orders/create/
    اگر درخواست JSON بود → اوردر می‌سازد و id را برمی‌گرداند (برای SPA flow).
    اگر form معمولی بود → redirect به صفحه ویرایش.
    """
    model = Order
    form_class = OrderForm
    template_name = 'dashboard/ordering/order_form.html'

    def post(self, request, *args, **kwargs):
        # ─── JSON (fetch) flow ───
        content_type = request.content_type or ''
        if 'application/json' in content_type:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'فرمت JSON نامعتبر'}, status=400)

            required = ['name', 'imp', 'condition', 'diet', 'action', 'position', 'category_id']
            missing = [f for f in required if not data.get(f)]
            if missing:
                return JsonResponse(
                    {'success': False, 'message': f'فیلدهای اجباری: {", ".join(missing)}'},
                    status=400,
                )

            try:
                order = OrderService.create_order(data)
                return JsonResponse({
                    'success': True,
                    'order_id': order.id,
                    'edit_url': request.build_absolute_uri(
                        reverse_lazy('dashboard:ordering:order_update', kwargs={'pk': order.id})
                    ),
                    'message': f'اوردر "{order.name}" با موفقیت ساخته شد',
                })
            except Exception as e:
                logger.exception('Error creating order (JSON)')
                return JsonResponse({'success': False, 'message': str(e)}, status=500)

        # ─── Form flow ───
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            data = {
                'name': form.cleaned_data['name'],
                'imp': form.cleaned_data['imp'],
                'condition': form.cleaned_data['condition'],
                'diet': form.cleaned_data['diet'],
                'action': form.cleaned_data['action'],
                'position': form.cleaned_data['position'],
                'notes': form.cleaned_data.get('notes', ''),
                'category_id': form.cleaned_data['category'].id,
                'color': form.cleaned_data.get('color', ''),
            }
            order = OrderService.create_order(data)
            messages.success(self.request, f'اوردر "{order.name}" با موفقیت ایجاد شد.')
            from django.shortcuts import redirect
            return redirect('dashboard:ordering:order_update', pk=order.id)
        except Exception as e:
            messages.error(self.request, f'خطا در ایجاد اوردر: {str(e)}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ایجاد اوردر جدید'
        context['submit_text'] = 'ایجاد اوردر'
        return context


# ════════════════════════════════════════════════════════
#  ORDER UPDATE
# ════════════════════════════════════════════════════════
class OrderUpdateView(
    LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, UpdateView
):
    model = Order
    form_class = OrderForm
    template_name = 'dashboard/ordering/order_form.html'
    success_url = reverse_lazy('dashboard:ordering:order_list')

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'sections',
            # 'sections__condition',
            'sections__items',
            'sections__drug_items',
            'sections__drug_items__drug'
        )

    def form_valid(self, form):
        try:
            data = {
                'name': form.cleaned_data['name'],
                'imp': form.cleaned_data['imp'],
                'condition': form.cleaned_data['condition'],
                'diet': form.cleaned_data['diet'],
                'action': form.cleaned_data['action'],
                'position': form.cleaned_data['position'],
                'notes': form.cleaned_data.get('notes', ''),
                'category_id': form.cleaned_data['category'].id,
                'color': form.cleaned_data.get('color', ''),
            }
            order = OrderService.update_order(self.object.id, data)
            messages.success(self.request, f'اوردر "{order.name}" بروزرسانی شد.')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'خطا در ویرایش اوردر: {str(e)}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'ویرایش اوردر: {self.object.name}'
        context['submit_text'] = 'بروزرسانی اوردر'
        return context


# ════════════════════════════════════════════════════════
#  ORDER DELETE
# ════════════════════════════════════════════════════════
class OrderDeleteView(
    LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, DeleteView
):
    model = Order
    template_name = 'dashboard/ordering/order_confirm_delete.html'
    success_url = reverse_lazy('dashboard:ordering:order_list')

    def delete(self, request, *args, **kwargs):
        order = self.get_object()
        order_name = order.name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'اوردر "{order_name}" حذف شد.')
        return response


# ════════════════════════════════════════════════════════
#  DRUG SEARCH
# ════════════════════════════════════════════════════════
class DrugSearchView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """جستجوی پویای دارو برای autocomplete."""

    def get(self, request):
        from apps.prescriptions.models import Drug
        q = request.GET.get('q', '').strip()
        if len(q) < 2:
            return JsonResponse({'success': True, 'drugs': []})
        drugs = Drug.objects.filter(
            Q(title__icontains=q) | Q(code__icontains=q)
        )[:20]
        return JsonResponse({
            'success': True,
            'drugs': [{'id': d.id, 'title': d.title, 'code': getattr(d, 'code', '')} for d in drugs],
        })


# ════════════════════════════════════════════════════════
#  SECTION BULK SYNC  —  تنها endpoint برای Section/Item/Condition
# ════════════════════════════════════════════════════════
class SectionBulkSyncView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """
    POST /orders/<order_id>/sections/sync/

    یک endpoint یکپارچه برای ذخیره همه Section ها، آیتم‌ها و شرط‌های یک Order.
    FE کل state را ارسال می‌کند؛ سرور آن را با DB sync می‌کند.

    Body:
    {
        "sections": [ ...  ]   ← ساختار کامل در SectionSyncService.sync()
    }

    Response:
    {
        "success": true,
        "order_id": int,
        "section_ids": [int, ...]
    }
    """

    def post(self, request, order_id):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'فرمت JSON نامعتبر'}, status=400)

        sections_payload = body.get('sections', [])
        if not isinstance(sections_payload, list):
            return JsonResponse({'success': False, 'message': 'sections باید آرایه باشد'}, status=400)

        # Order موجود است؟
        get_object_or_404(Order, id=order_id)

        try:
            with transaction.atomic():
                order = SectionSyncService.sync(order_id, sections_payload)

            section_ids = list(
                order.sections.order_by('order_index').values_list('id', flat=True)
            )
            logger.info('✅ Section sync completed — order=%s sections=%d', order_id, len(section_ids))

            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'section_ids': section_ids,
                'message': 'تغییرات با موفقیت ذخیره شد',
            })

        except Exception as e:
            logger.exception('❌ Section sync failed — order=%s', order_id)
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
