import json
import logging

from django.shortcuts import (
    render, redirect, get_object_or_404
)
from django.views import View
from django.views.generic import DetailView
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q, Max, Prefetch
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.prescriptions.models import Drug
from apps.ordering.models import (
    Order, Condition, OrderSection,
    SectionItem, DrugSectionItem,
    DynamicFieldGroup, DynamicFieldNode,
    EmergencyDisposition, EmergencyNode,
    OrderImage, OrderVideo,
    TailwindColor, ItemRelationshipGroup,
)
from ..forms import (
    # ===== Ordering ===== #
    OrderFilterForm,
    OrderForm, 
    OrderSectionFormSet, 
    SectionItemFormSet, 
    DrugSectionItemFormSet,
    OrderAliasFormSet,

    # ===== Dynamic ===== #
    DynamicFieldGroupForm,
    DynamicFieldChildNodeFormSet,
    DynamicFieldRootNodeForm,
    DynamicFieldChildNodeForm,

    # ===== Emergency ===== #
    EmergencyDispositionForm,
    EmergencyRootNodeForm,
    EmergencyChildNodeForm,
    ChildNodeFormSet,

    # ===== Media ===== #
    OrderImageFormSet,
    OrderVideoFormSet,
)

logger = logging.getLogger(__name__)

# ===================================================== #
# ==================== Order List ===================== #
# ===================================================== #
class OrderCopyView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, pk):
        original_order = get_object_or_404(Order, pk=pk)

        new_order = Order.objects.get(pk=pk)
        new_order.pk = None
        new_order.name = f"{new_order.name} (کپی)"
        new_order.save()

        for old_section in original_order.sections.all():
            old_section_id = old_section.pk
            
            new_section = OrderSection.objects.get(pk=old_section_id)
            new_section.pk = None
            new_section.order = new_order
            new_section.save()

            for item in SectionItem.objects.filter(section_id=old_section_id):
                old_conditions = list(item.conditions.all())
                item.pk = None
                item.section = new_section
                item.save()
                if old_conditions:
                    item.conditions.set(old_conditions)

            for drug_item in DrugSectionItem.objects.filter(section_id=old_section_id):
                old_conditions = list(drug_item.conditions.all())
                drug_item.pk = None
                drug_item.section = new_section
                drug_item.save()
                if old_conditions:
                    drug_item.conditions.set(old_conditions)

        for old_group in original_order.dynamic_field_groups.all():
            old_group_id = old_group.pk
            
            new_group = DynamicFieldGroup.objects.get(pk=old_group_id)
            new_group.pk = None
            new_group.order = new_order
            new_group.save()

            old_nodes = DynamicFieldNode.objects.filter(group_id=old_group_id)
            node_mapping = {}
            
            for old_node in old_nodes:
                new_node = DynamicFieldNode.objects.get(pk=old_node.pk)
                new_node.pk = None
                new_node.group = new_group
                new_node.parent = None
                new_node.save()
                node_mapping[old_node.pk] = new_node
                
            for old_node in old_nodes:
                if old_node.parent_id:
                    new_node = node_mapping[old_node.pk]
                    new_node.parent = node_mapping[old_node.parent_id]
                    new_node.save()

        if hasattr(original_order, 'emergency_disposition'):
            old_disp = original_order.emergency_disposition
            old_disp_id = old_disp.pk
            
            new_disp = EmergencyDisposition.objects.get(pk=old_disp_id)
            new_disp.pk = None
            new_disp.order = new_order
            new_disp.save()

            old_nodes = EmergencyNode.objects.filter(disposition_id=old_disp_id)
            node_mapping = {}
            
            for old_node in old_nodes:
                new_node = EmergencyNode.objects.get(pk=old_node.pk)
                new_node.pk = None
                new_node.disposition = new_disp
                new_node.parent = None
                new_node.save()
                node_mapping[old_node.pk] = new_node
                
            for old_node in old_nodes:
                if old_node.parent_id:
                    new_node = node_mapping[old_node.pk]
                    new_node.parent = node_mapping[old_node.parent_id]
                    new_node.save()

        messages.success(request, f'اوردر با موفقیت کپی شد. اکنون در حال ویرایش نسخه کپی هستید.')
        return redirect(reverse('dashboard:ordering:order_edit', kwargs={'pk': new_order.pk}))

