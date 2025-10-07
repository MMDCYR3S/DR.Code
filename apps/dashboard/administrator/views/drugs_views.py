from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q

import json

from apps.prescriptions.models import Drug
from apps.accounts.permissions import HasAdminAccessPermission
from ..forms import DrugForm


# ================================================== #
# ============= DRUG LIST VIEW ============= #
# ================================================== #
class DrugListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    """
    نمایش لیست داروها و مدیریت کامل عملیات CRUD از طریق AJAX.
    """
    model = Drug
    template_name = 'dashboard/drugs/drugs.html'
    context_object_name = 'drugs'
    ordering = ['-created_at']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = DrugForm()
        
        drugs = self.get_queryset()
        
        drugs_data = [
            {
                'id': drug.id,
                'title': drug.title,
                'code': drug.code or '',
                'created_at': drug.shamsi_created_at,
                'updated_at': drug.shamsi_updated_at,
            }
            for drug in drugs
        ]
        context['drugs_json'] = json.dumps(drugs_data)
        
        return context


# ================================================== #
# ============= DRUG CREATE VIEW ============= #
# ================================================== #
class DrugCreateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ ویو برای ایجاد دارو جدید """
    
    def post(self, request, *args, **kwargs):
        form = DrugForm(request.POST)
        if form.is_valid():
            drug = form.save()
            return JsonResponse({
                'success': True,
                'message': 'دارو با موفقیت ایجاد شد.',
                'drug': {
                    'id': drug.id,
                    'title': drug.title,
                    'code': drug.code or '',
                    'created_at': drug.shamsi_created_at,
                    'updated_at': drug.shamsi_updated_at,
                }
            }, status=201)
        return JsonResponse({
            'success': False, 
            'message': 'اطلاعات وارد شده معتبر نیست.',
            'errors': form.errors
        }, status=400)


# ================================================== #
# ============= DRUG UPDATE VIEW ============= #
# ================================================== #
class DrugUpdateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ ویو برای ویرایش یک دارو """
    
    def post(self, request, pk, *args, **kwargs):
        drug = get_object_or_404(Drug, pk=pk)
        form = DrugForm(request.POST, instance=drug)
        if form.is_valid():
            drug = form.save()
            return JsonResponse({
                'success': True,
                'message': 'دارو با موفقیت ویرایش شد.',
                'drug': {
                    'id': drug.id,
                    'title': drug.title,
                    'code': drug.code or '',
                    'created_at': drug.shamsi_created_at,
                    'updated_at': drug.shamsi_updated_at,
                }
            })
        return JsonResponse({
            'success': False, 
            'message': 'اطلاعات وارد شده معتبر نیست.', 
            'errors': form.errors
        }, status=400)


# ================================================== #
# ============= DRUG DELETE VIEW ============= #
# ================================================== #
class DrugDeleteView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ ویو برای حذف یک دارو """
    
    def post(self, request, pk, *args, **kwargs):
        drug = get_object_or_404(Drug, pk=pk)
        try:
            drug_title = drug.title
            drug.delete()
            return JsonResponse({
                'success': True,
                'message': f'دارو «{drug_title}» با موفقیت حذف شد.',
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': 'خطا در حذف دارو.', 
                'error': str(e)
            }, status=500)


# ================================================== #
# ============= DRUG DETAIL VIEW ============= #
# ================================================== #
class DrugDetailView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ ویو برای نمایش جزئیات یک دارو """
    
    def get(self, request, pk, *args, **kwargs):
        try:
            drug = get_object_or_404(Drug, pk=pk)
            return JsonResponse({
                'success': True,
                'drug': {
                    'id': drug.id,
                    'title': drug.title,
                    'code': drug.code or '',
                    'created_at': drug.shamsi_created_at,
                    'updated_at': drug.shamsi_updated_at,
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': 'خطا در بارگیری اطلاعات دارو.',
                'error': str(e)
            }, status=500)

# ================================================== #
# ============= DRUG SEARCH VIEW ============= #
# ================================================== #
class DrugSearchView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ ویو برای جستجوی داروها بر اساس نام یا کد """
    
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('q', '').strip()
        
        if not search_query:
            drugs = Drug.objects.all().order_by('-created_at')
        else:
            drugs = Drug.objects.filter(
                Q(title__icontains=search_query) | 
                Q(code__icontains=search_query)
            ).order_by('-created_at')
        
        drugs_data = [
            {
                'id': drug.id,
                'title': drug.title,
                'code': drug.code or '',
                'created_at': drug.shamsi_created_at,
                'updated_at': drug.shamsi_updated_at,
            }
            for drug in drugs
        ]
        
        return JsonResponse({
            'success': True,
            'drugs': drugs_data,
            'count': len(drugs_data)
        })
