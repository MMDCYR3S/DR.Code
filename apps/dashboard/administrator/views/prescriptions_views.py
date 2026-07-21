import json

from django.views.generic import ListView, CreateView, UpdateView, View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db.models import Q, Prefetch

from .mixins import PrescriptionFormMixin
from ..forms.prescriptions_forms import *
from apps.prescriptions.models import Prescription, PrescriptionDrug
from apps.accounts.permissions import HasAdminAccessPermission, IsTokenJtiActive

# ===== بردکرامب پایه ===== #
BREADCRUMB_HOME = {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')}
BREADCRUMB_PRESCRIPTIONS = {'label': 'مدیریت نسخه‌ها', 'url': reverse_lazy('dashboard:prescriptions:prescription_list')}

# ================================================== #
# ============= PRESCRIPTION LIST VIEW ============= #
# ================================================== #
class PrescriptionListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
    """ لیست نسخه‌ها با جستجو، فیلتر و صفحه‌بندی """
    model = Prescription
    template_name = 'dashboard/prescriptions/list.html'
    context_object_name = 'prescriptions'
    paginate_by = 10

    def get_queryset(self):
        queryset = Prescription.objects.select_related('category').prefetch_related('aliases')

        form = PrescriptionFilterForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            category = form.cleaned_data.get('category')
            sort_by = form.cleaned_data.get('sort_by')

            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(detailed_description__icontains=search) |
                    Q(aliases__name__icontains=search)
                ).distinct()
            if category:
                queryset = queryset.filter(category=category)
            if sort_by:
                queryset = queryset.order_by(sort_by)
            else:
                queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ===== بردکرامب ===== #
        context['breadcrumb'] = [BREADCRUMB_HOME, {'label': 'مدیریت نسخه‌ها', 'url': ''}]

        # ===== جستجو و فیلترهای جاری ===== #
        context['search'] = self.request.GET.get('search', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['sort_by'] = self.request.GET.get('sort_by', '')

        # ===== آمار کارت‌ها ===== #
        total = Prescription.objects.count()
        premium = Prescription.objects.filter(access_level='PREMIUM').count()
        free = Prescription.objects.filter(access_level='FREE').count()

        context['stats'] = {
            'total': total,
            'premium': premium,
            'free': free,
        }

        # ===== فرم فیلتر ===== #
        context['filter_form'] = PrescriptionFilterForm(self.request.GET)

        # ===== داده‌های اضافی برای نمایش رنگ ===== #
        prescriptions_with_color = []
        for prescription in context['prescriptions']:
            prescriptions_with_color.append({
                'object': prescription,
                'category_color': prescription.category.color_code if prescription.category else 'bg-slate-500',
                'category_title': prescription.category.title if prescription.category else 'بدون دسته‌بندی'
            })
        context['prescriptions_data'] = prescriptions_with_color

        return context

# ================================================== #
# ============= PRESCRIPTION DETAIL VIEW =========== #
# ================================================== #
class PrescriptionDetailView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, DetailView):
    """ نمایش جزییات کامل یک نسخه با تمام اطلاعات مرتبط """
    model = Prescription
    template_name = 'dashboard/prescriptions/detail.html'
    context_object_name = 'prescription'

    def get_queryset(self):
        return Prescription.objects.select_related('category').prefetch_related(
            'aliases',
            'videos',
            Prefetch('images', queryset=PrescriptionImage.objects.order_by('created_at')),
            Prefetch('prescriptiondrug_set', 
                     queryset=PrescriptionDrug.objects.select_related('drug').order_by('group_number', 'order'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ===== بردکرامب ===== #
        context['breadcrumb'] = [
            BREADCRUMB_HOME,
            BREADCRUMB_PRESCRIPTIONS,
            {'label': self.object.title, 'url': ''}
        ]

        # ===== گروه‌بندی داروها ===== #
        drugs = self.object.prescriptiondrug_set.all()
        grouped_drugs = {}
        for drug in drugs:
            group_key = drug.group_number or 'no_group'
            if group_key not in grouped_drugs:
                grouped_drugs[group_key] = []
            grouped_drugs[group_key].append(drug)
        context['grouped_drugs'] = grouped_drugs

        # ===== رنگ دسته‌بندی ===== #
        context['category_color'] = self.object.category.color_code if self.object.category else 'bg-slate-500'

        return context

# ================================================== #
# ============= PRESCRIPTION DELETE VIEW =========== #
# ================================================== #
class PrescriptionDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ حذف نسخه (با ریدایرکت و پیام موفقیت) """
    def post(self, request, pk):
        prescription = get_object_or_404(Prescription, pk=pk)
        title = prescription.title
        prescription.delete()
        messages.success(request, f'نسخه "{title}" با موفقیت حذف شد.')
        return redirect('dashboard:prescriptions:prescription_list')

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
        
        context['breadcrumb'] = [
            {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')},
            {'label': 'مدیریت نسخه‌ها', 'url': reverse_lazy('dashboard:prescriptions:prescription_list')},
            {'label': 'افزودن نسخه جدید' if not self.object else f'ویرایش نسخه: {self.object.title}', 'url': ''}
        ]

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
        
        context['breadcrumb'] = [
            {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')},
            {'label': 'مدیریت نسخه‌ها', 'url': reverse_lazy('dashboard:prescriptions:prescription_list')},
            {'label': 'افزودن نسخه جدید' if not self.object else f'ویرایش نسخه: {self.object.title}', 'url': ''}
        ]

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