# ===================================================== #
# ==================== Order List ===================== #
# ===================================================== #
class OrderListView(View):
    template_name = 'dashboard/ordering/orders.html'
    paginate_by = 15

    def get(self, request):
        from django.core.paginator import Paginator

        qs = Order.objects.all()

        filter_form = OrderFilterForm(request.GET or None)

        if filter_form.is_valid():
            search = filter_form.cleaned_data.get('search', '').strip()
            category = filter_form.cleaned_data.get('category')
            sort_by = filter_form.cleaned_data.get('sort_by') or '-created_at'

            if search:
                qs = qs.filter(Q(name__icontains=search))
            if category:
                qs = qs.filter(category=category)
            qs = qs.order_by(sort_by)
        else:
            qs = qs.order_by('-created_at')

        paginator = Paginator(qs, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        context = {
            'orders': page_obj,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
            'filter_form': filter_form,
        }
        return render(request, self.template_name, context)

# =========================================================== #
# ==================== Order Detail View ==================== #
# =========================================================== #
class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    نمایش جزئیات کامل یک اوردر شامل:
      - اطلاعات پایه (imp, condition, diet, action, position, notes)
      - بخش‌ها (Sections) با آیتم‌های متنی، داروها، شرط‌ها و روابط منطقی
      - اطلاعات پیش‌بالینی (DynamicFieldGroups → DynamicFieldNodes درختی)
      - تعیین تکلیف اورژانس (EmergencyDisposition + درخت گره‌ها)
      - تصاویر (OrderImage)
      - ویدیوها (OrderVideo)
    """
 
    model = Order
    template_name = "dashboard/ordering/order_detail.html"
    context_object_name = "order"
 
    def get_queryset(self):
        """
        queryset بهینه با prefetch_related برای تمام روابط مورد نیاز.
        از N+1 query جلوگیری می‌کند.
        """
 
        # ── Prefetch شرط‌های آیتم‌های متنی ──────────────────────────────
        item_conditions_prefetch = Prefetch(
            "conditions",
            queryset=Condition.objects.order_by("order_index"),
        )
 
        # ── Prefetch آیتم‌های متنی با شرط‌هایشان ──────────────────────
        items_prefetch = Prefetch(
            "items",
            queryset=SectionItem.objects.prefetch_related(
                item_conditions_prefetch,
            ).select_related("relationship_group").order_by("order_index"),
        )
 
        # ── Prefetch شرط‌های آیتم‌های دارویی ────────────────────────────
        drug_item_conditions_prefetch = Prefetch(
            "conditions",
            queryset=Condition.objects.order_by("order_index"),
        )
 
        # ── Prefetch آیتم‌های دارویی با شرط‌ها ──────────────────────────
        drug_items_prefetch = Prefetch(
            "drug_items",
            queryset=DrugSectionItem.objects.select_related(
                "drug", "relationship_group"
            ).prefetch_related(
                drug_item_conditions_prefetch,
            ).order_by("order_index"),
        )
 
        # ── Prefetch گروه‌های ارتباطی (OR/AND/THEN) ─────────────────────
        relationship_groups_prefetch = Prefetch(
            "relationship_groups",
            queryset=ItemRelationshipGroup.objects.order_by("order_index"),
        )
 
        # ── Prefetch بخش‌ها با همه زیرمجموعه‌ها ────────────────────────
        sections_prefetch = Prefetch(
            "sections",
            queryset=OrderSection.objects.prefetch_related(
                items_prefetch,
                drug_items_prefetch,
                relationship_groups_prefetch,
            ).order_by("order_index"),
        )
 
        # ── Prefetch گره‌های پیش‌بالینی (درختی، یک سطح فرزند) ──────────
        preclinical_children_prefetch = Prefetch(
            "children",
            queryset=DynamicFieldNode.objects.order_by("order_index"),
        )
        preclinical_root_nodes_prefetch = Prefetch(
            "nodes",
            queryset=DynamicFieldNode.objects.filter(parent=None).prefetch_related(
                preclinical_children_prefetch
            ).order_by("order_index"),
        )
        dynamic_groups_prefetch = Prefetch(
            "dynamic_field_groups",
            queryset=DynamicFieldGroup.objects.prefetch_related(
                preclinical_root_nodes_prefetch
            ).order_by("order_index"),
        )
 
        # ── Prefetch گره‌های تعیین تکلیف (یک سطح فرزند) ────────────────
        emergency_children_prefetch = Prefetch(
            "children",
            queryset=EmergencyNode.objects.order_by("order_index"),
        )
        emergency_nodes_prefetch = Prefetch(
            "nodes",
            queryset=EmergencyNode.objects.filter(parent=None).prefetch_related(
                emergency_children_prefetch
            ).order_by("order_index"),
        )
        disposition_prefetch = Prefetch(
            "emergency_disposition",
            queryset=EmergencyDisposition.objects.prefetch_related(
                emergency_nodes_prefetch
            ),
        )
 
        return (
            Order.objects.select_related("category")
            .prefetch_related(
                sections_prefetch,
                dynamic_groups_prefetch,
                disposition_prefetch,
                Prefetch(
                    "images",
                    queryset=OrderImage.objects.order_by("order_index"),
                ),
                Prefetch(
                    "videos",
                    queryset=OrderVideo.objects.order_by("order_index"),
                ),
            )
        )
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_detail"] = True
        return context
 
# ====================================================== #
# ==================== Order Delete ==================== #
# ====================================================== #
class OrderDeleteView(View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        order_name = order.name
        try:
            order.delete()
            return JsonResponse({'success': True, 'message': f'اوردر «{order_name}» با موفقیت حذف شد.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'خطا در حذف اوردر.', 'error': str(e)}, status=500)



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
        alias_formset = OrderAliasFormSet(instance=order) if order else None

        nested_sections = []
        for i, section_form in enumerate(section_formset):
            if not section_form.instance.pk:
                continue
            item_fs = SectionItemFormSet(instance=section_form.instance, prefix=f"{section_form.prefix}-items")
            drug_fs = DrugSectionItemFormSet(instance=section_form.instance, prefix=f"{section_form.prefix}-drugs")

            item_prefix_map = {f.instance.pk: f.prefix for f in item_fs if f.instance.pk}
            drug_prefix_map = {f.instance.pk: f.prefix for f in drug_fs if f.instance.pk}

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

            # آماده‌سازی دیتای گروه‌های ارتباطی
            relationship_groups_data = []
            groups = section_form.instance.relationship_groups.all().prefetch_related('text_items', 'drug_items')
            for group in groups:
                linked_item_prefixes = []
                for item in group.text_items.all():
                    if item.pk in item_prefix_map:
                        linked_item_prefixes.append(item_prefix_map[item.pk])
                for drug_item in group.drug_items.all():
                    if drug_item.pk in drug_prefix_map:
                        linked_item_prefixes.append(drug_prefix_map[drug_item.pk])
                
                relationship_groups_data.append({
                    'operator': group.operator,
                    'items': linked_item_prefixes,
                })

            nested_sections.append({
                'section_form': section_form,
                'item_fs': item_fs,
                'drug_fs': drug_fs,
                'index': i,
                'conditions': list(seen_conditions.values()),
                'relationship_groups': json.dumps(relationship_groups_data),
            })

        empty_item_fs = SectionItemFormSet(prefix='sections-__section_prefix__-items')
        empty_drug_fs = DrugSectionItemFormSet(prefix='sections-__section_prefix__-drugs')

        context = {
            'form': form,
            'order': order,
            'section_formset': section_formset,
            'nested_sections': nested_sections,
            'is_update': bool(order),
            'empty_section_form': section_formset.empty_form,
            'empty_item_fs': empty_item_fs,
            'empty_drug_fs': empty_drug_fs,
            'active_tab': 'order',
            'alias_formset': alias_formset,
        }
        return render(request, self.template_name, context)
    
    @transaction.atomic
    def post(self, request, pk=None):
        order = self.get_object(pk)
        
        form = OrderForm(request.POST, instance=order)
        section_formset = OrderSectionFormSet(request.POST, instance=order)
        alias_formset = OrderAliasFormSet(request.POST, instance=order) if order else None

        nested_sections = []
        all_nested_valid = True
        
        # ===== جمع‌آوری ارورهای ساختاریافته ===== #
        errors_detail = {
            'base': {},       # ارورهای فرم اصلی
            'aliases': {},    # ارورهای alias
            'sections': {}    # ارورهای سکشن‌ها و آیتم‌ها
        }

        if not form.is_valid():
            errors_detail['base'] = form.errors
            logger.error(f"❌ Order Form Errors: {form.errors}")

        if not section_formset.is_valid():
            logger.error(f"❌ Section Formset Errors: {section_formset.errors}")

        alias_valid = True
        if alias_formset:
            alias_valid = alias_formset.is_valid()
            if not alias_valid:
                errors_detail['aliases'] = alias_formset.errors
                logger.error(f"❌ Alias Formset Errors: {alias_formset.errors}")

        if form.is_valid() and section_formset.is_valid() and alias_valid:
            saved_order = form.save(commit=False)
            section_formset.instance = saved_order
            if alias_formset:
                alias_formset.instance = saved_order

            for i, section_form in enumerate(section_formset):
                if not section_form.cleaned_data and not section_form.instance.pk:
                    continue
                item_fs = SectionItemFormSet(request.POST, instance=section_form.instance, prefix=f"{section_form.prefix}-items")
                drug_fs = DrugSectionItemFormSet(request.POST, instance=section_form.instance, prefix=f"{section_form.prefix}-drugs")

                if not item_fs.is_valid():
                    all_nested_valid = False
                    errors_detail['sections'][i] = {
                        'section_errors': section_form.errors,
                        'item_errors': item_fs.errors,
                        'drug_errors': drug_fs.errors
                    }
                    logger.error(f"❌ Item Formset Errors (Section {i}): {item_fs.errors}")
                if not drug_fs.is_valid():
                    all_nested_valid = False
                    if i not in errors_detail['sections']:
                        errors_detail['sections'][i] = {}
                    errors_detail['sections'][i]['drug_errors'] = drug_fs.errors
                    logger.error(f"❌ Drug Formset Errors (Section {i}): {drug_fs.errors}")

                nested_sections.append({
                    'section_form': section_form,
                    'item_fs': item_fs,
                    'drug_fs': drug_fs,
                    'index': i,
                    '_has_error': i in errors_detail.get('sections', {})
                })

            if all_nested_valid:
                saved_order.save()
                form.save_m2m()
                section_formset.save()
                if alias_formset:
                    alias_formset.save()

                # پاک کردن گروه‌های ارتباطی قدیمی
                old_groups = ItemRelationshipGroup.objects.filter(section__order=saved_order)
                for group in old_groups:
                    group.text_items.clear()
                    group.drug_items.clear()
                old_groups.delete()

                section_map = {form.prefix: form.instance for form in section_formset}
                saved_items_map = {}

                for data in nested_sections:
                    if data['section_form'].prefix not in section_map:
                        continue

                    section_instance = section_map.get(data['section_form'].prefix)
                    if not section_instance or not section_instance.pk:
                        continue
                    
                    data['item_fs'].instance = section_instance
                    data['drug_fs'].instance = section_instance

                    data['item_fs'].save()
                    data['drug_fs'].save()

                    for item_form in data['item_fs'].forms:
                        if item_form.instance.pk and item_form not in data['item_fs'].deleted_forms:
                            saved_items_map[item_form.prefix] = item_form.instance
                            item_form.instance.conditions.clear()

                    for drug_form in data['drug_fs'].forms:
                        if drug_form.instance.pk and drug_form not in data['drug_fs'].deleted_forms:
                            saved_items_map[drug_form.prefix] = drug_form.instance
                            drug_form.instance.conditions.clear()

                    index = data['index']

                    # پردازش روابط
                    relationships_json = request.POST.get(f'section_relationships_{index}')
                    if relationships_json:
                        try:
                            relationships_data = json.loads(relationships_json)
                            for order_idx, rel_data in enumerate(relationships_data):
                                operator = rel_data.get('operator')
                                linked_prefixes = rel_data.get('items', [])
                                
                                if operator and linked_prefixes:
                                    group = ItemRelationshipGroup.objects.create(
                                        section=section_instance,
                                        operator=operator,
                                        order_index=order_idx
                                    )
                                    for prefix in linked_prefixes:
                                        if prefix in saved_items_map:
                                            saved_items_map[prefix].relationship_group = group
                                            saved_items_map[prefix].save()
                        except json.JSONDecodeError:
                            logger.error(f"Error decoding relationships JSON for section {index}")

                    # پردازش شرط‌ها
                    conditions_json = request.POST.get(f'section_conditions_{index}')
                    if conditions_json:
                        try:
                            conditions_data = json.loads(conditions_json)
                            for cond_data in conditions_data:
                                cond_text = cond_data.get('text', '')
                                linked_prefixes = cond_data.get('items', [])
                                
                                if cond_text and linked_prefixes:
                                    condition_obj, _ = Condition.objects.get_or_create(text=cond_text)
                                    for prefix in linked_prefixes:
                                        if prefix in saved_items_map:
                                            saved_items_map[prefix].conditions.add(condition_obj)
                        except json.JSONDecodeError:
                            logger.error(f"Error decoding conditions JSON for section {index}")

                messages.success(request, 'اوردر با موفقیت ذخیره شد.')
                return redirect(reverse('dashboard:ordering:order_edit', kwargs={'pk': saved_order.pk}))
            
            else:
                # ساخت پیام خطا جزئی‌تر
                section_names = []
                for idx, errs in errors_detail['sections'].items():
                    sec_form = nested_sections[idx]['section_form']
                    sec_name = sec_form.instance.title or f"بخش {idx + 1}"
                    section_names.append(sec_name)
                
                error_parts = []
                if errors_detail['base']:
                    error_parts.append('اطلاعات پایه اوردر')
                if errors_detail['aliases']:
                    error_parts.append('نام‌های جایگزین')
                if section_names:
                    error_parts.append('بخش‌ها: ' + '، '.join(section_names))
                
                error_msg = 'خطا در ' + ('، '.join(error_parts) if error_parts else 'فرم') + '. لطفاً بخش‌های مشخص‌شده را بررسی کنید.'
                messages.error(request, error_msg)
        
        else:
            error_parts = []
            if not form.is_valid():
                error_parts.append('اطلاعات پایه اوردر')
            if not section_formset.is_valid():
                error_parts.append('بخش‌ها')
            if alias_formset and not alias_valid:
                error_parts.append('نام‌های جایگزین')
            
            error_msg = 'خطا در ' + ('، '.join(error_parts) if error_parts else 'فرم') + '. لطفاً فیلدها را بررسی کنید.'
            messages.error(request, error_msg)
        
        context = {
            'form': form,
            'order': order,
            'section_formset': section_formset,
            'nested_sections': nested_sections,
            'is_update': bool(order),
            'empty_section_form': section_formset.empty_form,
            'empty_item_fs': SectionItemFormSet(prefix='sections-__section_prefix__-items'),
            'empty_drug_fs': DrugSectionItemFormSet(prefix='sections-__section_prefix__-drugs'),
            'active_tab': 'order',
            'alias_formset': alias_formset,
            'errors_detail': errors_detail  # ← برای استفاده در template
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
        
        drugs = Drug.objects.filter(is_for_order=True).filter(
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

@method_decorator(csrf_exempt, name='dispatch')
class DrugQuickCreateAjaxView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            title = data.get('title', '').strip()
            code = data.get('code', '').strip()
            
            if title:
                drug, created = Drug.objects.get_or_create(
                    title=title, 
                    defaults={'is_for_order': True, 'code': code}
                )
                
                if not created:
                    drug.is_for_order = True
                    if code and not drug.code:
                        drug.code = code
                    drug.save()
                    
                return JsonResponse({'success': True, 'id': drug.id, 'text': drug.title})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
        return JsonResponse({'success': False, 'error': 'اطلاعات نامعتبر است'})

# ====================================================== #
# ==================== Dynamic View ==================== #
# ====================================================== #
class PreClinicalManageView(View):
    template_name = 'dashboard/ordering/preclinical_form.html'

    def get_order(self, order_pk):
        return get_object_or_404(Order, pk=order_pk)

    def _build_nested(self, order, post_data=None):
        groups = DynamicFieldGroup.objects.filter(order=order).order_by('order_index')
        nested = []
        for group in groups:
            root_nodes = DynamicFieldNode.objects.filter(
                group=group, parent=None
            ).prefetch_related('children').order_by('order_index')

            node_entries = []
            for node in root_nodes:
                child_fs = DynamicFieldChildNodeFormSet(
                    post_data or None,
                    instance=node,
                    prefix=f'group-{group.pk}-node-{node.pk}-children',
                )
                node_entries.append({
                    'node': node,
                    'node_form': DynamicFieldRootNodeForm(
                        post_data or None,
                        instance=node,
                        prefix=f'group-{group.pk}-node-{node.pk}',
                    ),
                    'child_fs': child_fs,
                })
            nested.append({
                'group': group,
                'group_form': DynamicFieldGroupForm(
                    post_data or None,
                    instance=group,
                    prefix=f'group-{group.pk}',
                ),
                'node_entries': node_entries,
            })
        return nested

    def _base_context(self, order, post_data=None):
        return {
            'order': order,
            'nested': self._build_nested(order, post_data),
            'new_group_form': DynamicFieldGroupForm(prefix='new_group'),
            'child_form': DynamicFieldChildNodeForm(),
            'color_choices': TailwindColor.choices,
            'active_tab': 'preclinical',}

    def get(self, request, order_pk):
        order = self.get_order(order_pk)
        return render(request, self.template_name, self._base_context(order))

    @transaction.atomic
    def post(self, request, order_pk):
        order = self.get_order(order_pk)
        action = request.POST.get('action', '')
        redirect_url = reverse('dashboard:ordering:preclinical', kwargs={'order_pk': order_pk})

        # ===== افزودن گروه ===== #
        if action == 'add_group':
            title = request.POST.get('new_group-title', '').strip()
            color = request.POST.get('new_group-color', '')
            if title:
                max_idx = DynamicFieldGroup.objects.filter(order=order).aggregate(
                    m=Max('order_index'))['m'] or 0
                DynamicFieldGroup.objects.create(
                    order=order, title=title, color=color, order_index=max_idx + 1
                )
                messages.success(request, f'گروه «{title}» اضافه شد.')
            else:
                messages.error(request, 'عنوان گروه نمی‌تواند خالی باشد.')
            return redirect(redirect_url)

        # ===== حذف گروه ===== #
        if action == 'delete_group':
            deleted, _ = DynamicFieldGroup.objects.filter(
                pk=request.POST.get('group_pk'), order=order
            ).delete()
            if deleted:
                messages.success(request, 'گروه حذف شد.')
            return redirect(redirect_url)

        # ===== افزودن گره ریشه ===== #
        if action == 'add_root_node':
            group_pk = request.POST.get('group_pk')
            group = get_object_or_404(DynamicFieldGroup, pk=group_pk, order=order)
            title = request.POST.get('new_root-title', '').strip()
            color = request.POST.get('new_root-color', '')
            if title:
                max_idx = DynamicFieldNode.objects.filter(
                    group=group, parent=None
                ).aggregate(m=Max('order_index'))['m'] or 0
                DynamicFieldNode.objects.create(
                    group=group, parent=None,
                    title=title, color=color, order_index=max_idx + 1,
                )
                messages.success(request, f'گره «{title}» اضافه شد.')
            else:
                messages.error(request, 'عنوان گره نمی‌تواند خالی باشد.')
            return redirect(redirect_url)

        # ===== حذف گره ===== #
        if action == 'delete_node':
            DynamicFieldNode.objects.filter(
                pk=request.POST.get('node_pk'),
                group__order=order,
            ).delete()
            messages.success(request, 'گره حذف شد.')
            return redirect(redirect_url)

        # ===== ذخیره همه ===== #
        if action == 'save_all':
            groups = DynamicFieldGroup.objects.filter(order=order)
            all_valid = True
            all_group_forms = []
            all_node_data = []

            for group in groups:
                gf = DynamicFieldGroupForm(request.POST, instance=group, prefix=f'group-{group.pk}')
                if not gf.is_valid():
                    all_valid = False
                all_group_forms.append((group, gf))

                for node in DynamicFieldNode.objects.filter(group=group, parent=None):
                    nf = DynamicFieldRootNodeForm(
                        request.POST, instance=node, prefix=f'group-{group.pk}-node-{node.pk}'
                    )
                    cf = DynamicFieldChildNodeFormSet(
                        request.POST, instance=node, prefix=f'group-{group.pk}-node-{node.pk}-children'
                    )
                    if not nf.is_valid() or not cf.is_valid():
                        all_valid = False
                    all_node_data.append((group, node, nf, cf))

            if not all_valid:
                nested = []
                for group, gf in all_group_forms:
                    node_entries = [
                        {'node': node, 'node_form': nf, 'child_fs': cf}
                        for g, node, nf, cf in all_node_data if g.pk == group.pk
                    ]
                    nested.append({'group': group, 'group_form': gf, 'node_entries': node_entries})
                ctx = self._base_context(order)
                ctx['nested'] = nested
                messages.error(request, 'لطفاً خطاها را برطرف کنید.')
                return render(request, self.template_name, ctx)

            for group, gf in all_group_forms:
                gf.save()

            for group, node, nf, cf in all_node_data:
                nf.save()
                new_children = cf.save(commit=False)
                for child in new_children:
                    child.group = group
                    child.parent = node
                    child.save()
                    
                for obj in cf.deleted_objects:
                    obj.delete()
                cf.save_m2m()

            messages.success(request, 'پیش‌بالینی با موفقیت ذخیره شد.')
            return redirect(redirect_url)


# ======================================================== #
# ==================== Emergency View ==================== #
# ======================================================== #
class EmergencyDispositionManageView(View):
    template_name = 'dashboard/ordering/emergency_disposition_form.html'

    def get_order(self, order_pk):
        return get_object_or_404(Order, pk=order_pk)

    def _get_or_create_disposition(self, order):
        disp, _ = EmergencyDisposition.objects.get_or_create(order=order)
        return disp

    def _build_nested(self, disposition, post_data=None):
        root_nodes = EmergencyNode.objects.filter(
            disposition=disposition, parent=None
        ).prefetch_related('children').order_by('order_index')

        nested = []
        for node in root_nodes:
            child_fs = ChildNodeFormSet(
                post_data or None,
                instance=node,
                prefix=f'node-{node.pk}-children',
            )
            nested.append({
                'node': node,
                'node_form': EmergencyRootNodeForm(
                    post_data or None,
                    instance=node,
                    prefix=f'node-{node.pk}',
                ),
                'child_fs': child_fs,
            })
        return nested

    def _base_context(self, order, disposition, post_data=None):
        return {
            'order': order,
            'disposition': disposition,
            'disp_form': EmergencyDispositionForm(
                post_data or None,
                instance=disposition,
                prefix='disp',
            ),
            'nested': self._build_nested(disposition, post_data),
            'color_choices': TailwindColor.choices,
            'child_form': EmergencyChildNodeForm(),
            'active_tab': 'emergency',
        }

    # ===== GET ===== #
    def get(self, request, order_pk):
        order = self.get_order(order_pk)
        disposition = self._get_or_create_disposition(order)
        return render(
            request,
            self.template_name,
            self._base_context(order, disposition),
        )

    # ===== POST ===== #
    @transaction.atomic
    def post(self, request, order_pk):
        order = self.get_order(order_pk)
        disposition = self._get_or_create_disposition(order)
        action = request.POST.get('action', '')

        redirect_url = reverse(
            'dashboard:ordering:emergency_disposition',
            kwargs={'order_pk': order_pk},
        )

        # ===== افزودن گره ریشه ===== #
        if action == 'add_root_node':
            title = request.POST.get('new_root-title', '').strip()
            color = request.POST.get('new_root-color', '')
            if title:
                max_idx = EmergencyNode.objects.filter(
                    disposition=disposition, parent=None
                ).aggregate(m=Max('order_index'))['m'] or 0
                EmergencyNode.objects.create(
                    disposition=disposition,
                    parent=None,
                    title=title,
                    color=color,
                    order_index=max_idx + 1,
                )
                messages.success(request, f'گره «{title}» اضافه شد.')
            else:
                messages.error(request, 'عنوان گره نمی‌تواند خالی باشد.')
            return redirect(redirect_url)

        # ===== حذف گره ===== #
        if action == 'delete_node':
            node_pk = request.POST.get('node_pk')
            deleted, _ = EmergencyNode.objects.filter(
                pk=node_pk,
                disposition=disposition,
            ).delete()
            if deleted:
                messages.success(request, 'گره حذف شد.')
            return redirect(redirect_url)

        # ===== ذخیره اطلاعات پایه ===== #
        if action == 'save_disp':
            disp_form = EmergencyDispositionForm(
                request.POST,
                instance=disposition,
                prefix='disp',
            )
            if disp_form.is_valid():
                disp_form.save()
                messages.success(request, 'اطلاعات کلی ذخیره شد.')
                return redirect(redirect_url)
            ctx = self._base_context(order, disposition)
            ctx['disp_form'] = disp_form
            return render(request, self.template_name, ctx)

        # ===== ذخیره تمامی گره‌ها ===== #
        if action == 'save_all':
            root_nodes = EmergencyNode.objects.filter(
                disposition=disposition, parent=None
            ).order_by('order_index')

            all_node_forms = []
            all_child_formsets = []
            all_valid = True

            for node in root_nodes:
                nf = EmergencyRootNodeForm(
                    request.POST,
                    instance=node,
                    prefix=f'node-{node.pk}',
                )
                cf = ChildNodeFormSet(
                    request.POST,
                    instance=node,
                    prefix=f'node-{node.pk}-children',
                )
                if not nf.is_valid():
                    all_valid = False
                if not cf.is_valid():
                    all_valid = False
                all_node_forms.append((node, nf))
                all_child_formsets.append((node, cf))

            if not all_valid:
                nested = []
                for (node, nf), (_, cf) in zip(all_node_forms, all_child_formsets):
                    nested.append({
                        'node': node,
                        'node_form': nf,
                        'child_fs': cf,
                    })
                ctx = self._base_context(order, disposition)
                ctx['nested'] = nested
                messages.error(request, 'لطفاً خطاها را برطرف کنید.')
                return render(request, self.template_name, ctx)

            # ذخیره
            for node, nf in all_node_forms:
                nf.save()

            for node, cf in all_child_formsets:
                new_children = cf.save(commit=False)
                for child in new_children:
                    child.disposition = disposition
                    child.parent = node
                    child.save()
                for obj in cf.deleted_objects:
                    obj.delete()

            messages.success(request, 'تعیین تکلیف با موفقیت ذخیره شد.')
            return redirect(redirect_url)

        return redirect(redirect_url)

# ==================================================== #
# ==================== Media View ==================== #
# ==================================================== #
class OrderMediaManageView(View):
    template_name = 'dashboard/ordering/order_media_form.html'

    def get_order(self, order_pk):
        return get_object_or_404(Order, pk=order_pk)

    def _context(self, order, image_fs=None, video_fs=None):
        return {
            'order': order,
            'image_fs': image_fs or OrderImageFormSet(instance=order, prefix='images'),
            'video_fs': video_fs or OrderVideoFormSet(instance=order, prefix='videos'),
            'active_tab': 'media',
        }

    def get(self, request, order_pk):
        order = self.get_order(order_pk)
        return render(request, self.template_name, self._context(order))

    def post(self, request, order_pk):
        order = self.get_order(order_pk)
        action = request.POST.get('action', '')
        redirect_url = request.path

        if action == 'save_images':
            fs = OrderImageFormSet(request.POST, request.FILES, instance=order, prefix='images')
            if fs.is_valid():
                fs.save()
                messages.success(request, 'تصاویر با موفقیت ذخیره شدند.')
                return redirect(redirect_url)
            return render(request, self.template_name, self._context(order, image_fs=fs))

        if action == 'save_videos':
            fs = OrderVideoFormSet(request.POST, instance=order, prefix='videos')
            if fs.is_valid():
                fs.save()
                messages.success(request, 'ویدیوها با موفقیت ذخیره شدند.')
                return redirect(redirect_url)
            return render(request, self.template_name, self._context(order, video_fs=fs))

        return redirect(redirect_url)
