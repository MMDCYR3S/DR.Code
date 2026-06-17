from django import forms
from apps.prescriptions.models import Drug

class DrugForm(forms.ModelForm):
    class Meta:
        model = Drug
        fields = ['title', 'code', 'is_for_order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'نام دارو را وارد کنید'
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'کد دارو را وارد کنید (اختیاری)'
            }),
            'is_for_order': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2 cursor-pointer',
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'نام دارو'
        self.fields['code'].label = 'کد دارو'
        self.fields['code'].required = False
        self.fields['is_for_order'].label = 'داروی اوردری است؟'
        self.fields['is_for_order'].required = False
