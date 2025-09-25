from django import forms
from django.forms import inlineformset_factory
from apps.prescriptions.models import(
    Prescription,
    PrescriptionCategory,
    Drug,
    PrescriptionAlias,
    PrescriptionImage,
    PrescriptionVideo,
    PrescriptionDrug
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
    """ فرم برای ایجاد و ویرایش نسخه """
    
    class Meta:
        model = Prescription
        fields = ['title', 'category', 'access_level', 'is_active', 'detailed_description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
                'placeholder': 'عنوان نسخه را وارد کنید'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
            'access_level': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600'
            }),
        }
        
        labels = {
            'title': 'عنوان اصلی نسخه',
            'category': 'دسته‌بندی',
            'access_level': 'سطح دسترسی',
            'is_active': 'فعال باشد',
            'detailed_description': 'توضیحات کامل نسخه',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

# ========== PrescriptionDrug Inline Form ========== #
class PrescriptionDrugForm(forms.ModelForm):
    """ فرم مربوط به جزئیات هر دارو در نسخه """
    
    class Meta:
        model = PrescriptionDrug
        fields = ['drug', 'dosage', 'amount', 'instructions', 'is_combination', 'order']
        widgets = {
            'drug': forms.HiddenInput(),
            'dosage': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'مثال: قرص صبح و شب بعد از غذا'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-input w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-400',
                'placeholder': 'تعداد',
                'min': 1,
                'value': 1
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-textarea w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-400',
                'rows': 3,
                'placeholder': 'توضیحات اضافی در مورد نحوه مصرف دارو'
            }),
            'is_combination': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input w-full px-3 py-2 border border-slate-300 rounded-lg',
                'min': 1
            }),
        }
        labels = {
            'drug': 'دارو',
            'dosage': 'دوز و نحوه مصرف',
            'amount': 'مقدار/تعداد',
            'instructions': 'توضیحات اضافی',
            'is_combination': 'دارو ترکیبی است؟',
            'order': 'ترتیب نمایش'
        }

# ========== Formsets for Dependent Models ========== #
PrescriptionDrugFormSet = inlineformset_factory(
    Prescription,
    PrescriptionDrug,
    form=PrescriptionDrugForm,
    extra=0,
    min_num=0,
    validate_min=False,
    can_delete=True,
    widgets={
        'DELETE': forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-4 w-4 text-red-600'
        })
    }
)

AliasFormSet = inlineformset_factory(
    Prescription, 
    PrescriptionAlias, 
    fields=('name', 'is_primary'), 
    extra=1, 
    can_delete=True,
    widgets={
        'name': forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg',
            'placeholder': 'نام جایگزین'
        }),
        'is_primary': forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-4 w-4 text-blue-600'
        }),
        'DELETE': forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-4 w-4 text-red-600'
        })
    }
)

ImageFormSet = inlineformset_factory(
    Prescription, 
    PrescriptionImage, 
    fields=('image', 'caption'), 
    extra=1, 
    can_delete=True,
    widgets={
        'image': forms.FileInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg',
            'accept': 'image/*'
        }),
        'caption': forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg',
            'placeholder': 'کپشن تصویر'
        }),
        'DELETE': forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-4 w-4 text-red-600'
        })
    }
)

VideoFormSet = inlineformset_factory(
    Prescription, 
    PrescriptionVideo, 
    fields=('video_url', 'title', 'description'), 
    extra=1, 
    can_delete=True,
    widgets={
        'video_url': forms.URLInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg',
            'placeholder': 'https://www.aparat.com/...'
        }),
        'title': forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg',
            'placeholder': 'عنوان ویدیو'
        }),
        'description': forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg',
            'rows': 2,
            'placeholder': 'توضیحات ویدیو'
        }),
        'DELETE': forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-4 w-4 text-red-600'
        })
    }
)