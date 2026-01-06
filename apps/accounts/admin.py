from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export.admin import ImportExportModelAdmin

from .resource import UserExportResource
from .models import Profile, User, AuthenticationDocument, User

# برای نمایش و ویرایش پروفایل در همان صفحه یوزر
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'پروفایل کاربر'
    fk_name = 'user'

@admin.register(User)
class UserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    # اتصال Resource سفارشی به ادمین
    resource_class = UserExportResource
    
    # استفاده از اینلاین برای پروفایل
    inlines = (ProfileInline,)

    # فیلدهای نمایش داده شده در لیست کاربران
    list_display = (
        'phone_number', 
        'first_name', 
        'last_name', 
        'get_user_role', # متد سفارشی برای نمایش نقش
        'get_auth_status', # متد سفارشی برای نمایش وضعیت احراز
        'is_staff', 
        'shamsi_date_joined'
    )
    
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'profile__role', 'email','profile__auth_status')
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email', 'is_phone_verified')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌های مهم', {'fields': ('last_login', 'date_joined')}),
    )
    
    search_fields = ('phone_number', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)

    # متدهای سفارشی برای نمایش اطلاعات پروفایل در لیست
    @admin.display(description='نقش کاربری')
    def get_user_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display() # نمایش مقدار فارسی
        return '-'

    @admin.display(description='وضعیت احراز هویت')
    def get_auth_status(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_auth_status_display() # نمایش مقدار فارسی
        return '-'

    
    
@admin.register(AuthenticationDocument)
class AuthenticationDocumentAdmin(admin.ModelAdmin):
    pass
