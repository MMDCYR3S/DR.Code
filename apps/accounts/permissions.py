from rest_framework import permissions
from django.contrib.auth.mixins import UserPassesTestMixin
from apps.subscriptions.models import FeatureType

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

# ======== HAS PRESCRIPTION ACCESS ======== #
class HasPrescriptionAccess(permissions.BasePermission):
    """
    بررسی دسترسی به نسخه‌های پریمیوم
    """
    message = "برای دسترسی به نسخه‌های پریمیوم نیاز به خرید اشتراک مناسب دارید."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            self.message = "لطفاً ابتدا وارد حساب کاربری خود شوید."
            return False
            
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        return request.user.has_feature_access(FeatureType.PRESCRIPTION_ACCESS)
    
    def has_object_permission(self, request, view, obj):
        """
        بررسی دسترسی به یک نسخه خاص
        """
        # اگر نسخه FREE است، همه دسترسی دارند
        if hasattr(obj, 'access_level') and obj.access_level == 'FREE':
            return True
            
        # اگر نسخه PREMIUM است، باید اشتراک داشته باشد
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        return request.user.has_feature_access(FeatureType.PRESCRIPTION_ACCESS)

# ======== HAS ORDERING ACCESS ======== #
class HasOrderingAccess(permissions.BasePermission):
    """
    بررسی دسترسی به سیستم سفارش‌گذاری
    """
    message = "برای ثبت سفارش نیاز به خرید اشتراک مناسب دارید."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            self.message = "لطفاً ابتدا وارد حساب کاربری خود شوید."
            return False
            
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        return request.user.has_feature_access(FeatureType.ORDERING)

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
        
        return False

# ======= Has Admin Access Permission ======= #
class HasAdminAccessPermission(UserPassesTestMixin):
    """بررسی اینکه آیا کاربر ادمین هست یا خیر"""
    
    def test_func(self):
        user = self.request.user
        return (
            user.is_authenticated and (
                user.is_staff or
                user.is_superuser or
                getattr(user.profile, "role", None) == "admin"
            )
        )

# ======== HAS FEATURE PERMISSION (داینامیک) ======== #
class HasFeaturePermission(permissions.BasePermission):
    """
    پرمیشن داینامیک برای بررسی دسترسی به یک ویژگی خاص (Feature).
    ویو مربوطه باید یک اتربیوت به نام `required_feature` داشته باشد.
    
    مثال استفاده:
    class MyView(APIView):
        required_feature = FeatureType.PRESCRIPTION_ACCESS
        permission_classes = [HasFeaturePermission]
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            self.message = "لطفاً ابتدا وارد حساب کاربری خود شوید."
            return False
            
        required_feature = getattr(view, 'required_feature', None)
        
        if not required_feature:
            return True
            
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        has_access = request.user.has_feature_access(required_feature)
        
        if not has_access:
            feature_name_map = {
                FeatureType.PRESCRIPTION_ACCESS: "نسخه‌های پریمیوم",
                FeatureType.ORDERING: "سیستم سفارش‌گذاری",
            }
            feature_name = feature_name_map.get(required_feature, "این بخش")
            self.message = f"برای دسترسی به {feature_name} نیاز به خرید اشتراک مناسب دارید."
            
        return has_access
