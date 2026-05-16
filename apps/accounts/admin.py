from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export.admin import ImportExportModelAdmin

from .resource import UserExportResource
from .models import Profile, User, AuthenticationDocument # دقت کنید User دوبار ایمپورت شده بود، یکی را پاک کردم

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
    
    # === این خط را حذف کنید ===
    # inlines = (ProfileInline,)

    # === این متد را اضافه کنید ===
    def get_inlines(self, request, obj=None):
        """
        اگر کاربر جدید است فرم پروفایل را نشان نده تا سیگنال کارش را بکند.
        اگر کاربر از قبل وجود دارد (ویرایش)، فرم پروفایل را نشان بده.
        """
        if not obj:
            return list()
        return [ProfileInline]

    # فیلدهای نمایش داده شده در لیست کاربران
    list_display = (
        'phone_number', 
        'first_name', 
        'last_name', 
        'get_user_role',
        'get_auth_status',
        'is_staff', 
        'shamsi_date_joined' # اطمینان حاصل کنید این متد در مدل شما وجود دارد
    )
    
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'profile__role', 'profile__auth_status')
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌های مهم', {'fields': ('last_login', 'date_joined')}),
    )
    
    search_fields = ('phone_number', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)

    # متدهای سفارشی برای نمایش اطلاعات پروفایل در لیست
    @admin.display(description='نقش کاربری')
    def get_user_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return '-'

    @admin.display(description='وضعیت احراز هویت')
    def get_auth_status(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_auth_status_display()
        return '-'

    
@admin.register(AuthenticationDocument)
class AuthenticationDocumentAdmin(admin.ModelAdmin):
    pass
