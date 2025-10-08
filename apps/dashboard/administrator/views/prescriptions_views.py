import json

from django.views.generic import ListView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q

from .mixins import PrescriptionFormMixin
from ..forms.prescriptions_forms import *
from apps.prescriptions.models import Prescription, PrescriptionDrug
from apps.accounts.permissions import HasAdminAccessPermission, IsTokenJtiActive

# ================================================== #
# ============= PRESCRIPTION LIST VIEW ============= #
# ================================================== #
class PrescriptionListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
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
            
            # Apply search filter
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(detailed_description__icontains=search) |
                    Q(aliases__name__icontains=search)
                ).distinct()
            
            # Apply category filter
            if category:
                queryset = queryset.filter(category=category)
            
            # Apply sorting
            if sort_by:
                queryset = queryset.order_by(sort_by)
            else:
                queryset = queryset.order_by('-created_at')  # Default sorting
        else:
            queryset = queryset.order_by('-created_at')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        prescriptions_with_color = []
        for prescription in context['prescriptions']:
            prescriptions_with_color.append({
                'object': prescription,
                'category_color': prescription.category.color_code if prescription.category else 'bg-slate-500',
                'category_title': prescription.category.title if prescription.category else 'بدون دسته‌بندی'
            })
        context['filter_form'] = PrescriptionFilterForm(self.request.GET)
        context['prescriptions_data'] = prescriptions_with_color
        return context

# ================================================== #
# ============= PRESCRIPTION DETAIL VIEW ============= #
# ================================================== #
class PrescriptionDetailView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def get(self, request, pk):
        try:
            prescription = get_object_or_404(Prescription, pk=pk)
            
            drugs = []
            
            for prescription_drug in prescription.prescriptiondrug_set.select_related('drug').order_by('group_number', 'order'):  # ✅ مرتب‌سازی بر اساس گروه
                drug_data = {
                    'id': prescription_drug.id,
                    'drug_id': prescription_drug.drug.id,
                    'title': prescription_drug.drug.title,
                    'code': prescription_drug.drug.code or '',
                    'dosage': prescription_drug.dosage or '',
                    'amount': prescription_drug.amount or 1,
                    'instructions': prescription_drug.instructions or '',
                    'order': prescription_drug.order or 0,
                    'is_combination': prescription_drug.is_combination,
                    'is_substitute': prescription_drug.is_substitute,
                    'group_number': prescription_drug.group_number
                }
                drugs.append(drug_data)
            
            data = {
                'id': prescription.id,
                'title': prescription.title,
                'category': prescription.category.title if prescription.category else 'بدون دسته‌بندی',
                'category_color': prescription.category.color_code if prescription.category else 'bg-slate-500',
                'access_level': prescription.access_level,
                'detailed_description': prescription.detailed_description or '',
                'drugs': drugs,
                'aliases': list(prescription.aliases.values('id', 'name', 'is_primary')),
                'videos': list(prescription.videos.values('id', 'video_url', 'title', 'description')),
                'images': [
                    {
                        'id': img.id,
                        'image': img.image.url if img.image else '',
                        'caption': img.caption or ''
                    } for img in prescription.images.all()
                ]
            }
            
            return JsonResponse({'success': True, 'data': data})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'خطا در بارگیری اطلاعات: {str(e)}'})

