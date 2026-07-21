from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, View
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
import jdatetime

from apps.order.models import DiscountCode
from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission

BREADCRUMB_HOME = {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')}
BREADCRUMB_DISCOUNTS = {'label': 'مدیریت کدهای تخفیف', 'url': reverse_lazy('dashboard:orders:discount_list')}


class DiscountListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
    model = DiscountCode
    template_name = 'dashboard/discounts/list.html'
    context_object_name = 'discounts'
    paginate_by = 20

    def get_queryset(self):
        queryset = DiscountCode.objects.order_by('-id')
        search = self.request.GET.get('search', '').strip()
        status = self.request.GET.get('status', 'all')

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(code__icontains=search)
            )
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = [BREADCRUMB_HOME, {'label': 'مدیریت کدهای تخفیف', 'url': ''}]
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', 'all')
        context['stats'] = {
            'total': DiscountCode.objects.count(),
            'active': DiscountCode.objects.filter(is_active=True).count(),
            'inactive': DiscountCode.objects.filter(is_active=False).count(),
        }

        for discount in context['discounts']:
            if discount.start_at:
                discount.shamsi_start_at = jdatetime.datetime.fromgregorian(
                    datetime=discount.start_at.replace(tzinfo=None)
                ).strftime('%Y/%m/%d - %H:%M')
            else:
                discount.shamsi_start_at = 'نامحدود'

            if discount.end_at:
                discount.shamsi_end_at = jdatetime.datetime.fromgregorian(
                    datetime=discount.end_at.replace(tzinfo=None)
                ).strftime('%Y/%m/%d - %H:%M')
            else:
                discount.shamsi_end_at = 'نامحدود'

            discount.usage_percent = (discount.usage_count / discount.max_usage) * 100 if discount.max_usage > 0 else 0

        return context


class DiscountCreateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def post(self, request):
        title = request.POST.get('title', '').strip()
        code = request.POST.get('code', '').strip().upper()
        discount_percent = request.POST.get('discount_percent', '')
        start_at_str = request.POST.get('start_at', '')
        end_at_str = request.POST.get('end_at', '')
        max_usage = request.POST.get('max_usage', '')
        is_active = request.POST.get('is_active') == 'on'

        # Validation
        errors = []
        if not discount_percent or not (1 <= int(discount_percent) <= 100):
            errors.append('درصد تخفیف باید بین 1 تا 100 باشد.')
        if not max_usage or int(max_usage) < 1:
            errors.append('حداکثر تعداد استفاده باید بیشتر از 0 باشد.')
        if start_at_str:
            try:
                start_at = timezone.datetime.fromisoformat(start_at_str)
            except ValueError:
                errors.append('فرمت تاریخ شروع نامعتبر است.')
        else:
            start_at = None
        if end_at_str:
            try:
                end_at = timezone.datetime.fromisoformat(end_at_str)
            except ValueError:
                errors.append('فرمت تاریخ پایان نامعتبر است.')
        else:
            end_at = None
        if start_at and end_at and start_at >= end_at:
            errors.append('تاریخ شروع باید قبل از تاریخ پایان باشد.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('dashboard:orders:discount_list')

        discount = DiscountCode(
            title=title,
            code=code,
            discount_percent=int(discount_percent),
            start_at=start_at,
            end_at=end_at,
            max_usage=int(max_usage),
            is_active=is_active
        )
        discount.save()
        messages.success(request, f'کد تخفیف «{discount.code}» با موفقیت ایجاد شد.')
        return redirect('dashboard:orders:discount_list')


class DiscountUpdateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def post(self, request, pk):
        discount = get_object_or_404(DiscountCode, pk=pk)
        title = request.POST.get('title', '').strip()
        code = request.POST.get('code', '').strip().upper()
        discount_percent = request.POST.get('discount_percent', '')
        start_at_str = request.POST.get('start_at', '')
        end_at_str = request.POST.get('end_at', '')
        max_usage = request.POST.get('max_usage', '')
        is_active = request.POST.get('is_active') == 'on'

        errors = []
        if not discount_percent or not (1 <= int(discount_percent) <= 100):
            errors.append('درصد تخفیف باید بین 1 تا 100 باشد.')
        if not max_usage or int(max_usage) < discount.usage_count:
            errors.append(f'حداکثر استفاده نمی‌تواند کمتر از تعداد استفاده فعلی ({discount.usage_count}) باشد.')
        if start_at_str:
            try:
                start_at = timezone.datetime.fromisoformat(start_at_str)
            except ValueError:
                errors.append('فرمت تاریخ شروع نامعتبر است.')
        else:
            start_at = None
        if end_at_str:
            try:
                end_at = timezone.datetime.fromisoformat(end_at_str)
            except ValueError:
                errors.append('فرمت تاریخ پایان نامعتبر است.')
        else:
            end_at = None
        if start_at and end_at and start_at >= end_at:
            errors.append('تاریخ شروع باید قبل از تاریخ پایان باشد.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('dashboard:orders:discount_list')

        discount.title = title
        if code and code != discount.code:
            if DiscountCode.objects.filter(code=code).exclude(pk=discount.pk).exists():
                messages.error(request, 'این کد تخفیف قبلاً استفاده شده است.')
                return redirect('dashboard:orders:discount_list')
            discount.code = code
        discount.discount_percent = int(discount_percent)
        discount.start_at = start_at
        discount.end_at = end_at
        discount.max_usage = int(max_usage)
        discount.is_active = is_active
        discount.save()
        messages.success(request, f'کد تخفیف «{discount.code}» با موفقیت ویرایش شد.')
        return redirect('dashboard:orders:discount_list')


class DiscountDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def post(self, request, pk):
        discount = get_object_or_404(DiscountCode, pk=pk)
        if discount.usage_count > 0:
            messages.error(request, 'این کد تخفیف قبلاً استفاده شده و قابل حذف نیست.')
        else:
            code = discount.code
            discount.delete()
            messages.success(request, f'کد تخفیف «{code}» با موفقیت حذف شد.')
        return redirect('dashboard:orders:discount_list')
