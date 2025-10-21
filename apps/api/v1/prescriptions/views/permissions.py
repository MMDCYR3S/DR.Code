from rest_framework import permissions
from apps.accounts.models import AuthStatusChoices

class IsPrescriptionAccessible(permissions.BasePermission):
    """
    کلاس دسترسی یکپارچه برای نسخه‌ها.
    - به همه اجازه دیدن نسخه‌های رایگان را می‌دهد.
    - برای نسخه‌های ویژه، کاربر باید تایید هویت شده و اشتراک فعال داشته باشد.
    """
    message = "شما اجازه دسترسی به این محتوا را ندارید."

    def has_object_permission(self, request, view, obj):
        user = request.user
                
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return True

        if obj.access_level == 'FREE':
            return True
        
        elif obj.access_level == 'PREMIUM':
            if not user.is_authenticated:
                self.message = "برای دسترسی به این محتوا باید وارد حساب کاربری خود شوید."
                return False

            profile_approved = hasattr(user, 'profile') and user.profile.auth_status == AuthStatusChoices.APPROVED.value
            if not profile_approved:
                self.message = "حساب کاربری شما هنوز تایید نشده است. لطفا منتظر بمانید."
                return False
            
            if user.profile.role == "admin":
                return True
            
            if user.profile.role == "regular":
                self.message = "برای دسترسی به محتوای ویژه باید اشتراک بخرِید"
                return False
            elif user.profile.role == "visitor":
                self.message = "برای دسترسی به محتوای ویژه باید ابتدا ثبت نام کرده و اشتراک خریداری کنید."
                return False

            has_active_sub = user.has_active_membership()
            if not has_active_sub:
                self.message = "برای دسترسی به این نسخه نیاز به اشتراک فعال دارید."
                return False
            
            return True
        return False