# ====================================================== #
# ============= PRESCRIPTION CREATE VIEW ============= #
# ====================================================== #
class PrescriptionCreateView(LoginRequiredMixin, CreateView):
    model = Prescription
    form_class = PrescriptionForm
    template_name = 'dashboard/prescriptions/prescription_form.html'
    success_url = reverse_lazy('dashboard:prescriptions:prescription_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['alias_formset'] = AliasFormSet(self.request.POST, prefix='aliases')
            context['video_formset'] = VideoFormSet(self.request.POST, prefix='videos')
            context['image_formset'] = ImageFormSet(self.request.POST, self.request.FILES, prefix='images')
        else:
            context['alias_formset'] = AliasFormSet(prefix='aliases')
            context['video_formset'] = VideoFormSet(prefix='videos')
            context['image_formset'] = ImageFormSet(prefix='images')
        
        # تمام داروها برای JavaScript
        context['all_drugs_json'] = json.dumps(
            list(Drug.objects.values('id', 'title', 'code').order_by('title'))
        )
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        alias_formset = context['alias_formset']
        video_formset = context['video_formset']
        image_formset = context['image_formset']
        
        # ست کردن کاربر
        form.instance.user = self.request.user
        
        if (form.is_valid() and alias_formset.is_valid() and 
            video_formset.is_valid() and image_formset.is_valid()):
            
            # ذخیره نسخه
            self.object = form.save()
            
            # پردازش داروها از POST data
            self.save_prescription_drugs()
            
            # ذخیره سایر formset ها
            alias_formset.instance = self.object
            alias_formset.save()
            
            video_formset.instance = self.object
            video_formset.save()
            
            image_formset.instance = self.object
            image_formset.save()
            
            messages.success(self.request, 'نسخه با موفقیت ایجاد شد.')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def save_prescription_drugs(self):
        """ذخیره داروهای نسخه از داده‌های JavaScript"""
        drugs_data = json.loads(self.request.POST.get('drugs_data', '[]'))
        
        for drug_data in drugs_data:
            PrescriptionDrug.objects.create(
                prescription=self.object,
                drug_id=drug_data['drug_id'],
                dosage=drug_data['dosage'],
                amount=drug_data['amount'],
                instructions=drug_data['instructions'],
                is_combination=drug_data['is_combination'],
                is_substitute=drug_data.get('is_substitute', False),
                order=drug_data['order'],
                group_number=drug_data.get('group_number')
            )

# ================================================== #
# ============= PRESCRIPTION UPDATE VIEW ============= #
# ================================================== #
class PrescriptionUpdateView(LoginRequiredMixin, UpdateView):
    model = Prescription
    form_class = PrescriptionForm
    template_name = 'dashboard/prescriptions/prescription_form.html'
    success_url = reverse_lazy('dashboard:prescriptions:prescription_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['alias_formset'] = AliasFormSet(self.request.POST, instance=self.object, prefix='aliases')
            context['video_formset'] = VideoFormSet(self.request.POST, instance=self.object, prefix='videos')
            context['image_formset'] = ImageFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='images')
        else:
            context['alias_formset'] = AliasFormSet(instance=self.object, prefix='aliases')
            context['video_formset'] = VideoFormSet(instance=self.object, prefix='videos')
            context['image_formset'] = ImageFormSet(instance=self.object, prefix='images')
        
        # تمام داروها برای JavaScript
        context['all_drugs_json'] = json.dumps(
            list(Drug.objects.values('id', 'title', 'code').order_by('title'))
        )
        
        # داروهای موجود
        existing_drugs = []
        for prescription_drug in self.object.prescriptiondrug_set.all():
            existing_drugs.append({
                'id': prescription_drug.id,
                'drug_id': prescription_drug.drug.id,
                'drug_title': prescription_drug.drug.title,
                'drug_code': prescription_drug.drug.code,
                'dosage': prescription_drug.dosage,
                'amount': prescription_drug.amount,
                'instructions': prescription_drug.instructions,
                'is_combination': prescription_drug.is_combination,
                'is_substitute': prescription_drug.is_substitute,
                'order': prescription_drug.order,
                'group_number': prescription_drug.group_number
            })
        
        context['existing_drugs_json'] = json.dumps(existing_drugs)
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        alias_formset = context['alias_formset']
        video_formset = context['video_formset']
        image_formset = context['image_formset']
        
        if (form.is_valid() and alias_formset.is_valid() and 
            video_formset.is_valid() and image_formset.is_valid()):
            
            # ذخیره تغییرات
            self.object = form.save()
            
            # پردازش داروها
            self.update_prescription_drugs()
            
            # ذخیره سایر formset ها
            alias_formset.save()
            video_formset.save()
            image_formset.save()
            
            messages.success(self.request, 'نسخه با موفقیت ویرایش شد.')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def update_prescription_drugs(self):
        """بروزرسانی داروهای نسخه"""
        # حذف داروهای قدیمی
        self.object.prescriptiondrug_set.all().delete()
        
        # اضافه کردن داروهای جدید
        drugs_data = json.loads(self.request.POST.get('drugs_data', '[]'))
        
        for drug_data in drugs_data:
            PrescriptionDrug.objects.create(
                prescription=self.object,
                drug_id=drug_data['drug_id'],
                dosage=drug_data['dosage'],
                amount=drug_data['amount'],
                instructions=drug_data['instructions'],
                is_combination=drug_data['is_combination'],
                is_substitute=drug_data.get('is_substitute', False),
                order=drug_data['order'],
                group_number=drug_data.get('group_number')
            )

# ================================================== #
# ============= PRESCRIPTION DELETE VIEW ============= #
# ================================================== #
class PrescriptionDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
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
