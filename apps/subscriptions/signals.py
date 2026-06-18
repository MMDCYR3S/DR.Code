from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Subscription

@receiver([post_save, post_delete], sender=Subscription)
def clear_user_feature_cache(sender, instance, **kwargs):
    """
    بعد از ایجاد، بروزرسانی یا حذف اشتراک، کش فیچرهای کاربر را پاک می‌کند
    """
    if instance.user:
        instance.user.clear_feature_cache()
