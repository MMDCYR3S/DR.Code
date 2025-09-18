from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

import json

from apps.prescriptions.models import PrescriptionCategory
from apps.accounts.permissions import HasAdminAccessPermission
from ..forms import CategoryForm, TAILWIND_COLOR_CHOICES


# ================================================== #
# ============= CATEGORY LIST VIEW ============= #
# ================================================== #
class CategoryListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    """
    نمایش لیست دسته‌بندی‌ها و مدیریت کامل عملیات CRUD از طریق AJAX.
    """
    model = PrescriptionCategory
    template_name = 'dashboard/categories/categories.html'
    context_object_name = 'categories'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CategoryForm()
        
        categories = self.get_queryset()
        color_map = dict(TAILWIND_COLOR_CHOICES)
        
        categories_data = [
            {
                'id': category.id,
                'title': category.title,
                'color_code': category.color_code,
                'color_name': color_map.get(category.color_code, '')
            }
            for category in categories
        ]
        context['categories_json'] = json.dumps(categories_data)
        
        return context
    
# ================================================== #
# ============= CATEGORY CREATE VIEW ============= #
# ================================================== #
class CategoryCreateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ ویو برای ایجاد دسته‌بندی جدید """
    
    def post(self, request, *args, **kwargs):
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            return JsonResponse({
                'success': True,
                'message': 'دسته‌بندی با موفقیت ایجاد شد.',
                'category': {
                    'id': category.id,
                    'title': category.title,
                    'color_code': category.color_code,
                    'color_name': dict(form.fields['color_code'].choices).get(category.color_code)
                }
            }, status=201)
        return JsonResponse({'success': False, 'message': 'اطلاعات وارد شده معتبر نیست.' ,'errors': form.errors}, status=400)
    
# ================================================== #
# ============= CATEGORY UPDATE VIEW ============= #
# ================================================== #
class CategoryUpdateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ ویو برای ویرایش یک دسته‌بندی """
    
    def post(self, request, pk, *args, **kwargs):
        category = get_object_or_404(PrescriptionCategory, pk=pk)
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            return JsonResponse({
                'success': True,
                'message': 'دسته‌بندی با موفقیت ویرایش شد.',
                'category': {
                    'id': category.id,
                    'title': category.title,
                    'color_code': category.color_code,
                    'color_name': dict(form.fields['color_code'].choices).get(category.color_code)
                }
            })
        return JsonResponse({'success': False, 'message': 'اطلاعات وارد شده معتبر نیست.', 'errors': form.errors}, status=400)
    
# ================================================== #
# ============= CATEGORY DELETE VIEW ============= #
# ================================================== #
class CategoryDeleteView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ ویو برای حذف یک دسته‌بندی """
    
    def post(self, request, pk, *args, **kwargs):
        category = get_object_or_404(PrescriptionCategory, pk=pk)
        try:
            category.delete()
            return JsonResponse({'success': True,'message': 'دسته‌بندی با موفقیت حذف شد.',})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'خطا در حذف دسته‌بندی.', 'error': str(e)}, status=500)