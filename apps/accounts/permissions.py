from rest_framework import permissions

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