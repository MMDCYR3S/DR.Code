from django import forms
from django.contrib.auth import get_user_model

from apps.accounts.models import Profile, AuthStatusChoices

User = get_user_model()

# ============================================= #
# ============== USER SEARCH FORM ============== #
# ============================================= #
class UserSearchForm(forms.Form):
    """ فرم جستجو و فیلتر کاربران """
    
    ROLE_CHOICES = [
        ('', 'همه نقش‌ها'),
        ('visitor', 'بازدیدکننده'),
        ('regular', 'کاربر عادی'),
        ('premium', 'کاربر ویژه'),
        ('admin', 'ادمین'),
    ]
    
    STATUS_CHOICES = [
        ('', 'همه وضعیت‌ها'),
        (AuthStatusChoices.APPROVED.value, 'تایید شده'),
        (AuthStatusChoices.REJECTED.value, 'رد شده'),
        (AuthStatusChoices.PENDING.value, 'در انتظار تایید'),
    ]
    
    SORT_CHOICES = [
        ('-date_joined', 'جدیدترین'),
        ('date_joined', 'قدیمی‌ترین'),
        ('first_name', 'الفبایی (الف تا ی)'),
        ('-first_name', 'الفبایی (ی تا الف)'),
    ]
    
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-10 pr-4 py-2 border rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-300',
            'placeholder': 'جستجو بر اساس نام، شماره تماس یا کد نظام پزشکی...'
        })
    )
    
    role = forms.ChoiceField(
        required=False,
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full py-2 px-4 border rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-300'
        })
    )
    
    auth_status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full py-2 px-4 border rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-300'
        })
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial='-date_joined',
        widget=forms.Select(attrs={
            'class': 'w-full py-2 px-4 border rounded-lg bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-300'
        })
    )
    
# ============================================= #
# ============== USER EDIT FORM ============== #
# ============================================= #
class UserEditForm(forms.ModelForm):
    """فرم ویرایش کاربر"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'
            })
        }
        
# ============================================= #
# ============== PROFILE EDIT FORM ============== #
# ============================================= #
class ProfileEditForm(forms.ModelForm):
    """فرم ویرایش پروفایل کاربر"""
    
    class Meta:
        model = Profile
        fields = ['role', 'auth_status', 'medical_code', 'rejection_reason']
        widgets = {
            'role': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'auth_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'medical_code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'rejection_reason': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3
            })
        }
