from django.views.generic import ListView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q

import json

from apps.prescriptions.models import Prescription
from ..forms import PrescriptionFilterForm
from .mixins import PrescriptionFormMixin
from apps.accounts.permissions import HasAdminAccessPermission

# ================================================== #
# ============= PRESCRIPTION LIST VIEW ============= #
# ================================================== #
class PrescriptionListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    """ نمایش لیست نسخه ها """
    model = Prescription
    template_name = 'dashboard/prescriptions/prescriptions.html'
    context_object_name = 'prescriptions'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Prescription.objects.select_related('category').prefetch_related('aliases').all()
        form = PrescriptionFilterForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            category = form.cleaned_data.get('category')
            sort_by = form.cleaned_data.get('sort_by')

            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) | Q(aliases__name__icontains=search)
                ).distinct()
            if category:
                queryset = queryset.filter(category=category)
            if sort_by:
                queryset = queryset.order_by(sort_by)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = PrescriptionFilterForm(self.request.GET)
        return context

# ================================================== #
# ============= PRESCRIPTION DETAIL VIEW ============= #
# ================================================== #
class PrescriptionDetailView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """نمایش جزئیات نسخه به صورت JSON برای مودال"""
    
    def get(self, request, pk):
        try:
            prescription = get_object_or_404(Prescription, pk=pk)
            
            # جمع‌آوری اطلاعات
            data = {
                'id': prescription.id,
                'title': prescription.title,
                'category': prescription.category.title if prescription.category else None,
                'access_level': prescription.access_level,
                'detailed_description': prescription.detailed_description,
                'drugs': list(prescription.drugs.values(
                    'id', 'title', 'code', 'dosage', 'amount', 'instructions', 
                    'is_combination', 'combination_group', 'order'
                ).order_by('order')),
                'aliases': list(prescription.aliases.values('id', 'name', 'is_primary')),
                'videos': list(prescription.videos.values('id', 'video_url', 'title', 'description')),
                'images': [
                    {
                        'id': img.id,
                        'image': img.image.url if img.image else '',
                        'caption': img.caption
                    } for img in prescription.images.all()
                ]
            }
            
            return JsonResponse({'success': True, 'data': data})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

# ================================================== #
# ============= PRESCRIPTION CREATE VIEW ============= #
# ================================================== #
class PrescriptionCreateView(LoginRequiredMixin, HasAdminAccessPermission, PrescriptionFormMixin, CreateView):
    """ ایجاد نسخه به وسیله فرم شخصی سازی شده و همچنین استفاده از Mixin """
    def get_object(self, queryset=None):
        return None

# ================================================== #
# ============= PRESCRIPTION UPDATE VIEW ============= #
# ================================================== #
class PrescriptionUpdateView(LoginRequiredMixin, HasAdminAccessPermission, PrescriptionFormMixin, UpdateView):
    """ ویرایش نسخه به وسیله داروهای آن به واسطه Mixin سفارشی """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        prescription = self.get_object()
        drugs_data = list(prescription.drugs.values('id', 'title', 'code', 'dosage', 'amount', 'instructions', 'is_combination', 'combination_group', 'order'))
        
        context['object_data_json'] = json.dumps({
            'title': prescription.title,
            'detailed_description': prescription.detailed_description or "",
            'category': prescription.category.id if prescription.category else "",
            'access_level': prescription.access_level,
            'is_active': prescription.is_active,
            'slug': prescription.slug,
            'drugs': drugs_data
        })
        return context

# ================================================== #
# ============= PRESCRIPTION DELETE VIEW ============= #
# ================================================== #
class PrescriptionDeleteView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ حذف یک نسخه """
    def post(self, request, pk, *args, **kwargs):
        """ بررسی اینکه آیا نسخه وجود دارد یا خیر """
        prescription = get_object_or_404(Prescription, pk=pk)
        prescription_title = prescription.title
        try:
            prescription.delete()
            return JsonResponse({'success': True, 'message': f'نسخه "{prescription_title}" با موفقیت حذف شد.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'خطا در حذف نسخه.', 'error': str(e)}, status=500)
