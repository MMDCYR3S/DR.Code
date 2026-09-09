import json
import logging
import re

from django.shortcuts import (
    render, redirect, get_object_or_404
)
from django.views.generic import DetailView, ListView, View
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q, Max, Prefetch
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError

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

logger = logging.getLogger('order_manager')

# ============================================================ #
# ==================== Error Helper ========================== #
# ============================================================ #

def _collect_form_errors(form, label: str) -> list[str]:
    """
    ارورهای یک فرم را با ذکر دقیق نام فیلد و پیام خطا برمی‌گرداند.
    مثال خروجی: ["اطلاعات پایه → نام: این فیلد الزامی است."]
    """
    msgs = []
    for field_name, error_list in form.errors.items():
        if field_name == '__all__':
            human_field = 'عمومی'
        else:
            human_field = form.fields[field_name].label or field_name if field_name in form.fields else field_name
        for err in error_list:
            msgs.append(f"{label} ← {human_field}: {err}")
    return msgs

def _collect_formset_errors(formset, formset_label: str, form_label_fn=None) -> list[str]:
    """
    ارورهای یک فرم‌ست را با شماره فرم و نام فیلد برمی‌گرداند.
    form_label_fn: تابعی که یک فرم می‌گیرد و یک label رشته‌ای برمی‌گرداند (اختیاری).
    """
    msgs = []
    for i, form in enumerate(formset.forms):
        if not form.errors:
            continue
        if form_label_fn:
            row_label = form_label_fn(form, i)
        else:
            row_label = f"ردیف {i + 1}"
        msgs.extend(_collect_form_errors(form, f"{formset_label} / {row_label}"))
    if formset.non_form_errors():
        for err in formset.non_form_errors():
            msgs.append(f"{formset_label}: {err}")
    return msgs

def _emit_error_messages(request, all_error_lines: list[str], summary: str = 'لطفاً خطاهای زیر را برطرف کنید:') -> None:
    """
    خطاها را به‌صورت پیام‌های جداگانه (تک‌خطی) ثبت می‌کند تا با Toastify
    در messages.html به‌درستی نمایش داده شوند.
    نکته: پیام‌ها نباید شامل newline باشند، چون در text: "{{ message }}"
    باعث خطای syntax در جاوااسکریپت می‌شوند و toast نمایش داده نمی‌شود.
    """
    messages.error(request, summary)
    for line in all_error_lines:
        # اطمینان از تک‌خطی بودن (جایگزینی newline با فاصله برای ایمنی Toastify)
        safe_line = ' '.join(str(line).splitlines())
        messages.error(request, safe_line)

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

