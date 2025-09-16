from rest_framework import permissions
from apps.accounts.models import AuthStatusChoices

# ======== IS PRESCRIPTION ACCESSIBLE ======== #
class IsPrescriptionAccessible(permissions.BasePermission):
    """
    بررسی دسترسی به نسخه بر اساس سطح دسترسی
    """
    message = "برای دسترسی به این نسخه نیاز به اشتراک ویژه دارید."
    
    def has_object_permission(self, request, view, obj):
        # اگر نسخه رایگان است
        if obj.access_level == 'free':
            return True
            
        # اگر نسخه ویژه است، کاربر باید تایید هویت شده و اشتراک فعال داشته باشد
        if obj.access_level == 'premium':
            if not request.user.is_authenticated:
                return False
            
            # بررسی تایید هویت
            if not hasattr(request.user, 'profile') or not request.user.profile.auth_status == AuthStatusChoices.APPROVED.value:
                self.message = "حساب کاربری شما تایید نشده است."
                return False
            
            # # بررسی اشتراک فعال
            # if not hasattr(request.user, 'subscription') or not request.user.subscription.is_active:
            #     self.message = "برای دسترسی به این نسخه نیاز به اشتراک فعال دارید."
            #     return False
        
        return True

class IsVerifiedUser(permissions.BasePermission):
    """
    فقط کاربران تایید شده می‌توانند دسترسی داشته باشند
    """
    message = "حساب کاربری شما تایید نشده است."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'profile') and request.user.profile.is_verified
