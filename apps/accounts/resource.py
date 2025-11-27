from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import User
from apps.accounts.models import Profile # مسیر پروفایل را متناسب با پروژه خود تغییر دهید

class UserExportResource(resources.ModelResource):
    # --- تعریف فیلدهای مدل User ---
    # ما به صورت دستی فیلدها را تعریف می کنیم تا کنترل کاملی روی نام ستون ها و ترتیب آنها داشته باشیم
    first_name = fields.Field(attribute='first_name', column_name='نام')
    last_name = fields.Field(attribute='last_name', column_name='نام خانوادگی')
    phone_number = fields.Field(attribute='phone_number', column_name='شماره تلفن')
    shamsi_date_joined = fields.Field(attribute='shamsi_date_joined', column_name='تاریخ عضویت شمسی')

    # --- تعریف فیلدهای مدل Profile با استفاده از رابطه ---
    # جادو اینجا اتفاق می افتد: attribute='profile__field_name'
    role = fields.Field(attribute='profile__role', column_name='نقش کاربری')
    medical_code = fields.Field(attribute='profile__medical_code', column_name='کد نظام پزشکی')
    auth_status = fields.Field(attribute='profile__auth_status', column_name='وضعیت احراز هویت')
    
    # --- فیلد سفارشی برای نمایش متن فارسی وضعیت احراز هویت ---
    auth_status_display = fields.Field(column_name='وضعیت احراز هویت (فارسی)')

    class Meta:
        model = User
        # فیلدهایی از مدل اصلی که مستقیما میخواهیم (اگر دستی تعریف نکرده بودیم)
        # fields = ('id', 'first_name', 'last_name', 'phone_number', 'shamsi_date_joined',)
        
        # مشخص کردن فیلدهایی که باید در خروجی باشند و ترتیب آنها
        export_order = (
            'id', 
            'first_name', 
            'last_name', 
            'phone_number', 
            'role', 
            'medical_code',
            'auth_status',
            'auth_status_display',
            'shamsi_date_joined',
        )
        
        # برای اینکه فقط فیلدهای تعریف شده در export_order خروجی گرفته شوند
        fields = export_order

    def dehydrate_auth_status_display(self, user):
        """
        این متد برای هر ردیف (کاربر) اجرا می شود.
        مقدار فیلد 'auth_status_display' را بر اساس مقدار فارسی آن در مدل Profile برمی گرداند.
        """
        # متد get_FOO_display به صورت خودکار توسط جنگو برای فیلدهای choices ساخته می شود
        if hasattr(user, 'profile'):
            return user.profile.get_auth_status_display()
        return "بدون پروفایل"
