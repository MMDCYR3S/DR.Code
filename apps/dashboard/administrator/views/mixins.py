import json
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.db.models import Max

from apps.prescriptions.models import Prescription, PrescriptionDrug, Drug
from ..forms import (
    PrescriptionForm, 
    PrescriptionDrugFormSet, 
    AliasFormSet, 
    ImageFormSet, 
    VideoFormSet
)

# ======== Prescription Form Mixin ======== #
class PrescriptionFormMixin:
    model = Prescription
    form_class = PrescriptionForm
    template_name = 'dashboard/prescriptions/prescription-form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['drug_formset'] = PrescriptionDrugFormSet(
                self.request.POST, 
                instance=self.object,
                prefix='drugs'  # اضافه کردن prefix
            )
            context['alias_formset'] = AliasFormSet(
                self.request.POST, 
                instance=self.object,
                prefix='aliases'
            )
            context['image_formset'] = ImageFormSet(
                self.request.POST, 
                self.request.FILES, 
                instance=self.object,
                prefix='images'
            )
            context['video_formset'] = VideoFormSet(
                self.request.POST, 
                instance=self.object,
                prefix='videos'
            )
        else:
            # برای حالت GET - نمایش فرم خالی یا با داده‌های موجود
            if self.object and self.object.pk:
                # حالت ویرایش - نمایش داروهای موجود
                context['drug_formset'] = PrescriptionDrugFormSet(
                    instance=self.object,
                    prefix='drugs'
                )
            else:
                # حالت ایجاد - نمایش فرم خالی
                context['drug_formset'] = PrescriptionDrugFormSet(
                    prefix='drugs'
                )
                
            context['alias_formset'] = AliasFormSet(
                instance=self.object,
                prefix='aliases'
            )
            context['image_formset'] = ImageFormSet(
                instance=self.object,
                prefix='images'
            )
            context['video_formset'] = VideoFormSet(
                instance=self.object,
                prefix='videos'
            )
        
        # اضافه کردن لیست تمام داروها برای جاوااسکریپت
        context['all_drugs'] = list(
            Drug.objects.values('id', 'title', 'code').order_by('title')
        )
        
        return context

    def form_valid(self, form):
        # ذخیره فرم اصلی
        self.object = form.save(commit=False)
        
        # دریافت formset ها
        context = self.get_context_data()
        drug_formset = context['drug_formset']
        alias_formset = context['alias_formset']
        image_formset = context['image_formset']
        video_formset = context['video_formset']

        # بررسی اعتبار همه formset ها
        is_valid = all([
            drug_formset.is_valid(),
            alias_formset.is_valid(),
            image_formset.is_valid(),
            video_formset.is_valid()
        ])

        if is_valid:
            # ذخیره نسخه اصلی
            self.object.save()
            
            # حالا که نسخه ذخیره شد، formset ها را ذخیره کن
            drug_formset.instance = self.object
            drug_formset.save()
            
            alias_formset.instance = self.object
            alias_formset.save()
            
            image_formset.instance = self.object
            image_formset.save()
            
            video_formset.instance = self.object
            video_formset.save()
            
            # پردازش داروهای انتخاب شده از چک‌باکس‌ها (فقط برای حالت ایجاد)
            if not self.object.pk or self.request.GET.get('new_drugs'):
                self.process_new_drugs(form)
            
            # بررسی عمل انتشار
            if 'publish' in self.request.POST:
                self.object.is_active = True
                self.object.save()
                messages.success(self.request, 'نسخه با موفقیت منتشر شد!')
            else:
                messages.success(self.request, f'نسخه «{self.object.title}» با موفقیت ذخیره شد!')
                
            return HttpResponseRedirect(self.get_success_url())
        else:
            # نمایش خطاهای دقیق
            if not drug_formset.is_valid():
                messages.error(self.request, f'خطا در اطلاعات داروها: {drug_formset.errors}')
            if not alias_formset.is_valid():
                messages.error(self.request, f'خطا در نام‌های جایگزین: {alias_formset.errors}')
            if not image_formset.is_valid():
                messages.error(self.request, f'خطا در تصاویر: {image_formset.errors}')
            if not video_formset.is_valid():
                messages.error(self.request, f'خطا در ویدیوها: {video_formset.errors}')
            
            return self.form_invalid(form)

    def process_new_drugs(self, form):
        """
        فقط برای اضافه کردن داروهای جدید از چک‌باکس‌ها
        این متد فقط در حالت ایجاد یا زمانی که کاربر داروی جدید انتخاب کرده استفاده می‌شود
        """
        # داروهای موجود را دریافت کن
        existing_drug_ids = set(
            self.object.prescriptiondrug_set.values_list('drug_id', flat=True)
        )
        
        # محاسبه آخرین order
        last_order = self.object.prescriptiondrug_set.aggregate(
            max_order=Max('order')
        )['max_order'] or 0
        
        order = last_order + 1
        
        # اضافه کردن داروهای عادی جدید
        regular_drugs = form.cleaned_data.get('regular_drugs', [])
        for drug in regular_drugs:
            if drug.id not in existing_drug_ids:
                PrescriptionDrug.objects.create(
                    prescription=self.object,
                    drug=drug,
                    dosage="",
                    amount=1,
                    instructions="",
                    is_combination=False,
                    order=order
                )
                order += 1
        
        # اضافه کردن داروهای ترکیبی جدید
        combination_drugs = form.cleaned_data.get('combination_drugs', [])
        for drug in combination_drugs:
            if drug.id not in existing_drug_ids:
                PrescriptionDrug.objects.create(
                    prescription=self.object,
                    drug=drug,
                    dosage="",
                    amount=1,
                    instructions="",
                    is_combination=True,
                    order=order
                )
                order += 1

    def form_invalid(self, form):
        messages.error(self.request, 'لطفاً خطاهای موجود در فرم را بررسی کنید.')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('dashboard:prescriptions:prescription_list')