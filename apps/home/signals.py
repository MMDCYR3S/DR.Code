from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from apps.home.models import Contact
from apps.accounts.models import User
from apps.notifications.models import Notification


@receiver(post_save, sender=Contact)
def notify_user_on_contact_response(sender, instance, created, **kwargs):
    """
    زمانی که ادمین به پیام تماس پاسخ می‌دهد، نوتیفیکیشن برای کاربر ارسال می‌شود
    """
    if created or not instance.admin_response:
        return
    
    # پیدا کردن کاربر بر اساس شماره تلفن
    try:
        user = User.objects.get(phone_number=instance.phone)
    except User.DoesNotExist:
        return
    
    # بررسی اینکه قبلاً نوتیف ارسال نشده باشد
    content_type = ContentType.objects.get_for_model(Contact)
    if Notification.objects.filter(
        recipient=user,
        content_type=content_type,
        object_id=instance.id
    ).exists():
        return
    
    # ایجاد نوتیفیکیشن
    Notification.objects.create(
        recipient=user,
        title="پاسخ به پیام تماس شما",
        message=instance.admin_response,
        content_type=content_type,
        object_id=instance.id
    )
