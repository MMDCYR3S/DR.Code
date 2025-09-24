from rest_framework import permissions
from rest_framework_simplejwt.exceptions import InvalidToken

from django.contrib.auth.mixins import UserPassesTestMixin

# ======== HAS ACTIVE SUBSCRIPTION ======== #
class HasActiveSubscription(permissions.BasePermission):
    """
    مجوز برای کاربرانی که اشتراک فعال دارند
    """
    message = "برای استفاده از این قابلیت باید اشتراک ویژه داشته باشید."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.has_active_membership()
    
# ========== IS TOKEN JTI ACTIVE ========== #
class IsTokenJtiActive(permissions.BasePermission):
    """
    بررسی می‌کند که آیا 'jti' توکن با 'active_jti' ذخیره شده برای کاربر مطابقت دارد یا خیر.
    این کار تضمین می‌کند که فقط آخرین توکن صادر شده (آخرین نشست) فعال است.
    """
    message = 'نشست شما منقضی شده یا از دستگاه دیگری وارد شده‌اید. لطفاً دوباره وارد شوید.'

    def has_permission(self, request, view):
        user = request.user
        
        if not user or not user.is_authenticated:
            return True
        
        try:
            token_jti = request.auth.get('jti')
        except AttributeError:
            return True 
        
        active_jti = user.active_jti
        
        if token_jti and active_jti and token_jti == active_jti:
            return True
        
        print(active_jti)
        print(token_jti)
        return False

    
# ======= Has Admin Access Permission ======= #
class HasAdminAccessPermission(UserPassesTestMixin):
    """ بررسی اینکه آیا کاربر ادمین هست یا خیر """
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser