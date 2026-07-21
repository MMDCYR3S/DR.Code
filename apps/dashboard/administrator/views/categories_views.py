from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages

from apps.prescriptions.models import PrescriptionCategory
from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from ..forms import CategoryForm, TAILWIND_COLOR_CHOICES


# ===== لینک‌های پایه بردکرامب ===== #
BREADCRUMB_HOME = {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')}


# ================================================== #
# ================= لیست دسته‌بندی‌ها =============== #
# ================================================== #
class CategoryListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
    """ لیست دسته‌بندی‌ها با جستجوی سرورساید و صفحه‌بندی """

    model = PrescriptionCategory
    template_name = 'dashboard/categories/list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        queryset = PrescriptionCategory.objects.order_by('title')
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(title__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        color_map = dict(TAILWIND_COLOR_CHOICES)
        for category in context['categories']:
            category.color_name = color_map.get(category.color_code, '')
        context['form'] = CategoryForm()
        context['color_choices'] = [c for c in TAILWIND_COLOR_CHOICES if c[0]]
        context['breadcrumb'] = [BREADCRUMB_HOME, {'label': 'مدیریت دسته‌بندی‌ها', 'url': ''}]
        context['search'] = self.request.GET.get('search', '')
        context['stats'] = {
            'total': PrescriptionCategory.objects.count(),
        }
        return context


# ================================================== #
# ================= ایجاد دسته‌بندی ================= #
# ================================================== #
class CategoryCreateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ ایجاد دسته‌بندی جدید (POST + redirect) """

    def post(self, request, *args, **kwargs):
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'دسته‌بندی «{category.title}» با موفقیت ایجاد شد.')
        else:
            messages.error(request, f'اطلاعات وارد شده معتبر نیست: {form.errors.as_text()}')
        return redirect('dashboard:categories:category_list')


# ================================================== #
# ================ ویرایش دسته‌بندی ================ #
# ================================================== #
class CategoryUpdateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ ویرایش دسته‌بندی (POST + redirect) """

    def post(self, request, pk, *args, **kwargs):
        category = get_object_or_404(PrescriptionCategory, pk=pk)
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'دسته‌بندی «{category.title}» با موفقیت ویرایش شد.')
        else:
            messages.error(request, f'اطلاعات وارد شده معتبر نیست: {form.errors.as_text()}')
        return redirect('dashboard:categories:category_list')


# ================================================== #
# ================= حذف دسته‌بندی ================== #
# ================================================== #
class CategoryDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ حذف دسته‌بندی (POST + redirect) """

    def post(self, request, pk, *args, **kwargs):
        category = get_object_or_404(PrescriptionCategory, pk=pk)
        title = category.title
        category.delete()
        messages.success(request, f'دسته‌بندی «{title}» با موفقیت حذف شد.')
        return redirect('dashboard:categories:category_list')
