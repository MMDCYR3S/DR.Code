from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q

from apps.prescriptions.models import Drug
from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from ..forms import DrugForm


# ===== لینک‌های پایه بردکرامب ===== #
BREADCRUMB_HOME = {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')}
BREADCRUMB_DRUGS = {'label': 'مدیریت داروها', 'url': reverse_lazy('dashboard:drugs:drug_list')}


# ================================================== #
# ==================== لیست داروها ================= #
# ================================================== #
class DrugListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
    """ لیست داروها با جستجوی سرورساید، فیلتر نوع و صفحه‌بندی """

    model = Drug
    template_name = 'dashboard/drugs/list.html'
    context_object_name = 'drugs'
    paginate_by = 20

    def get_queryset(self):
        queryset = Drug.objects.order_by('-created_at')

        search = self.request.GET.get('search', '').strip()
        drug_type = self.request.GET.get('type', '').strip()

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(code__icontains=search)
            )
        if drug_type == 'order':
            queryset = queryset.filter(is_for_order=True)
        elif drug_type == 'prescription':
            queryset = queryset.filter(is_for_order=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = DrugForm()
        context['breadcrumb'] = [BREADCRUMB_HOME, {'label': 'مدیریت داروها', 'url': ''}]
        context['search'] = self.request.GET.get('search', '')
        context['drug_type'] = self.request.GET.get('type', '')
        context['stats'] = {
            'total': Drug.objects.count(),
            'order': Drug.objects.filter(is_for_order=True).count(),
            'prescription': Drug.objects.filter(is_for_order=False).count(),
        }
        return context


# ================================================== #
# ==================== ایجاد دارو ================== #
# ================================================== #
class DrugCreateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ ایجاد داروی جدید از طریق فرم (POST + redirect) """

    def post(self, request, *args, **kwargs):
        form = DrugForm(request.POST)
        if form.is_valid():
            drug = form.save()
            messages.success(request, f'داروی «{drug.title}» با موفقیت ایجاد شد.')
        else:
            messages.error(request, f'اطلاعات وارد شده معتبر نیست: {form.errors.as_text()}')
        return redirect('dashboard:drugs:drug_list')


# ================================================== #
# =================== ویرایش دارو ================== #
# ================================================== #
class DrugUpdateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ ویرایش دارو (POST + redirect) """

    def post(self, request, pk, *args, **kwargs):
        drug = get_object_or_404(Drug, pk=pk)
        form = DrugForm(request.POST, instance=drug)
        if form.is_valid():
            drug = form.save()
            messages.success(request, f'داروی «{drug.title}» با موفقیت ویرایش شد.')
        else:
            messages.error(request, f'اطلاعات وارد شده معتبر نیست: {form.errors.as_text()}')
        return redirect('dashboard:drugs:drug_list')


# ================================================== #
# ==================== حذف دارو =================== #
# ================================================== #
class DrugDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ حذف دارو (POST + redirect) """

    def post(self, request, pk, *args, **kwargs):
        drug = get_object_or_404(Drug, pk=pk)
        title = drug.title
        drug.delete()
        messages.success(request, f'داروی «{title}» با موفقیت حذف شد.')
        return redirect('dashboard:drugs:drug_list')
