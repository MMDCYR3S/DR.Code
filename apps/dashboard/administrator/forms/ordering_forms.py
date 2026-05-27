from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet, modelformset_factory
from django_ckeditor_5.widgets import CKEditor5Widget

from apps.ordering.models import (
    Order, OrderSection, SectionItem, DrugSectionItem,
    DynamicFieldGroup, DynamicFieldSubGroup, DynamicFieldItem,
    EmergencyDisposition, EmergencyNode
)
from apps.prescriptions.models.category import PrescriptionCategory
from apps.prescriptions.models.drug import Drug


# ===== Shared Styles ===== #
INPUT_CLASSES_LTR = 'w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition text-left'
INPUT_CLASSES_RTL = 'w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition text-right'
CHECKBOX_CLASSES = 'form-checkbox h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500'

# ==================================================== #
# ==================== Order Form ==================== #
# ==================================================== #
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'imp', 'condition', 'diet', 'action', 'position', 'notes', 'category', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASSES_RTL, 'placeholder': 'نام اوردر...'}),
            'imp': forms.Textarea(attrs={'class': INPUT_CLASSES_RTL, 'rows': 2}),
            'condition': forms.Textarea(attrs={'class': INPUT_CLASSES_RTL, 'rows': 2}),
            'diet': forms.Textarea(attrs={'class': INPUT_CLASSES_RTL, 'rows': 2}),
            'action': forms.Textarea(attrs={'class': INPUT_CLASSES_RTL, 'rows': 2}),
            'position': forms.Textarea(attrs={'class': INPUT_CLASSES_RTL, 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': INPUT_CLASSES_RTL, 'rows': 3}),
            'category': forms.Select(attrs={'class': INPUT_CLASSES_RTL}),
            'color': forms.Select(attrs={'class': INPUT_CLASSES_LTR}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = PrescriptionCategory.objects.all().order_by('title')


class OrderSectionForm(forms.ModelForm):
    class Meta:
        model = OrderSection
        fields = ['title', 'notes', 'is_drug_section', 'order_index', 'color']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASSES_RTL, 'placeholder': 'عنوان بخش...'}),
            'notes': forms.Textarea(attrs={'class': INPUT_CLASSES_RTL, 'rows': 1}),
            'is_drug_section': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASSES}),
            'order_index': forms.NumberInput(attrs={'class': INPUT_CLASSES_LTR}),
            'color': forms.Select(attrs={'class': INPUT_CLASSES_LTR}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_index'].required = False
        self.fields['order_index'].initial = 0

    def clean_order_index(self):
        value = self.cleaned_data.get('order_index')
        if value is None:
            return 0
        return value


class SectionItemForm(forms.ModelForm):
    class Meta:
        model = SectionItem
        fields = ['text', 'notes', 'order_index']
        widgets = {
            'text': forms.Textarea(attrs={'class': INPUT_CLASSES_LTR + ' item-name-input', 'rows': 1, 'placeholder': 'متن آیتم...'}),
            'notes': forms.Textarea(attrs={'class': INPUT_CLASSES_RTL, 'rows': 1, 'placeholder': 'توضیحات...'}),
            'order_index': forms.NumberInput(attrs={'class': INPUT_CLASSES_LTR}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_index'].required = False
        self.fields['order_index'].initial = 0

    def clean_order_index(self):
        value = self.cleaned_data.get('order_index')
        if value is None:
            return 0
        return value


class DrugSectionItemForm(forms.ModelForm):
    class Meta:
        model = DrugSectionItem
        fields = ['drug', 'notes', 'order_index']
        widgets = {
            'drug': forms.Select(attrs={'class': INPUT_CLASSES_LTR + ' select2-drug-search item-name-input', 'data-placeholder': 'جستجو...'}),
            'notes': forms.Textarea(attrs={'class': INPUT_CLASSES_RTL, 'rows': 1, 'placeholder': 'توضیحات...'}),
            'order_index': forms.NumberInput(attrs={'class': INPUT_CLASSES_LTR}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_index'].required = False
        self.fields['order_index'].initial = 0
        self.fields['drug'].queryset = Drug.objects.all()

    def clean_order_index(self):
        value = self.cleaned_data.get('order_index')
        if value is None:
            return 0
        return value


# ── Custom BaseInlineFormSet که فرم‌های کاملاً خالی رو valid می‌کنه ──
class BaseOrderSectionFormSet(BaseInlineFormSet):
    """
    فرم‌هایی که title ندارن و instance جدید هستن رو به عنوان empty در نظر می‌گیره
    تا Django اونا رو skip کنه به جای اینکه error بده.
    """
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        return form

    def full_clean(self):
        super().full_clean()
        # فرم‌های extra که title ندارن رو از errors پاک کن
        for form in self.forms:
            if not form.instance.pk and not form.cleaned_data.get('title'):
                form._errors = {}
                form.cleaned_data = {}


OrderSectionFormSet = inlineformset_factory(
    Order,
    OrderSection,
    form=OrderSectionForm,
    formset=BaseOrderSectionFormSet,
    extra=0,
    can_delete=True,
)

SectionItemFormSet = inlineformset_factory(
    OrderSection,
    SectionItem,
    form=SectionItemForm,
    extra=0,
    can_delete=True,
)

DrugSectionItemFormSet = inlineformset_factory(
    OrderSection,
    DrugSectionItem,
    form=DrugSectionItemForm,
    extra=0,
    can_delete=True,
)

# ====================================================== #
# ==================== Dynamic Form ==================== #
# ====================================================== #
class DynamicFieldGroupForm(forms.ModelForm):
    class Meta:
        model = DynamicFieldGroup
        fields = ['title', 'order_index', 'color']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASSES_RTL, 'placeholder': 'عنوان گروه...'}),
            'order_index': forms.NumberInput(attrs={'class': INPUT_CLASSES_LTR}),
            'color': forms.Select(attrs={'class': INPUT_CLASSES_LTR}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_index'].required = False
        self.fields['order_index'].initial = 0

    def clean_order_index(self):
        return self.cleaned_data.get('order_index') or 0


class DynamicFieldSubGroupForm(forms.ModelForm):
    class Meta:
        model = DynamicFieldSubGroup
        fields = ['title', 'order_index']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASSES_RTL, 'placeholder': 'عنوان زیرگروه...'}),
            'order_index': forms.NumberInput(attrs={'class': INPUT_CLASSES_LTR}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_index'].required = False
        self.fields['order_index'].initial = 0

    def clean_order_index(self):
        return self.cleaned_data.get('order_index') or 0


class DynamicFieldItemForm(forms.ModelForm):
    class Meta:
        model = DynamicFieldItem
        fields = ['key', 'value', 'order_index']
        widgets = {
            'key': forms.TextInput(attrs={'class': INPUT_CLASSES_RTL, 'placeholder': 'تعریف...'}),
            'value': forms.Textarea(attrs={'class': INPUT_CLASSES_RTL, 'rows': 2, 'placeholder': 'توضیحات...'}),
            'order_index': forms.NumberInput(attrs={'class': INPUT_CLASSES_LTR}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_index'].required = False
        self.fields['order_index'].initial = 0

    def clean_order_index(self):
        return self.cleaned_data.get('order_index') or 0


class SkipEmptyFormSet(BaseInlineFormSet):
    empty_field: str = 'title'

    def full_clean(self):
        super().full_clean()
        for form in self.forms:
            if not form.instance.pk and not form.cleaned_data.get(self.empty_field):
                form._errors = {}
                form.cleaned_data = {}

class BaseGroupFormSet(SkipEmptyFormSet):
    empty_field = 'title'

class BaseSubGroupFormSet(SkipEmptyFormSet):
    empty_field = 'title'


class BaseItemFormSet(SkipEmptyFormSet):
    empty_field = 'key'


DynamicFieldGroupFormSet = inlineformset_factory(
    Order,
    DynamicFieldGroup,
    form=DynamicFieldGroupForm,
    formset=BaseGroupFormSet,
    extra=0,
    can_delete=True,
)

DynamicFieldSubGroupFormSet = inlineformset_factory(
    DynamicFieldGroup,
    DynamicFieldSubGroup,
    form=DynamicFieldSubGroupForm,
    formset=BaseSubGroupFormSet,
    extra=0,
    can_delete=True,
)

DynamicFieldItemFormSet = inlineformset_factory(
    DynamicFieldSubGroup,
    DynamicFieldItem,
    form=DynamicFieldItemForm,
    formset=BaseItemFormSet,
    extra=0,
    can_delete=True,
)

# ====================================================== #
# ============= Emergency Disposition Forms ============ #
# ====================================================== #
class EmergencyDispositionForm(forms.ModelForm):
    class Meta:
        model = EmergencyDisposition
        fields = ['title', 'color', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASSES_RTL,
                'placeholder': 'عنوان تعیین تکلیف...'
            }),
            'color': forms.Select(attrs={'class': INPUT_CLASSES_LTR}),
            'notes': forms.Textarea(attrs={
                'class': INPUT_CLASSES_RTL,
                'rows': 2,
                'placeholder': 'توضیحات...'
            }),
        }


class EmergencyRootNodeForm(forms.ModelForm):
    """گره‌های ریشه (parent=None)"""
    class Meta:
        model = EmergencyNode
        fields = ['title', 'color', 'order_index']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASSES_RTL,
                'placeholder': 'عنوان گره...'
            }),
            'color': forms.Select(attrs={'class': INPUT_CLASSES_LTR}),
            'order_index': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_index'].required = False
        self.fields['order_index'].initial = 0

    def clean_order_index(self):
        return self.cleaned_data.get('order_index') or 0


class EmergencyChildNodeForm(forms.ModelForm):
    """گره‌های فرزند"""
    class Meta:
        model = EmergencyNode
        fields = ['title', 'content', 'color', 'order_index']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASSES_RTL,
                'placeholder': 'عنوان فرزند...'
            }),
            'content': CKEditor5Widget(
                attrs={
                    'class': 'django_ckeditor_5',
                },
                config_name='extends',
            ),
            'color': forms.Select(attrs={'class': INPUT_CLASSES_LTR}),
            'order_index': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_index'].required = False
        self.fields['order_index'].initial = 0
        self.fields['content'].required = False

    def clean_order_index(self):
        return self.cleaned_data.get('order_index') or 0


class SkipEmptyNodeFormSet(BaseInlineFormSet):
    def full_clean(self):
        super().full_clean()
        for form in self.forms:
            if not form.instance.pk and not form.cleaned_data.get('title'):
                form._errors = {}
                form.cleaned_data = {}


ChildNodeFormSet = inlineformset_factory(
    EmergencyNode,
    EmergencyNode,
    form=EmergencyChildNodeForm,
    formset=SkipEmptyNodeFormSet,
    extra=0,
    can_delete=True,
    fk_name='parent',
)
