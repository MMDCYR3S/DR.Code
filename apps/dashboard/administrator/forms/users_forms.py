from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

from apps.accounts.models import Profile, AuthStatusChoices

User = get_user_model()

# ===== کلاس‌های استایل مشترک ===== #
FIELD_CLASS = (
    'w-full px-4 py-2.5 border border-slate-200 rounded-lg bg-white text-slate-700 '
    'placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-c1 focus:border-c1 '
    'transition-all disabled:opacity-60'
)
CHECKBOX_CLASS = 'w-4 h-4 text-c1 bg-slate-100 border-slate-300 rounded focus:ring-c1'


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
            'class': f'{FIELD_CLASS} pr-10 text-sm py-1.5',
            'placeholder': 'جستجو بر اساس نام، شماره تماس یا کد نظام پزشکی...'
        })
    )
    role = forms.ChoiceField(
        required=False,
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': f'{FIELD_CLASS} text-sm py-1.5'})
    )
    auth_status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': f'{FIELD_CLASS} text-sm py-1.5'})
    )
    sort_by = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial='-date_joined',
        widget=forms.Select(attrs={'class': f'{FIELD_CLASS} text-sm py-1.5'})
    )


# ============================================= #
# ============== USER EDIT FORM ============== #
# ============================================= #
class UserEditForm(forms.ModelForm):
    """ فرم ویرایش اطلاعات کاربر """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'last_name': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'email': forms.EmailInput(attrs={'class': FIELD_CLASS}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
        }


# ============================================= #
# ============== PROFILE EDIT FORM ============== #
# ============================================= #
class ProfileEditForm(forms.ModelForm):
    """ فرم ویرایش پروفایل (نقش، وضعیت احراز، کد نظام و دلیل رد) """

    class Meta:
        model = Profile
        fields = ['role', 'auth_status', 'medical_code', 'rejection_reason']
        widgets = {
            'role': forms.Select(attrs={'class': FIELD_CLASS}),
            'auth_status': forms.Select(attrs={'class': FIELD_CLASS}),
            'medical_code': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'rejection_reason': forms.Textarea(attrs={'class': FIELD_CLASS, 'rows': 3}),
        }


# ============================================= #
# ============== ADD USER FORM ============== #
# ============================================= #
class AddUserForm(forms.Form):
    """ فرم ایجاد کاربر جدید توسط ادمین """

    first_name = forms.CharField(
        max_length=30, label='نام',
        widget=forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'نام'})
    )
    last_name = forms.CharField(
        max_length=30, label='نام خانوادگی',
        widget=forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'نام خانوادگی'})
    )
    email = forms.EmailField(
        label='ایمیل',
        widget=forms.EmailInput(attrs={'class': FIELD_CLASS, 'placeholder': 'example@email.com'})
    )
    phone_number = forms.CharField(
        max_length=11, label='شماره تلفن',
        validators=[RegexValidator(
            regex=r'^09\d{9}$',
            message="شماره تلفن باید با 09 شروع شده و 11 رقم باشد."
        )],
        widget=forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': '09123456789'})
    )
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={'class': FIELD_CLASS, 'placeholder': 'رمز عبور'})
    )
    medical_code = forms.CharField(
        max_length=50, label='کد نظام پزشکی', required=False,
        widget=forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'کد نظام پزشکی'})
    )
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES, label='نقش', initial='regular',
        widget=forms.Select(attrs={'class': FIELD_CLASS})
    )

    # ===== اعتبارسنجی یکتایی ===== #
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
