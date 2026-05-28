import json
import logging

from django.shortcuts import (
    render, redirect, get_object_or_404
)
from django.views import View
from django.views.generic import DetailView
from django.db import transaction
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q, Max, Prefetch
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.prescriptions.models import Drug
from apps.ordering.models import (
    Order, Condition, OrderSection,
    SectionItem, DrugSectionItem, DynamicFieldItem,
    DynamicFieldGroup, DynamicFieldSubGroup,
    EmergencyDisposition, EmergencyNode,
    OrderImage, OrderVideo,
    TailwindColor,
)
from ..forms import (
    # ===== Ordering ===== #
    OrderFilterForm,
    OrderForm, 
    OrderSectionFormSet, 
    SectionItemFormSet, 
    DrugSectionItemFormSet,

    # ===== Dynamic ===== #
    DynamicFieldGroupForm,
    DynamicFieldSubGroupFormSet,
    DynamicFieldItemFormSet,

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
# ==================== Order Detail List ==================== #
# =========================================================== #
class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    نمایش جزئیات کامل یک اوردر شامل:
      - اطلاعات پایه (imp, condition, diet, action, position, notes)
      - بخش‌ها (Sections) با آیتم‌های متنی، داروها و شرط‌ها
      - اطلاعات پیش‌بالینی (DynamicFieldGroups)
      - تعیین تکلیف اورژانس (EmergencyDisposition + درخت گره‌ها)
      - تصاویر (OrderImage)
      - ویدیوها (OrderVideo)
    """
 
    model = Order
    template_name = "dashboard/ordering/order_detail.html"
    context_object_name = "order"
 
    def get_queryset(self):
        """
        یک queryset بهینه با prefetch_related برای تمام روابط مورد نیاز.
        از N+1 query جلوگیری می‌کند.
        """
 
        # ── Prefetch شرط‌های آیتم‌های متنی ──────────────────────────────
        items_prefetch = Prefetch(
            "items",
            queryset=SectionItem.objects.prefetch_related(
                Prefetch(
                    "conditions",
                    queryset=Condition.objects.order_by("order_index"),
                )
            ).order_by("order_index"),
        )
 
        # ── Prefetch شرط‌های آیتم‌های دارویی ────────────────────────────
        drug_items_prefetch = Prefetch(
            "drug_items",
            queryset=DrugSectionItem.objects.select_related("drug").prefetch_related(
                Prefetch(
                    "conditions",
                    queryset=Condition.objects.order_by("order_index"),
                )
            ).order_by("order_index"),
        )
 
        # ── Prefetch بخش‌ها ──────────────────────────────────────────────
        sections_prefetch = Prefetch(
            "sections",
            queryset=OrderSection.objects.prefetch_related(
                items_prefetch,
                drug_items_prefetch,
            ).order_by("order_index"),
        )
 
        # ── Prefetch آیتم‌های KEY-VALUE پیش‌بالینی ──────────────────────
        field_items_prefetch = Prefetch(
            "items",
            queryset=DynamicFieldItem.objects.order_by("order_index"),
        )
        subgroups_prefetch = Prefetch(
            "subgroups",
            queryset=DynamicFieldSubGroup.objects.prefetch_related(
                field_items_prefetch
            ).order_by("order_index"),
        )
        dynamic_groups_prefetch = Prefetch(
            "dynamic_field_groups",
            queryset=DynamicFieldGroup.objects.prefetch_related(
                subgroups_prefetch
            ).order_by("order_index"),
        )
 
        # ── Prefetch گره‌های تعیین تکلیف (یک سطح فرزند) ────────────────
        # برای درخت چندسطحی، Template با include بازگشتی رندر می‌شود.
        children_prefetch = Prefetch(
            "children",
            queryset=EmergencyNode.objects.order_by("order_index"),
        )
        nodes_prefetch = Prefetch(
            "nodes",
            queryset=EmergencyNode.objects.prefetch_related(
                children_prefetch
            ).order_by("order_index"),
        )
        disposition_prefetch = Prefetch(
            "emergency_disposition",
            queryset=EmergencyDisposition.objects.prefetch_related(nodes_prefetch),
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

        nested_sections = []
        for i, section_form in enumerate(section_formset):
            if not section_form.instance.pk:
                continue
            item_fs = SectionItemFormSet(instance=section_form.instance, prefix=f"{section_form.prefix}-items")
            drug_fs = DrugSectionItemFormSet(instance=section_form.instance, prefix=f"{section_form.prefix}-drugs")

            # ===== مپ کردن Instance به Prefix جهت نمایش آیتم‌ها و داروها ===== #
            item_prefix_map = {f.instance.pk: f.prefix for f in item_fs if f.instance.pk}
            drug_prefix_map = {f.instance.pk: f.prefix for f in drug_fs if f.instance.pk}

            # ===== جمع‌آوری شرط‌ها جهت نمایش در حین ویرایش ===== #
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
                'conditions': list(seen_conditions.values()),
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

                messages.success(request, 'اوردر با موفقیت ذخیره شد.')
                return redirect(reverse('dashboard:ordering:order_edit', kwargs={'pk': saved_order.pk}))
            else:
                logger.error("❌ all_nested_valid is FALSE!")
                messages.error(request, 'خطا در ذخیره اوردر. لطفاً فیلدها را بررسی کنید.')
        else:
            logger.error("❌ Main form or Section formset is invalid!")
            messages.error(request, 'خطا در ذخیره اوردر. لطفاً فیلدها را بررسی کنید.')
        
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


# ====================================================== #
# ==================== Dynamic View ==================== #
# ====================================================== #
class PreClinicalManageView(View):
    template_name = 'dashboard/ordering/preclinical_form.html'

    def get_order(self, order_pk):
        return get_object_or_404(Order, pk=order_pk)

    def _build_nested(self, order, post_data=None):
        groups = DynamicFieldGroup.objects.filter(order=order).prefetch_related('subgroups__items')
        nested = []
        for group in groups:
            subgroup_fs = DynamicFieldSubGroupFormSet(
                post_data or None,
                instance=group,
                prefix=f'group-{group.pk}-subgroups'
            )
            sub_nested = []
            for sub_form in subgroup_fs:
                if not sub_form.instance.pk:
                    continue
                item_fs = DynamicFieldItemFormSet(
                    post_data or None,
                    instance=sub_form.instance,
                    prefix=f'group-{group.pk}-sub-{sub_form.instance.pk}-items'
                )
                sub_nested.append({'sub_form': sub_form, 'item_fs': item_fs})
            nested.append({
                'group': group,
                'group_form': DynamicFieldGroupForm(post_data or None, instance=group, prefix=f'group-{group.pk}'),
                'subgroup_fs': subgroup_fs,
                'sub_nested': sub_nested,
            })
        return nested

    def get(self, request, order_pk):
        order = self.get_order(order_pk)
        context = {
            'order': order,
            'nested': self._build_nested(order),
            'new_group_form': DynamicFieldGroupForm(prefix='new_group'),
            'empty_subgroup_fs': DynamicFieldSubGroupFormSet(instance=DynamicFieldGroup(), prefix='group-__gid__-subgroups'),
            'empty_item_fs': DynamicFieldItemFormSet(instance=DynamicFieldSubGroup(), prefix='group-__gid__-sub-__sid__-items'),
            'active_tab': 'preclinical',
        }
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, order_pk):
        order = self.get_order(order_pk)
        action = request.POST.get('action')

        if action == 'add_group':
            form = DynamicFieldGroupForm(request.POST, prefix='new_group')
            if form.is_valid():
                group = form.save(commit=False)
                group.order = order
                group.save()
                messages.success(request, 'گروه جدید با موفقیت اضافه شد.')
            else:
                messages.error(request, 'خطا در افزودن گروه. لطفاً عنوان را وارد کنید.')
            return redirect(reverse('dashboard:ordering:preclinical', kwargs={'order_pk': order_pk}))

        if action == 'delete_group':
            deleted, _ = DynamicFieldGroup.objects.filter(pk=request.POST.get('group_pk'), order=order).delete()
            if deleted:
                messages.success(request, 'گروه با موفقیت حذف شد.')
            return redirect(reverse('dashboard:ordering:preclinical', kwargs={'order_pk': order_pk}))

        if action == 'save_all':
            groups = DynamicFieldGroup.objects.filter(order=order)
            all_valid = True
            nested_data = []

            for group in groups:
                group_form = DynamicFieldGroupForm(request.POST, instance=group, prefix=f'group-{group.pk}')
                subgroup_fs = DynamicFieldSubGroupFormSet(request.POST, instance=group, prefix=f'group-{group.pk}-subgroups')

                gf_valid = group_form.is_valid()
                sf_valid = subgroup_fs.is_valid()

                if not gf_valid:
                    print(f"[INVALID] group_form {group.pk}: {group_form.errors}")
                if not sf_valid:
                    print(f"[INVALID] subgroup_fs {group.pk}: {subgroup_fs.errors} | non_form: {subgroup_fs.non_form_errors()}")

                if not gf_valid or not sf_valid:
                    all_valid = False

                nested_data.append({'group_form': group_form, 'subgroup_fs': subgroup_fs})

            if not all_valid:
                nested = self._build_nested(order)
                return render(request, self.template_name, {
                    'order': order,
                    'nested': nested,
                    'new_group_form': DynamicFieldGroupForm(prefix='new_group'),
                    'empty_subgroup_fs': DynamicFieldSubGroupFormSet(instance=DynamicFieldGroup(), prefix='group-__gid__-subgroups'),
                    'empty_item_fs': DynamicFieldItemFormSet(instance=DynamicFieldSubGroup(), prefix='group-__gid__-sub-__sid__-items'),
                    'active_tab': 'preclinical',
                })

            if all_valid:
                for data in nested_data:
                    data['group_form'].save()
                    
                    new_sub_temp_sids = {}
                    for sub_form in data['subgroup_fs']:
                        if not sub_form.instance.pk:
                            prefix = sub_form.prefix 
                            temp_sid = request.POST.get(f'{prefix}-temp_sid')
                            if temp_sid:
                                new_sub_temp_sids[sub_form.prefix] = temp_sid
                    
                    saved_subs = data['subgroup_fs'].save()
                    
                    for sub_form in data['subgroup_fs']:
                        sub = sub_form.instance
                        if not sub.pk or sub_form in data['subgroup_fs'].deleted_forms:
                            continue

                        temp_sid = new_sub_temp_sids.get(sub_form.prefix)
                        item_prefix = f'group-{sub.group_id}-sub-{temp_sid or sub.pk}-items'
                        item_fs = DynamicFieldItemFormSet(request.POST, instance=sub, prefix=item_prefix)
                        if item_fs.is_valid():
                            item_fs.save()
                messages.success(self.request, 'پیش‌بالینی با موفقیت ذخیره شد.')
                return redirect(reverse('dashboard:ordering:preclinical', kwargs={'order_pk': order_pk}))

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