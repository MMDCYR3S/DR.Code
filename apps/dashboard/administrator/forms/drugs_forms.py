from django import forms
from apps.prescriptions.models import Drug

INPUT_CLASS = (
    'w-full px-4 py-2.5 border border-slate-200 rounded-lg '
    'focus:outline-none focus:ring-2 focus:ring-c1 focus:border-c1 transition-colors'
)


class DrugForm(forms.ModelForm):
    class Meta:
        model = Drug
        fields = ['title', 'code', 'is_for_order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'نام دارو را وارد کنید',
            }),
            'code': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'کد دارو را وارد کنید (اختیاری)',
            }),
            'is_for_order': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-c1 bg-slate-100 border-slate-300 rounded focus:ring-c1 focus:ring-2 cursor-pointer',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'نام دارو'
        self.fields['code'].label = 'کد دارو'
        self.fields['code'].required = False
        self.fields['is_for_order'].label = 'داروی اوردری است؟'
        self.fields['is_for_order'].required = False