# ============================================================ #
# ==================== Order List View ======================== #
# ============================================================ #
class OrderListView(LoginRequiredMixin, ListView):
    """
    لیست اوردرها با جستجو، فیلتر دسته‌بندی، مرتب‌سازی و صفحه‌بندی
    مطابق با الگوی نمونه (مدیریت داروها)
    """
    model = Order
    template_name = 'dashboard/ordering/list.html'
    context_object_name = 'orders'
    paginate_by = 15

    def get_queryset(self):
        queryset = Order.objects.select_related('category').order_by('-created_at')

        search = self.request.GET.get('search', '').strip()
        category = self.request.GET.get('category')
        sort_by = self.request.GET.get('sort_by', '-created_at')

        if search:
            queryset = queryset.filter(Q(name__icontains=search))
        if category:
            queryset = queryset.filter(category_id=category)
        if sort_by:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ===== بردکرامب ===== #
        context['breadcrumb'] = [
            {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')},
            {'label': 'مدیریت اوردرها', 'url': ''}
        ]

        # ===== جستجو و فیلترهای جاری ===== #
        context['search'] = self.request.GET.get('search', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['sort_by'] = self.request.GET.get('sort_by', '-created_at')

        # ===== آمار کارت‌ها ===== #
        total = Order.objects.count()
        active = Order.objects.filter(is_active=True).count() if hasattr(Order, 'is_active') else 0
        draft = Order.objects.filter(is_draft=True).count() if hasattr(Order, 'is_draft') else 0

        context['stats'] = {
            'total': total,
            'active': active,
            'draft': draft,
        }

        # ===== لیست دسته‌بندی‌ها برای فیلتر ===== #
        from apps.prescriptions.models import PrescriptionCategory
        context['categories'] = PrescriptionCategory.objects.all().order_by('title')

        return context


# ============================================================ #
# ==================== Order Detail View ====================== #
# ============================================================ #
class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    نمایش جزییات کامل یک اوردر با تمام روابط (بخش‌ها، آیتم‌ها، داروها،
    گروه‌های پیش‌بالینی، تعیین تکلیف اورژانس، تصاویر، ویدیوها)
    """
    model = Order
    template_name = 'dashboard/ordering/detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        # ── Prefetch شرط‌های آیتم‌های متنی ──
        item_conditions_prefetch = Prefetch(
            "conditions",
            queryset=Condition.objects.order_by("order_index"),
        )

        # ── Prefetch آیتم‌های متنی با شرط‌ها ──
        items_prefetch = Prefetch(
            "items",
            queryset=SectionItem.objects.prefetch_related(
                item_conditions_prefetch,
            ).select_related("relationship_group").order_by("order_index"),
        )

        # ── Prefetch شرط‌های آیتم‌های دارویی ──
        drug_item_conditions_prefetch = Prefetch(
            "conditions",
            queryset=Condition.objects.order_by("order_index"),
        )

        # ── Prefetch آیتم‌های دارویی با شرط‌ها ──
        drug_items_prefetch = Prefetch(
            "drug_items",
            queryset=DrugSectionItem.objects.select_related(
                "drug", "relationship_group"
            ).prefetch_related(
                drug_item_conditions_prefetch,
            ).order_by("order_index"),
        )

        # ── Prefetch گروه‌های ارتباطی ──
        relationship_groups_prefetch = Prefetch(
            "relationship_groups",
            queryset=ItemRelationshipGroup.objects.order_by("order_index"),
        )

        # ── Prefetch بخش‌ها ──
        sections_prefetch = Prefetch(
            "sections",
            queryset=OrderSection.objects.prefetch_related(
                items_prefetch,
                drug_items_prefetch,
                relationship_groups_prefetch,
            ).order_by("order_index"),
        )

        # ── Prefetch گره‌های پیش‌بالینی ──
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

        # ── Prefetch گره‌های تعیین تکلیف ──
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
                Prefetch("images", queryset=OrderImage.objects.order_by("order_index")),
                Prefetch("videos", queryset=OrderVideo.objects.order_by("order_index")),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ===== بردکرامب ===== #
        context['breadcrumb'] = [
            {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')},
            {'label': 'مدیریت اوردرها', 'url': reverse_lazy('dashboard:ordering:order_list')},
            {'label': self.object.name, 'url': ''}
        ]

        return context


# ============================================================ #
# ==================== Order Delete View ====================== #
# ============================================================ #
class OrderDeleteView(LoginRequiredMixin, View):
    """
    حذف اوردر (با نمایش پیام موفقیت و ریدایرکت به لیست)
    مطابق با الگوی نمونه (ارسال فرم POST)
    """
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        name = order.name
        order.delete()
        messages.success(request, f'اوردر «{name}» با موفقیت حذف شد.')
        return redirect('dashboard:ordering:order_list')

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
        context['breadcrumb'] = [
            {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')},
            {'label': 'مدیریت اوردرها', 'url': reverse_lazy('dashboard:ordering:order_list')},
            {'label': 'افزودن اوردر جدید' if not order else f'ویرایش اوردر: {order.name}', 'url': ''}
        ]
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
            # ─────────────────── تغییر: اضافه شدن try/except ───────────────────
            try:
                saved_order = form.save(commit=False)
                section_formset.instance = saved_order
                if alias_formset:
                    alias_formset.instance = saved_order

                for i, section_form in enumerate(section_formset):
                    if not section_form.cleaned_data and not section_form.instance.pk:
                        continue
                    item_fs = SectionItemFormSet(request.POST, instance=section_form.instance, prefix=f"{section_form.prefix}-items")
                    drug_fs = DrugSectionItemFormSet(request.POST, instance=section_form.instance, prefix=f"{section_form.prefix}-drugs")

                    sec_name = section_form.instance.title or f"بخش {i + 1}"

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
                    saved_order.save()  # ⚠️ اینجا ممکنه ValidationError رخ بده (slug تکراری)
                    form.save_m2m()
                    section_formset.save()
                    if alias_formset:
                        alias_formset.save()

                    section_map = {form.prefix: form.instance for form in section_formset}
                    saved_items_map = {}

                    # =======================================================================
                    # مرحله ۱: ابتدا تمام آیتم‌ها و داروها را ذخیره کن
                    # =======================================================================
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

                    # =======================================================================
                    # مرحله ۲: پاکسازی ایمن دیتابیس از روابط قدیمی
                    # =======================================================================
                    SectionItem.objects.filter(section__order=saved_order).update(relationship_group=None)
                    DrugSectionItem.objects.filter(section__order=saved_order).update(relationship_group=None)
                    ItemRelationshipGroup.objects.filter(section__order=saved_order).delete()

                    # =======================================================================
                    # مرحله ۳: بازسازی روابط و شرط‌های جدید
                    # =======================================================================
                    for data in nested_sections:
                        section_instance = section_map.get(data['section_form'].prefix)
                        if not section_instance or not section_instance.pk:
                            continue

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
                                                saved_item = saved_items_map[prefix]
                                                saved_item.relationship_group = group
                                                saved_item.save(update_fields=['relationship_group'])
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
                    # ─── جمع‌آوری تمام خطاها با جزئیات کامل ───────────────────
                    all_error_lines = []
                    if errors_detail['base']:
                        all_error_lines.extend(_collect_form_errors(form, 'اطلاعات پایه اوردر'))
                    if alias_formset and errors_detail['aliases']:
                        all_error_lines.extend(
                            _collect_formset_errors(
                                alias_formset,
                                'نام‌های جایگزین',
                                form_label_fn=lambda f, i: f.instance.alias or f"ردیف {i + 1}",
                            )
                        )
                    for idx, errs in errors_detail['sections'].items():
                        sec_form = nested_sections[idx]['section_form']
                        sec_name = sec_form.instance.title or f"بخش {idx + 1}"
                        if errs.get('section_errors'):
                            all_error_lines.extend(_collect_form_errors(sec_form, f"سکشن «{sec_name}»"))
                        item_fs = nested_sections[idx]['item_fs']
                        if errs.get('item_errors'):
                            all_error_lines.extend(
                                _collect_formset_errors(
                                    item_fs,
                                    f"سکشن «{sec_name}» / آیتم‌های متنی",
                                    form_label_fn=lambda f, i: f.instance.text[:20] if f.instance.text else f"آیتم {i + 1}",
                                )
                            )
                        drug_fs = nested_sections[idx]['drug_fs']
                        if errs.get('drug_errors'):
                            all_error_lines.extend(
                                _collect_formset_errors(
                                    drug_fs,
                                    f"سکشن «{sec_name}» / داروها",
                                    form_label_fn=lambda f, i: str(f.instance.drug) if f.instance.drug_id else f"دارو {i + 1}",
                                )
                            )
                    _emit_error_messages(request, all_error_lines, 'ذخیره اوردر ناموفق بود — خطاهای زیر را برطرف کنید:')

            # ─────────────────── تغییر: گرفتن خطای ValidationError ───────────────────
            except ValidationError as e:
                # خطای اعتبارسنجی (مثلاً slug تکراری) را بگیر و به فرم اضافه کن
                logger.error(f"❌ ValidationError during order save: {e}")
                
                # اگر خطا دیکشنری فیلدها رو داشته باشه (مثل clean مدل)
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            form.add_error(field, error)
                # اگر یک پیام ساده باشه
                else:
                    form.add_error('name', str(e))
                
                # تنظیم مجدد متغیرها برای نمایش دوباره فرم
                all_nested_valid = False
                errors_detail['base'] = form.errors

        # ─── خارج از if اصلی: همیشه اگر به اینجا رسیدیم فرم رو دوباره نشون بده ───
        # (چه خطا در مرحله اول باشه، چه nested invalid باشه، چه ValidationError)
        all_error_lines = []

        if errors_detail.get('base'):
            all_error_lines.extend(_collect_form_errors(form, 'اطلاعات پایه اوردر'))

        if not section_formset.is_valid():
            all_error_lines.extend(
                _collect_formset_errors(
                    section_formset,
                    'بخش‌ها',
                    form_label_fn=lambda f, i: f.instance.title or f"بخش {i + 1}",
                )
            )

        if alias_formset and errors_detail.get('aliases'):
            all_error_lines.extend(
                _collect_formset_errors(
                    alias_formset,
                    'نام‌های جایگزین',
                    form_label_fn=lambda f, i: f.instance.alias or f"ردیف {i + 1}",
                )
            )

        for idx, errs in errors_detail.get('sections', {}).items():
            if idx < len(nested_sections):
                sec_form = nested_sections[idx]['section_form']
                sec_name = sec_form.instance.title or f"بخش {idx + 1}"
                if errs.get('section_errors'):
                    all_error_lines.extend(_collect_form_errors(sec_form, f"سکشن «{sec_name}»"))
                item_fs = nested_sections[idx]['item_fs']
                if errs.get('item_errors'):
                    all_error_lines.extend(
                        _collect_formset_errors(
                            item_fs,
                            f"سکشن «{sec_name}» / آیتم‌های متنی",
                            form_label_fn=lambda f, i: f.instance.text[:20] if f.instance.text else f"آیتم {i + 1}",
                        )
                    )
                drug_fs = nested_sections[idx]['drug_fs']
                if errs.get('drug_errors'):
                    all_error_lines.extend(
                        _collect_formset_errors(
                            drug_fs,
                            f"سکشن «{sec_name}» / داروها",
                            form_label_fn=lambda f, i: str(f.instance.drug) if f.instance.drug_id else f"دارو {i + 1}",
                        )
                    )

        if all_error_lines:
            _emit_error_messages(request, all_error_lines, 'ذخیره اوردر ناموفق بود — خطاهای زیر را برطرف کنید:')
        
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
            'errors_detail': errors_detail
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
    """
    مدیریت پیش‌بالینی.

    نکته معماری (تغییر این بخش):
    --------------------------------
    ایجاد گروه، گره ریشه و فرزند دیگر به‌صورت یک ریکوئست جداگانه و رفرش
    صفحه انجام نمی‌شود. تمام آیتم‌های جدید (گروه، گره، فرزند) در سمت کلاینت
    (JS) ساخته می‌شوند و تنها با زدن دکمهٔ «ذخیره همه» در دیتابیس persist
    می‌گردند.

    • گروه‌های موجود: همانند قبل با فرم اختصاصی رندر می‌شوند، با این تفاوت که
      حذف آن‌ها به‌جای POST جداگانه، با یک چک‌باکس DELETE (deferred) انجام
      می‌شود و در زمان save_all اعمال می‌گردد.
    • گروه‌های جدید: با پیشوند موقت (مثل new1, new2) در POST ارسال می‌شوند،
      در save_all اعتبارسنجی و سپس ایجاد می‌گردند و گره‌هایشان پس از ساخت
      گروه، به آن متصل می‌شوند.
    • گره‌های موجود: حذف با چک‌باکس DELETE (deferred)، اعمال در save_all.
    • گره‌های جدید: با پیشوند موقت در POST، در save_all ایجاد و فرزندانشان
      به آن‌ها متصل می‌شوند.

    منطق ایجاد/ویرایش/حذف گروه دقیقاً مشابه گره و فرزند است (بدون رفرش).
    """
    template_name = 'dashboard/ordering/preclinical_form.html'

    def get_order(self, order_pk):
        return get_object_or_404(Order, pk=order_pk)

    @staticmethod
    def _extract_new_group_temp_ids(post_data):
        """
        شناسه‌های موقتِ گروه‌های جدید را از POST استخراج می‌کند.
        گروه‌های موجود پیشوندشان عددی (pk) است؛ گروه‌های جدید رشته‌ای مثل new1.
        کلیدهای گره‌ها (...-node-...) نادیده گرفته می‌شوند.
        ترتیب ظاهر در POST حفظ می‌شود (برای نمایش پایدار).
        """
        pat = re.compile(r'^group-(?!.*-node-)(.+?)-title$')
        ids = []
        seen = set()
        for key in post_data.keys():
            m = pat.match(key)
            if m:
                tid = m.group(1)
                if not tid.isdigit() and tid not in seen:
                    seen.add(tid)
                    ids.append(tid)
        return ids

    @staticmethod
    def _extract_new_root_temp_ids(post_data, group_pk):
        """
        شناسه‌های موقتِ گره‌های ریشهٔ جدید را از POST استخراج می‌کند.
        گره‌های موجود پیشوندشان عددی (pk) است؛ گره‌های جدید رشته‌ای مثل new1.
        کلیدهای فرزندان (...-children-...) نادیده گرفته می‌شوند.
        ترتیب ظاهر در POST حفظ می‌شود (برای نمایش پایدار).
        group_pk می‌تواند عدد (گروه موجود) یا رشتهٔ موقت (گروه جدید) باشد.
        """
        pat = re.compile(rf'^group-{group_pk}-node-(?!.*-children-)(.+?)-title$')
        ids = []
        seen = set()
        for key in post_data.keys():
            m = pat.match(key)
            if m:
                tid = m.group(1)
                if not tid.isdigit() and tid not in seen:
                    seen.add(tid)
                    ids.append(tid)
        return ids

    def _build_nested(self, order, post_data=None):
        nested = []

        # ── گروه‌های موجود ── #
        groups = DynamicFieldGroup.objects.filter(order=order).order_by('order_index')
        for group in groups:
            group_pk_str = str(group.pk)
            delete_flag = bool(post_data) and bool(post_data.get(f'group-{group_pk_str}-DELETE'))

            root_nodes = DynamicFieldNode.objects.filter(
                group=group, parent=None
            ).prefetch_related('children').order_by('order_index')

            node_entries = []
            # ── گره‌های ریشه موجود ── #
            for node in root_nodes:
                prefix = f'group-{group.pk}-node-{node.pk}'
                node_delete = bool(post_data) and bool(post_data.get(f'{prefix}-DELETE'))
                node_entries.append({
                    'node': node,
                    'node_id': str(node.pk),
                    'is_new': False,
                    'node_form': DynamicFieldRootNodeForm(
                        post_data or None, instance=node, prefix=prefix,
                    ),
                    'child_fs': DynamicFieldChildNodeFormSet(
                        post_data or None, instance=node,
                        prefix=f'{prefix}-children',
                    ),
                    'delete_flag': node_delete,
                })

            # ── گره‌های ریشه جدید (تنها در حالت POST) ── #
            if post_data:
                for temp_id in self._extract_new_root_temp_ids(post_data, group.pk):
                    prefix = f'group-{group.pk}-node-{temp_id}'
                    temp_instance = DynamicFieldNode(group=group)
                    node_entries.append({
                        'node': None,
                        'node_id': temp_id,
                        'is_new': True,
                        'node_form': DynamicFieldRootNodeForm(post_data, prefix=prefix),
                        'child_fs': DynamicFieldChildNodeFormSet(
                            post_data, instance=temp_instance,
                            prefix=f'{prefix}-children',
                            queryset=DynamicFieldNode.objects.none(),
                        ),
                        'delete_flag': False,
                    })

            nested.append({
                'group': group,
                'group_id': group_pk_str,
                'is_new': False,
                'delete_flag': delete_flag,
                'group_form': DynamicFieldGroupForm(
                    post_data or None, instance=group, prefix=f'group-{group.pk}',
                ),
                'node_entries': node_entries,
            })

        # ── گروه‌های جدید (تنها در حالت POST) ── #
        if post_data:
            for g_temp_id in self._extract_new_group_temp_ids(post_data):
                node_entries = []
                # گره‌های ریشه جدید داخل گروه جدید
                for temp_id in self._extract_new_root_temp_ids(post_data, g_temp_id):
                    prefix = f'group-{g_temp_id}-node-{temp_id}'
                    temp_instance = DynamicFieldNode()
                    node_entries.append({
                        'node': None,
                        'node_id': temp_id,
                        'is_new': True,
                        'node_form': DynamicFieldRootNodeForm(post_data, prefix=prefix),
                        'child_fs': DynamicFieldChildNodeFormSet(
                            post_data, instance=temp_instance,
                            prefix=f'{prefix}-children',
                            queryset=DynamicFieldNode.objects.none(),
                        ),
                        'delete_flag': False,
                    })

                nested.append({
                    'group': None,
                    'group_id': g_temp_id,
                    'is_new': True,
                    'delete_flag': False,
                    'group_form': DynamicFieldGroupForm(post_data, prefix=f'group-{g_temp_id}'),
                    'node_entries': node_entries,
                })

        return nested

    def _base_context(self, order, post_data=None):
        return {
            'order': order,
            'nested': self._build_nested(order, post_data),
            'child_form': DynamicFieldChildNodeForm(),
            'color_choices': TailwindColor.choices,
            'active_tab': 'preclinical',
            'breadcrumb': [
                {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')},
                {'label': 'مدیریت اوردرها', 'url': reverse_lazy('dashboard:ordering:order_list')},
                {'label': 'افزودن اوردر جدید' if not order else f'ویرایش اوردر: {order.name}', 'url': ''}
            ]}

    def get(self, request, order_pk):
        order = self.get_order(order_pk)
        return render(request, self.template_name, self._base_context(order))

    @transaction.atomic
    def post(self, request, order_pk):
        order = self.get_order(order_pk)
        action = request.POST.get('action', '')
        redirect_url = reverse('dashboard:ordering:preclinical', kwargs={'order_pk': order_pk})

        # ===== ذخیره همه (شامل گروه‌های موجود + جدید و گره‌های موجود + جدید) ===== #
        # ایجاد/ویرایش/حذف گروه دقیقاً مشابه گره و فرزند، بدون رفرش صفحه،
        # تنها با زدن دکمهٔ «ذخیره همه» در دیتابیس persist می‌شود.
        if action == 'save_all':
            groups = DynamicFieldGroup.objects.filter(order=order)
            all_valid = True
            all_group_data = []     # (group_or_None, gf, delete_flag, is_new, id_str)
            existing_node_data = []  # (group, node, nf, cf, delete_flag)
            new_node_data = []       # (group_ref, node_temp_id, nf, cf, in_new_group)
                                     # group_ref: group instance (موجود) یا g_temp_id (جدید)

            # ── گروه‌های موجود ── #
            for group in groups:
                g_prefix = f'group-{group.pk}'
                delete_flag = bool(request.POST.get(f'{g_prefix}-DELETE'))
                gf = DynamicFieldGroupForm(request.POST, instance=group, prefix=g_prefix)
                if not delete_flag:
                    if not gf.is_valid():
                        all_valid = False
                all_group_data.append((group, gf, delete_flag, False, str(group.pk)))

                # ── گره‌های موجود در گروه موجود ── #
                for node in DynamicFieldNode.objects.filter(group=group, parent=None):
                    prefix = f'group-{group.pk}-node-{node.pk}'
                    node_delete = bool(request.POST.get(f'{prefix}-DELETE'))
                    nf = DynamicFieldRootNodeForm(request.POST, instance=node, prefix=prefix)
                    cf = DynamicFieldChildNodeFormSet(
                        request.POST, instance=node, prefix=f'{prefix}-children'
                    )
                    # اگر گروه یا گره برای حذف علامت خورده، اعتبارسنجی لازم نیست
                    if not delete_flag and not node_delete:
                        if not nf.is_valid() or not cf.is_valid():
                            all_valid = False
                    existing_node_data.append((group, node, nf, cf, node_delete))

                # ── گره‌های جدید در گروه موجود ── #
                for temp_id in self._extract_new_root_temp_ids(request.POST, group.pk):
                    prefix = f'group-{group.pk}-node-{temp_id}'
                    nf = DynamicFieldRootNodeForm(request.POST, prefix=prefix)
                    temp_instance = DynamicFieldNode(group=group)
                    cf = DynamicFieldChildNodeFormSet(
                        request.POST, instance=temp_instance,
                        prefix=f'{prefix}-children',
                        queryset=DynamicFieldNode.objects.none(),
                    )
                    # اگر گروه برای حذف علامت خورده، اعتبارسنجی گره جدید لازم نیست
                    if not delete_flag:
                        if not nf.is_valid() or not cf.is_valid():
                            all_valid = False
                    new_node_data.append((group, temp_id, nf, cf, False))

            # ── گروه‌های جدید ── #
            for g_temp_id in self._extract_new_group_temp_ids(request.POST):
                g_prefix = f'group-{g_temp_id}'
                gf = DynamicFieldGroupForm(request.POST, prefix=g_prefix)
                if not gf.is_valid():
                    all_valid = False
                all_group_data.append((None, gf, False, True, g_temp_id))

                # ── گره‌های جدید داخل گروه جدید ── #
                for temp_id in self._extract_new_root_temp_ids(request.POST, g_temp_id):
                    prefix = f'group-{g_temp_id}-node-{temp_id}'
                    nf = DynamicFieldRootNodeForm(request.POST, prefix=prefix)
                    temp_instance = DynamicFieldNode()
                    cf = DynamicFieldChildNodeFormSet(
                        request.POST, instance=temp_instance,
                        prefix=f'{prefix}-children',
                        queryset=DynamicFieldNode.objects.none(),
                    )
                    if not nf.is_valid() or not cf.is_valid():
                        all_valid = False
                    new_node_data.append((g_temp_id, temp_id, nf, cf, True))

            # مجموعهٔ pk گروه‌هایی که برای حذف علامت خورده‌اند
            # (برای نادیده گرفتن گره‌هایشان در اعتبارسنجی/خطا و ذخیره)
            deleted_group_pks = {
                group.pk for group, gf, delete_flag, is_new, id_str
                in all_group_data if not is_new and delete_flag
            }

            # ── در صورت خطا: رندر مجدد با حفظ داده‌های آیتم‌های جدید ── #
            if not all_valid:
                nested = []
                # گروه‌های موجود
                for group, gf, delete_flag, is_new, id_str in all_group_data:
                    if is_new:
                        continue
                    node_entries = []
                    for g, node, nf, cf, df in existing_node_data:
                        if g.pk == group.pk:
                            node_entries.append({
                                'node': node, 'node_id': str(node.pk),
                                'is_new': False, 'node_form': nf,
                                'child_fs': cf, 'delete_flag': df,
                            })
                    for g, tid, nf, cf, in_new in new_node_data:
                        if not in_new and g.pk == group.pk:
                            node_entries.append({
                                'node': None, 'node_id': tid,
                                'is_new': True, 'node_form': nf,
                                'child_fs': cf, 'delete_flag': False,
                            })
                    nested.append({
                        'group': group, 'group_id': id_str,
                        'is_new': False, 'delete_flag': delete_flag,
                        'group_form': gf, 'node_entries': node_entries,
                    })
                # گروه‌های جدید
                for group, gf, delete_flag, is_new, id_str in all_group_data:
                    if not is_new:
                        continue
                    node_entries = []
                    for g, tid, nf, cf, in_new in new_node_data:
                        if in_new and g == id_str:
                            node_entries.append({
                                'node': None, 'node_id': tid,
                                'is_new': True, 'node_form': nf,
                                'child_fs': cf, 'delete_flag': False,
                            })
                    nested.append({
                        'group': None, 'group_id': id_str,
                        'is_new': True, 'delete_flag': False,
                        'group_form': gf, 'node_entries': node_entries,
                    })

                ctx = self._base_context(order)
                ctx['nested'] = nested

                all_error_lines = []
                for group, gf, delete_flag, is_new, id_str in all_group_data:
                    if delete_flag:
                        continue
                    if is_new:
                        label = f"گروه جدید ({id_str})"
                    else:
                        label = f"گروه «{group.title or id_str}»"
                    if gf.errors:
                        all_error_lines.extend(_collect_form_errors(gf, label))

                for group, node, nf, cf, delete_flag in existing_node_data:
                    # گره‌های موجود در گروه‌های حذف‌شده نادیده گرفته می‌شوند
                    if group.pk in deleted_group_pks or delete_flag:
                        continue
                    group_label = group.title or f"گروه {group.pk}"
                    node_label = node.title or f"گره {node.pk}"
                    if nf.errors:
                        all_error_lines.extend(
                            _collect_form_errors(nf, f"گروه «{group_label}» / گره «{node_label}»")
                        )
                    if cf.errors:
                        all_error_lines.extend(
                            _collect_formset_errors(
                                cf,
                                f"گروه «{group_label}» / گره «{node_label}» / فرزندان",
                                form_label_fn=lambda f, i: f.instance.title or f"فرزند {i + 1}",
                            )
                        )

                for group_ref, temp_id, nf, cf, in_new in new_node_data:
                    # گره‌های جدید در گروه‌های حذف‌شده نادیده گرفته می‌شوند
                    if not in_new and group_ref.pk in deleted_group_pks:
                        continue
                    if in_new:
                        group_label = f"گروه جدید ({group_ref})"
                    else:
                        group_label = group_ref.title or f"گروه {group_ref.pk}"
                    label = f"گروه «{group_label}» / گره جدید ({temp_id})"
                    if nf.errors:
                        all_error_lines.extend(_collect_form_errors(nf, label))
                    if cf.errors:
                        all_error_lines.extend(
                            _collect_formset_errors(
                                cf,
                                f"{label} / فرزندان",
                                form_label_fn=lambda f, i: f.instance.title or f"فرزند {i + 1}",
                            )
                        )

                _emit_error_messages(request, all_error_lines, 'ذخیره پیش‌بالینی ناموفق بود — خطاهای زیر را برطرف کنید:')
                return render(request, self.template_name, ctx)

            # ── ذخیره نهایی ── #
            # ۱) گروه‌های موجود: حذف (cascade) یا ذخیرهٔ ویرایش
            for group, gf, delete_flag, is_new, id_str in all_group_data:
                if is_new:
                    continue
                if delete_flag:
                    # حذف گروه + گره‌ها و فرزندان (cascade)
                    deleted_group_pks.add(group.pk)
                    group.delete()
                    continue
                gf.save()

            # ۲) گره‌های موجود: حذف یا ذخیره + فرزندان
            for group, node, nf, cf, delete_flag in existing_node_data:
                if group.pk in deleted_group_pks:
                    continue
                if delete_flag:
                    node.delete()
                    continue
                nf.save()

                # ذخیره فرزندان موجود
                cf.is_valid()  # اعتبارسنجی کامل فرم‌ست
                for form in cf.forms:
                    if not form.is_valid():
                        continue
                    if form.cleaned_data.get('DELETE', False):
                        if form.instance.pk:
                            form.instance.delete()
                        continue
                    if form.has_changed() or form.instance.pk is None:
                        child = form.save(commit=False)
                        child.group = group
                        child.parent = node
                        child.save()

            # ۳) گروه‌های جدید: ایجاد، سپس گره‌های جدید داخلشان
            for group, gf, delete_flag, is_new, id_str in all_group_data:
                if not is_new:
                    continue
                new_group = gf.save(commit=False)
                new_group.order = order
                new_group.save()

                for group_ref, temp_id, nf, cf, in_new in new_node_data:
                    if not in_new or group_ref != id_str:
                        continue
                    new_node = nf.save(commit=False)
                    new_node.group = new_group
                    new_node.parent = None
                    new_node.save()

                    children_prefix = f'group-{id_str}-node-{temp_id}-children'
                    cf2 = DynamicFieldChildNodeFormSet(
                        request.POST, instance=new_node,
                        prefix=children_prefix,
                        queryset=DynamicFieldNode.objects.none(),
                    )
                    cf2.is_valid()
                    for form in cf2.forms:
                        if not form.is_valid():
                            continue
                        if form.cleaned_data.get('DELETE', False):
                            continue
                        if form.has_changed() or form.instance.pk is None:
                            child = form.save(commit=False)
                            child.group = new_group
                            child.parent = new_node
                            child.save()

            # ۴) گره‌های جدید در گروه‌های موجود
            for group_ref, temp_id, nf, cf, in_new in new_node_data:
                if in_new:
                    continue
                if group_ref.pk in deleted_group_pks:
                    continue
                new_node = nf.save(commit=False)
                new_node.group = group_ref
                new_node.parent = None
                new_node.save()

                children_prefix = f'group-{group_ref.pk}-node-{temp_id}-children'
                cf2 = DynamicFieldChildNodeFormSet(
                    request.POST, instance=new_node,
                    prefix=children_prefix,
                    queryset=DynamicFieldNode.objects.none(),
                )
                cf2.is_valid()
                for form in cf2.forms:
                    if not form.is_valid():
                        continue
                    if form.cleaned_data.get('DELETE', False):
                        continue
                    if form.has_changed() or form.instance.pk is None:
                        child = form.save(commit=False)
                        child.group = group_ref
                        child.parent = new_node
                        child.save()

            messages.success(request, 'پیش‌بالینی با موفقیت ذخیره شد.')
            return redirect(redirect_url)

        return redirect(redirect_url)

# ======================================================== #
# ==================== Emergency View ==================== #
# ======================================================== #
class EmergencyDispositionManageView(View):
    """
    مدیریت تعیین تکلیف اورژانسی.

    نکته معماری (تغییر این بخش):
    --------------------------------
    ایجاد گره ریشه دیگر رفرش صفحه ندارد؛ گره‌های جدید در JS ساخته و با
    «ذخیره همه» persist می‌شوند. حذف گره موجود نیز به‌جای POST جداگانه،
    deferred (چک‌باکس DELETE) و در save_all اعمال می‌شود.

    بخش «ذخیره اطلاعات کلی» (save_disp) و سایر ویوها دست‌نخورده‌اند.
    """
    template_name = 'dashboard/ordering/emergency_disposition_form.html'

    def get_order(self, order_pk):
        return get_object_or_404(Order, pk=order_pk)

    def _get_or_create_disposition(self, order):
        disp, _ = EmergencyDisposition.objects.get_or_create(order=order)
        return disp

    @staticmethod
    def _extract_new_root_temp_ids(post_data):
        """
        شناسه‌های موقتِ گره‌های ریشهٔ جدید را از POST استخراج می‌کند.
        پیشوند گره موجود عددی (pk) است؛ جدید رشته‌ای (new1, ...).
        کلیدهای فرزندان نادیده گرفته می‌شوند. ترتیب POST حفظ می‌شود.
        """
        pat = re.compile(r'^node-(?!.*-children-)(.+?)-title$')
        ids = []
        seen = set()
        for key in post_data.keys():
            m = pat.match(key)
            if m:
                tid = m.group(1)
                if not tid.isdigit() and tid not in seen:
                    seen.add(tid)
                    ids.append(tid)
        return ids

    def _build_nested(self, disposition, post_data=None):
        root_nodes = EmergencyNode.objects.filter(
            disposition=disposition, parent=None
        ).prefetch_related('children').order_by('order_index')

        node_entries = []
        # ── گره‌های ریشه موجود ── #
        for node in root_nodes:
            prefix = f'node-{node.pk}'
            delete_flag = bool(post_data) and bool(post_data.get(f'{prefix}-DELETE'))
            node_entries.append({
                'node': node,
                'node_id': str(node.pk),
                'is_new': False,
                'node_form': EmergencyRootNodeForm(
                    post_data or None, instance=node, prefix=prefix,
                ),
                'child_fs': ChildNodeFormSet(
                    post_data or None, instance=node,
                    prefix=f'{prefix}-children',
                ),
                'delete_flag': delete_flag,
            })

        # ── گره‌های ریشه جدید (تنها در حالت POST) ── #
        if post_data:
            for temp_id in self._extract_new_root_temp_ids(post_data):
                prefix = f'node-{temp_id}'
                temp_instance = EmergencyNode(disposition=disposition)
                node_entries.append({
                    'node': None,
                    'node_id': temp_id,
                    'is_new': True,
                    'node_form': EmergencyRootNodeForm(post_data, prefix=prefix),
                    'child_fs': ChildNodeFormSet(
                        post_data, instance=temp_instance,
                        prefix=f'{prefix}-children',
                        queryset=EmergencyNode.objects.none(),
                    ),
                    'delete_flag': False,
                })

        return node_entries

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
            'breadcrumb': [
                {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')},
                {'label': 'مدیریت اوردرها', 'url': reverse_lazy('dashboard:ordering:order_list')},
                {'label': 'افزودن اوردر جدید' if not order else f'ویرایش اوردر: {order.name}', 'url': ''}
            ]
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

        # ===== ذخیره اطلاعات پایه ===== #
        # (دست‌نخورده — خارج از اسکوپِ گره)
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

            all_error_lines = _collect_form_errors(disp_form, 'اطلاعات کلی تعیین تکلیف')
            _emit_error_messages(request, all_error_lines, 'ذخیره اطلاعات کلی ناموفق بود:')
            ctx = self._base_context(order, disposition)
            ctx['disp_form'] = disp_form
            return render(request, self.template_name, ctx)

        # ===== ذخیره تمامی گره‌ها (موجود + جدید) ===== #
        if action == 'save_all':
            root_nodes = EmergencyNode.objects.filter(
                disposition=disposition, parent=None
            ).order_by('order_index')

            all_valid = True
            existing_node_data = []   # (node, nf, cf, delete_flag)
            new_node_data = []        # (temp_id, nf, cf)

            for node in root_nodes:
                prefix = f'node-{node.pk}'
                delete_flag = bool(request.POST.get(f'{prefix}-DELETE'))
                nf = EmergencyRootNodeForm(request.POST, instance=node, prefix=prefix)
                cf = ChildNodeFormSet(request.POST, instance=node, prefix=f'{prefix}-children')
                if not delete_flag:
                    if not nf.is_valid() or not cf.is_valid():
                        all_valid = False
                existing_node_data.append((node, nf, cf, delete_flag))

            for temp_id in self._extract_new_root_temp_ids(request.POST):
                prefix = f'node-{temp_id}'
                nf = EmergencyRootNodeForm(request.POST, prefix=prefix)
                temp_instance = EmergencyNode(disposition=disposition)
                cf = ChildNodeFormSet(
                    request.POST, instance=temp_instance,
                    prefix=f'{prefix}-children',
                    queryset=EmergencyNode.objects.none(),
                )
                if not nf.is_valid() or not cf.is_valid():
                    all_valid = False
                new_node_data.append((temp_id, nf, cf))

            # ── در صورت خطا: رندر مجدد با حفظ داده‌های گره‌های جدید ── #
            if not all_valid:
                nested = []
                for node, nf, cf, delete_flag in existing_node_data:
                    nested.append({
                        'node': node, 'node_id': str(node.pk),
                        'is_new': False, 'node_form': nf,
                        'child_fs': cf, 'delete_flag': delete_flag,
                    })
                for temp_id, nf, cf in new_node_data:
                    nested.append({
                        'node': None, 'node_id': temp_id,
                        'is_new': True, 'node_form': nf,
                        'child_fs': cf, 'delete_flag': False,
                    })
                ctx = self._base_context(order, disposition)
                ctx['nested'] = nested

                all_error_lines = []
                for node, nf, cf, delete_flag in existing_node_data:
                    if delete_flag:
                        continue
                    node_label = node.title or f"گره {node.pk}"
                    if nf.errors:
                        all_error_lines.extend(_collect_form_errors(nf, f"گره «{node_label}»"))
                    if cf.errors:
                        all_error_lines.extend(
                            _collect_formset_errors(
                                cf,
                                f"گره «{node_label}» / فرزندان",
                                form_label_fn=lambda f, i: f.instance.title or f"فرزند {i + 1}",
                            )
                        )

                for temp_id, nf, cf in new_node_data:
                    label = f"گره جدید ({temp_id})"
                    if nf.errors:
                        all_error_lines.extend(_collect_form_errors(nf, label))
                    if cf.errors:
                        all_error_lines.extend(
                            _collect_formset_errors(
                                cf,
                                f"{label} / فرزندان",
                                form_label_fn=lambda f, i: f.instance.title or f"فرزند {i + 1}",
                            )
                        )

                _emit_error_messages(request, all_error_lines, 'ذخیره تعیین تکلیف ناموفق بود — خطاهای زیر را برطرف کنید:')
                return render(request, self.template_name, ctx)

            # ── ذخیره نهایی ── #
            for node, nf, cf, delete_flag in existing_node_data:
                if delete_flag:
                    node.delete()
                    continue
                nf.save()

                cf.is_valid()
                for form in cf.forms:
                    if not form.is_valid():
                        continue
                    if form.cleaned_data.get('DELETE', False):
                        if form.instance.pk:
                            form.instance.delete()
                        continue
                    if form.has_changed() or form.instance.pk is None:
                        child = form.save(commit=False)
                        child.disposition = disposition
                        child.parent = node
                        child.save()

            # ─ـ گره‌های جدید: ابتدا ریشه را بساز، سپس فرزندانش را ── #
            for temp_id, nf, cf in new_node_data:
                new_node = nf.save(commit=False)
                new_node.disposition = disposition
                new_node.parent = None
                new_node.save()

                children_prefix = f'node-{temp_id}-children'
                cf2 = ChildNodeFormSet(
                    request.POST, instance=new_node,
                    prefix=children_prefix,
                    queryset=EmergencyNode.objects.none(),
                )
                cf2.is_valid()
                for form in cf2.forms:
                    if not form.is_valid():
                        continue
                    if form.cleaned_data.get('DELETE', False):
                        continue
                    if form.has_changed() or form.instance.pk is None:
                        child = form.save(commit=False)
                        child.disposition = disposition
                        child.parent = new_node
                        child.save()

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
            'breadcrumb': [
                {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')},
                {'label': 'مدیریت اوردرها', 'url': reverse_lazy('dashboard:ordering:order_list')},
                {'label': 'افزودن اوردر جدید' if not order else f'ویرایش اوردر: {order.name}', 'url': ''}
            ]
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
            all_error_lines = _collect_formset_errors(
                fs,
                'تصاویر',
                form_label_fn=lambda f, i: str(f.instance.image.name) if f.instance.image else f"تصویر {i + 1}",
            )
            _emit_error_messages(request, all_error_lines, 'ذخیره تصاویر ناموفق بود:')
            return render(request, self.template_name, self._context(order, image_fs=fs))

        if action == 'save_videos':
            fs = OrderVideoFormSet(request.POST, instance=order, prefix='videos')
            if fs.is_valid():
                fs.save()
                messages.success(request, 'ویدیوها با موفقیت ذخیره شدند.')
                return redirect(redirect_url)
            all_error_lines = _collect_formset_errors(
                fs,
                'ویدیوها',
                form_label_fn=lambda f, i: str(f.instance.video.name) if f.instance.video else f"ویدیو {i + 1}",
            )
            _emit_error_messages(request, all_error_lines, 'ذخیره ویدیوها ناموفق بود:')
            return render(request, self.template_name, self._context(order, video_fs=fs))

        return redirect(redirect_url)
