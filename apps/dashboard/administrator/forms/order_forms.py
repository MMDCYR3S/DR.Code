from django import forms
from django.db.models import Q

from apps.ordering.models import Order
from apps.prescriptions.models import PrescriptionCategory
from apps.ordering.models import TailwindColor


class OrderFilterForm(forms.Form):
    """فرم فیلتر لیست Order"""
    
    search = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
            'placeholder': 'Search in name, imp, condition, diet, action, position...',
            'dir': 'ltr',
            'autocomplete': 'off'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=PrescriptionCategory.objects.all(),
        required=False,
        label='',
        empty_label='همه',
        widget=forms.Select(attrs={
            'class': 'w-full py-2.5 px-4 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
            'dir': 'ltr'
        })
    )
    
    color = forms.ChoiceField(
        choices=[('', 'همه رنگ‌ها')] + list(TailwindColor.choices),
        required=False,
        label='',
        widget=forms.Select(attrs={
            'class': 'w-full py-2.5 px-4 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
            'dir': 'ltr'
        })
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('', 'پیش‌فرض (جدیدترین‌ها)'),
            ('-created_at', 'جدیدترین'),
            ('created_at', 'قدیمی‌ترین'),
            ('name', 'نام (A-Z)'),
            ('-name', 'نام (Z-A)'),
        ],
        required=False,
        label='',
        widget=forms.Select(attrs={
            'class': 'w-full py-2.5 px-4 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
            'dir': 'ltr'
        })
    )


class OrderForm(forms.ModelForm):
    """فرم ایجاد و ویرایش Order"""
    
    class Meta:
        model = Order
        fields = ['name', 'imp', 'condition', 'diet', 'action', 'position', 'notes', 'category', 'color']
        labels = {
            'name': 'Name',
            'imp': 'IMP',
            'condition': 'Condition',
            'diet': 'Diet',
            'action': 'Action',
            'position': 'Position',
            'notes': 'Notes',
            'category': 'Category',
            'color': 'Color',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
                'placeholder': 'Enter order name',
                'dir': 'ltr',
                'required': True
            }),
            'imp': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
                'placeholder': 'Enter IMP',
                'dir': 'ltr'
            }),
            'condition': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
                'placeholder': 'Enter condition',
                'dir': 'ltr'
            }),
            'diet': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
                'placeholder': 'Enter diet',
                'dir': 'ltr'
            }),
            'action': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
                'placeholder': 'Enter action',
                'dir': 'ltr'
            }),
            'position': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
                'placeholder': 'Enter position',
                'dir': 'ltr'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
                'placeholder': 'یادداشت‌های اضافی را وارد کنید (اختیاری)',
                'rows': 4,
                'dir': 'rtl'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'dir': 'ltr',
                'required': True
            }),
            'color': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400',
                'dir': 'ltr',
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تنظیم queryset برای category
        self.fields['category'].queryset = PrescriptionCategory.objects.all()
        self.fields['category'].empty_label = 'Select Category'
        
        # تنظیم choices برای color
        self.fields['color'].choices = [('', 'Select Color')] + list(TailwindColor.choices)
