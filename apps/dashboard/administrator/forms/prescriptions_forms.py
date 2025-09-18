from django import forms
from django.forms import inlineformset_factory
from apps.prescriptions.models import(
    Prescription,
    PrescriptionCategory,
    PrescriptionDrug,
    PrescriptionAlias,
    PrescriptionImage,
    PrescriptionVideo
)

# ========== Prescription Filter Form ========== #
class PrescriptionFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
            'placeholder': 'جستجوی نسخه...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=PrescriptionCategory.objects.all(),
        required=False,
        label="",
        empty_label="همه دسته‌بندی‌ها",
        widget=forms.Select(attrs={
            'class': 'w-full py-2.5 px-4 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition'
        })
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'جدیدترین'),
            ('created_at', 'قدیمی‌ترین'),
            ('title', 'عنوان (الفبایی)'),
        ],
        required=False,
        label="",
        widget=forms.Select(attrs={
            'class': 'w-full py-2.5 px-4 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition'
        })
    )
    
# ========== Prescription Form ========== #
class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['title', 'category', 'access_level', 'is_active', 'detailed_description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition'}),
            'category': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'access_level': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        
        labels = {
            'title': 'عنوان اصلی نسخه',
            'category': 'دسته‌بندی',
            'access_level': 'سطح دسترسی',
            'is_active': 'فعال باشد',
            'detailed_description': 'توضیحات کامل نسخه',
        }
        
# ========== Formsets for Dependent Models ========== #
DrugFormSet = inlineformset_factory(
    Prescription, PrescriptionDrug,
    fields=('title', 'dosage', 'amount', 'instructions', 'is_combination', 'combination_group', 'order'),
    extra=1, can_delete=True,
    widgets={
        'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'نام دارو'}),
        'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'کد دارو'}),
        'dosage': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'دوز مصرف'}),
        'amount': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'تعداد'}),
        'instructions': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2}),
        'is_combination': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        'combination_group': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'گروه ترکیبی'}),
        'order': forms.NumberInput(attrs={'class': 'form-input'}),
    }
)

AliasFormSet = inlineformset_factory(Prescription, PrescriptionAlias, fields=('name', 'is_primary'), extra=1, can_delete=True)
ImageFormSet = inlineformset_factory(Prescription, PrescriptionImage, fields=('image', 'caption'), extra=1, can_delete=True)
VideoFormSet = inlineformset_factory(Prescription, PrescriptionVideo, fields=('video_url', 'title'), extra=1, can_delete=True)
