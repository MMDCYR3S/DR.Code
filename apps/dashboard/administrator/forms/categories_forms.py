from django import forms
from apps.prescriptions.models import PrescriptionCategory

# ====== TAILWIND COLOR CHOICES ====== #
TAILWIND_COLOR_CHOICES = [
    ('', 'یک رنگ انتخاب کنید...'),
    ('bg-red-500', 'قرمز'),
    ('bg-orange-500', 'نارنجی'),
    ('bg-amber-500', 'کهربایی'),
    ('bg-yellow-400', 'زرد'),
    ('bg-lime-500', 'لیمویی'),
    ('bg-green-500', 'سبز'),
    ('bg-emerald-500', 'زمردی'),
    ('bg-teal-500', 'سبز دودی'),
    ('bg-cyan-500', 'فیروزه‌ای'),
    ('bg-sky-500', 'آبی آسمانی'),
    ('bg-blue-500', 'آبی'),
    ('bg-indigo-500', 'نیلی'),
    ('bg-violet-500', 'بنفش'),
    ('bg-purple-500', 'ارغوانی'),
    ('bg-fuchsia-500', 'سرخابی'),
    ('bg-pink-500', 'صورتی'),
    ('bg-rose-500', 'گلی'),
    ('bg-slate-500', 'خاکستری'),
    ('bg-gray-700', 'دودی'),
]

# ========== CATEGORY FORM ========== #
class CategoryForm(forms.ModelForm):
    """ فرم برای ایجاد و ویرایش دسته‌بندی نسخه‌ها """
    
    color_code = forms.ChoiceField(
        choices=TAILWIND_COLOR_CHOICES,
        label="رنگ دسته‌بندی",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400'
        })
    )
    
    class Meta:
        model = PrescriptionCategory
        fields = ['title', 'color_code']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'مثال: روانپزشکی',
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400'
            })
        }
        labels = {
            'title': 'نام دسته‌بندی'
        }
