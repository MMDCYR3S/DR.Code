from rest_framework import permissions
from apps.accounts.models import AuthStatusChoices

class IsOrderAccessible(permissions.BasePermission):
    """
    کنترل دسترسی به Order.
    - همه می‌توانند Order را ببینند اما برای دسترسی به جزئیات باید اشتراک داشته باشند.
    """
    message = "شما اجازه دسترسی به این محتوا را ندارید."

    def has_object_permission(self, request, view, obj):
        user = request.user
                
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return True

        # برای دسترسی به Order، کاربر باید احراز هویت شده باشد
        if not user.is_authenticated:
            self.message = "برای دسترسی به این محتوا باید وارد حساب کاربری خود شوید."
            return False

        # بررسی تایید پروفایل
        profile_approved = hasattr(user, 'profile') and user.profile.auth_status == AuthStatusChoices.APPROVED.value
        if not profile_approved:
            self.message = "حساب کاربری شما هنوز تایید نشده است. لطفا منتظر بمانید."
            return False
        
        # ادمین‌ها دسترسی کامل دارند
        if user.profile.role == "admin":
            return True
        
        # کاربران عادی بدون اشتراک دسترسی ندارند
        if user.profile.role == "regular":
            self.message = "برای دسترسی به Order باید اشتراک بخرید"
            return False
        elif user.profile.role == "visitor":
            self.message = "برای دسترسی به Order باید ابتدا ثبت نام کرده و اشتراک خریداری کنید."
            return False

        # بررسی اشتراک فعال
        has_active_sub = user.has_active_membership()
        if not has_active_sub:
            self.message = "برای دسترسی به این Order نیاز به اشتراک فعال دارید."
            return False
        
        # بررسی دسترسی به ویژگی Ordering
        from apps.subscriptions.models import FeatureType
        if not user.has_feature_access(FeatureType.ORDERING):
            self.message = "برای دسترسی به سیستم سفارش‌گذاری نیاز به خرید اشتراک مناسب دارید."
            return False
        
        return True
