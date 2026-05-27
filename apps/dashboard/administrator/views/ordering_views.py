import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db import transaction
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q  

from apps.prescriptions.models import Drug
from apps.ordering.models import Order, Condition
from ..forms import (
    OrderForm, 
    OrderSectionFormSet, 
    SectionItemFormSet, 
    DrugSectionItemFormSet
)

logger = logging.getLogger(__name__)

# ==================================================== #
# ==================== Order View ==================== #
# ==================================================== #
class OrderManageView(View):
    template_name = 'dashboard/ordering/order_form.html'
    success_url = reverse_lazy('dashboard:ordering:order_create')

    def get_object(self, pk):
        if pk:
            return get_object_or_404(Order, pk=pk)
        return None

    def get(self, request, pk=None):
        order = self.get_object(pk)
        
        form = OrderForm(instance=order)
        section_formset = OrderSectionFormSet(instance=order)

        nested_sections = []
        for i, section_form in enumerate(section_formset):
            if not section_form.instance.pk:
                continue
            item_fs = SectionItemFormSet(instance=section_form.instance, prefix=f"{section_form.prefix}-items")
            drug_fs = DrugSectionItemFormSet(instance=section_form.instance, prefix=f"{section_form.prefix}-drugs")

            # ساخت map از instance.pk به prefix فرم
            item_prefix_map = {f.instance.pk: f.prefix for f in item_fs if f.instance.pk}
            drug_prefix_map = {f.instance.pk: f.prefix for f in drug_fs if f.instance.pk}

            # جمع‌آوری شرط‌ها
            seen_conditions = {}
            for item_form in item_fs:
                if not item_form.instance.pk:
                    continue
                for cond in item_form.instance.conditions.all():
                    if cond.pk not in seen_conditions:
                        seen_conditions[cond.pk] = {'text': cond.text, 'items': []}
                    seen_conditions[cond.pk]['items'].append(item_prefix_map[item_form.instance.pk])

            for drug_form in drug_fs:
                if not drug_form.instance.pk:
                    continue
                for cond in drug_form.instance.conditions.all():
                    if cond.pk not in seen_conditions:
                        seen_conditions[cond.pk] = {'text': cond.text, 'items': []}
                    seen_conditions[cond.pk]['items'].append(drug_prefix_map[drug_form.instance.pk])

            nested_sections.append({
                'section_form': section_form,
                'item_fs': item_fs,
                'drug_fs': drug_fs,
                'index': i,
                'conditions': list(seen_conditions.values()),  # <-- اضافه شد
            })


        empty_item_fs = SectionItemFormSet(prefix='sections-__section_prefix__-items')
        empty_drug_fs = DrugSectionItemFormSet(prefix='sections-__section_prefix__-drugs')

        context = {
            'form': form,
            'section_formset': section_formset,
            'nested_sections': nested_sections,
            'is_update': bool(order),
            'empty_section_form': section_formset.empty_form,
            'empty_item_fs': empty_item_fs,
            'empty_drug_fs': empty_drug_fs,
        }
        return render(request, self.template_name, context)
    
    @transaction.atomic
    def post(self, request, pk=None):
        order = self.get_object(pk)
        
        form = OrderForm(request.POST, instance=order)
        section_formset = OrderSectionFormSet(request.POST, instance=order)

        nested_sections = []
        all_nested_valid = True

        # === دیباگ: بررسی خطاهای فرم اصلی و فرم‌ست سکشن ===
        if not form.is_valid():
            logger.error(f"❌ Order Form Errors: {form.errors}")
            
        if not section_formset.is_valid():
            logger.error(f"❌ Section Formset Errors: {section_formset.errors}")
            logger.error(f"❌ Section Formset Non-Form Errors: {section_formset.non_form_errors()}")

        if form.is_valid() and section_formset.is_valid():
            saved_order = form.save(commit=False)
            section_formset.instance = saved_order

            for i, section_form in enumerate(section_formset):
                if not section_form.cleaned_data and not section_form.instance.pk:
                    continue
                item_fs = SectionItemFormSet(request.POST, instance=section_form.instance, prefix=f"{section_form.prefix}-items")
                drug_fs = DrugSectionItemFormSet(request.POST, instance=section_form.instance, prefix=f"{section_form.prefix}-drugs")

                # === دیباگ: بررسی خطاهای فرم‌ست‌های داخلی ===
                if not item_fs.is_valid():
                    all_nested_valid = False
                    logger.error(f"❌ Item Formset Errors (Section {i}): {item_fs.errors}")
                    
                if not drug_fs.is_valid():
                    all_nested_valid = False
                    logger.error(f"❌ Drug Formset Errors (Section {i}): {drug_fs.errors}")

                nested_sections.append({
                    'section_form': section_form,
                    'item_fs': item_fs,
                    'drug_fs': drug_fs,
                    'index': i
                })

            if all_nested_valid:
                saved_order.save()
                form.save_m2m()
                section_formset.save()

                saved_items_map = {}

                for data in nested_sections:
                    if data['section_form'] in section_formset.deleted_forms:
                        continue

                    # ===== ذخیره آیتم‌ها ===== #
                    data['item_fs'].save()
                    data['drug_fs'].save()

                    # ===== ساخت مپ و پاک کردن شرط‌های قبلیِ آیتم‌های باقی‌مانده ===== #
                    for item_form in data['item_fs'].forms:
                        if item_form.instance.pk and item_form not in data['item_fs'].deleted_forms:
                            saved_items_map[item_form.prefix] = item_form.instance
                            item_form.instance.conditions.clear()

                    for drug_form in data['drug_fs'].forms:
                        if drug_form.instance.pk and drug_form not in data['drug_fs'].deleted_forms:
                            saved_items_map[drug_form.prefix] = drug_form.instance
                            drug_form.instance.conditions.clear()

                    # ===== پردازش شرط‌های ارسالی فرانت‌اند ===== #
                    index = data['index']
                    conditions_json = request.POST.get(f'section_conditions_{index}')
                    
                    if conditions_json:
                        try:
                            conditions_data = json.loads(conditions_json)
                            for cond_data in conditions_data:
                                cond_text = cond_data.get('text', '')
                                linked_prefixes = cond_data.get('items', [])
                                
                                if cond_text and linked_prefixes:
                                    # ===== پیدا کردن یا ساخت شرط جدید ===== #
                                    condition_obj, _ = Condition.objects.get_or_create(text=cond_text)
                                    
                                    # ===== اتصال شرط به آیتم‌ها ===== #
                                    for prefix in linked_prefixes:
                                        if prefix in saved_items_map:
                                            saved_items_map[prefix].conditions.add(condition_obj)
                        except json.JSONDecodeError:
                            pass

                return redirect(self.success_url)
            else:
                logger.error("❌ all_nested_valid is FALSE!")
        else:
            logger.error("❌ Main form or Section formset is invalid!")
        
        context = {
            'form': form,
            'section_formset': section_formset,
            'nested_sections': nested_sections,
            'is_update': bool(order),
            'empty_section_form': section_formset.empty_form,
            'empty_item_fs': SectionItemFormSet(prefix='sections-__section_prefix__-items'),
            'empty_drug_fs': DrugSectionItemFormSet(prefix='sections-__section_prefix__-drugs'),
        }
        return render(request, self.template_name, context)

# ===================================================== #
# ==================== Drug Search ==================== #
# ===================================================== #
class DrugSearchAjaxView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()

        if len(query) < 2:
            return JsonResponse({'results': []})
        
        # جستجو در نام دارو "یا" کد دارو
        drugs = Drug.objects.filter(
            Q(title__icontains=query) | Q(code__icontains=query)
        )[:20]
        
        results = [
            {
                'id': drug.id, 
                'text': f"{drug.title} (کد: {drug.code})" if drug.code else drug.title, 
                'code': drug.code
            } 
            for drug in drugs
        ]
        
        return JsonResponse({'results': results})
