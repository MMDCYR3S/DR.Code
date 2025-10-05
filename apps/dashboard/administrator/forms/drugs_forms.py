from django import forms
from apps.prescriptions.models import Drug

class DrugForm(forms.ModelForm):
    class Meta:
        model = Drug
        fields = ['title', 'code']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'نام دارو را وارد کنید'
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'کد دارو را وارد کنید (اختیاری)'
            }),
            'groups': forms.SelectMultiple(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'نام دارو'
        self.fields['code'].label = 'کد دارو'
        self.fields['code'].required = False
