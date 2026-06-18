from django import forms
from apps.subscriptions.models import Feature, Membership, Plan

class FeatureForm(forms.ModelForm):
    class Meta:
        model = Feature
        fields = ['name', 'feature_type', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200',
                'placeholder': 'مثال: دانلود فایل PDF'
            }),
            'feature_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200',
                'placeholder': 'توضیحات (اختیاری)',
                'rows': 3
            }),
        }
        labels = {
            'name': 'نام ویژگی',
            'feature_type': 'نوع ویژگی',
            'description': 'توضیحات',
            'is_active': 'فعال'
        }

class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ['title', 'description', 'features', 'is_active'] 
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200',
                'placeholder': 'مثال: پریمیوم'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200',
                'placeholder': 'توضیحات درباره نوع اشتراک',
                'rows': 3
            }),
            'features': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200',
                'size': '4'
            }),
        }

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['membership', 'name', 'duration_days', 'price', 'is_active']
        widgets = {
            'membership': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200',
                'placeholder': 'مثال: بسته ۱ ماهه'
            }),
            'duration_days': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200',
                'placeholder': '30'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200',
                'placeholder': 'قیمت به ریال'
            }),
        }