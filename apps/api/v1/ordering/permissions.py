from rest_framework import permissions
from apps.accounts.models import AuthStatusChoices
from apps.ordering.models import AccessChoices   # ← import اضافه شد


class IsOrderAccessible(permissions.BasePermission):
    """
    کنترل دسترسی به Order با در نظر گرفتن access_level.
    - اوردرهای FREE: همه کاربران احراز‌هویت‌شده و تأییدشده می‌توانند ببینند.
    - اوردرهای PREMIUM: نیاز به اشتراک فعال با ویژگی ORDERING دارد.
    """
    message = "شما اجازه دسترسی به این محتوا را ندارید."

    def has_object_permission(self, request, view, obj):
        user = request.user

        # ادمین‌های سیستم همیشه دسترسی دارند
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return True

        # احراز هویت اجباری است
        if not user.is_authenticated:
            self.message = "برای دسترسی به این محتوا باید وارد حساب کاربری خود شوید."
            return False

        # بررسی تایید پروفایل
        profile_approved = (
            hasattr(user, 'profile') and
            user.profile.auth_status == AuthStatusChoices.APPROVED.value
        )
        if not profile_approved:
            self.message = "حساب کاربری شما هنوز تایید نشده است. لطفا منتظر بمانید."
            return False

        # ادمین‌های نقش‌محور دسترسی کامل دارند
        if user.profile.role == "admin":
            return True

        # ─── اوردر رایگان: کاربر تأییدشده کافی است ───────────────────
        if obj.access_level == AccessChoices.free:
            return True

        # ─── اوردر ویژه (PREMIUM): بررسی‌های اشتراک ──────────────────
        if user.profile.role == "regular":
            self.message = "برای دسترسی به این اوردر ویژه باید اشتراک تهیه کنید."
            return False

        if user.profile.role == "visitor":
            self.message = "برای دسترسی به اوردر ویژه ابتدا ثبت‌نام کرده و اشتراک خریداری کنید."
            return False

        if not user.has_active_membership():
            self.message = "برای دسترسی به این اوردر ویژه نیاز به اشتراک فعال دارید."
            return False

        from apps.subscriptions.models import FeatureType
        if not user.has_feature_access(FeatureType.ORDERING):
            self.message = "برای دسترسی به سیستم سفارش‌گذاری نیاز به خرید اشتراک مناسب دارید."
            return False

        return True