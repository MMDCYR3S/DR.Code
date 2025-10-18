from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

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

# ================================================ #
# ============== PROFILE EDIT FORM ============== #
# ================================================ #
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['role', 'auth_status']
        widgets = {
            'role': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'auth_status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            })
        }

# ============================================= #
# ============== ADD USER FORM ============== #
# ============================================= #
class AddUserForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
        label='نام',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'نام'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        label='نام خانوادگی',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'نام خانوادگی'
        })
    )
    
    email = forms.EmailField(
        label='ایمیل',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'example@email.com'
        })
    )
    
    phone_number = forms.CharField(
        max_length=11,
        label='شماره تلفن',
        validators=[RegexValidator(
            regex=r'^09\d{9}$',
            message="شماره تلفن باید با 09 شروع شده و 11 رقم باشد."
        )],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '09123456789'
        })
    )
    
    password = forms.CharField(
        label='پسورد',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'پسورد'
        })
    )
    
    medical_code = forms.CharField(
        max_length=50,
        label='کد نظام پزشکی',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'کد نظام پزشکی'
        })
    )
    
    role = forms.ChoiceField(
        choices=[
            ('regular', 'کاربر عادی'),
            ('visitor', 'بازدیدکننده'),
            ('premium', 'کاربر ویژه'),
            ('admin', 'ادمین')
        ],
        label='نقش',
        initial='regular',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("ایمیل وارد شده تکراری است.")
        return email
        
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("شماره تلفن وارد شده تکراری است.")
        return phone_number
