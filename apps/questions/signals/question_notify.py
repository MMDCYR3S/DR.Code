from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from ..models import Question
from apps.notifications.models import Notification

User = get_user_model()

@receiver(post_save, sender=Question)
def create_question_notification(sender, instance, created, **kwargs):
    """
    یک سیگنال برای ایجاد اعلان پس از ثبت شدن یک سوال توسط کاربر ویژه
    اساس کار اینگونه است که اگر کاربر ویژه سوال را ارسال کرد، یک اعلان به سمت
    ادمین ارسال می شود و اگر که ادمین یک پاسخ به سوال داد، یک اعلان و همچنین یک 
    ایمیل باید به سمت کاربرارسال شود که به سوال او پاسخ داده شد.
    """
    
    if created:
        admin_users = User.objects.filter(profile__role="admin", is_active=True)

        if not admin_users.exists():
            return None
        
        question_user = instance.user.full_name
        message = f"سؤال جدیدی از طرف {question_user} ثبت گردید."
        
        content_type = ContentType.objects.get_for_model(Question)
        
        notifications_to_create = [
             Notification(
                recipient=admin_user,
                message=message,
                content_type=content_type,
                object_id=instance.pk,
                is_read=False
            )
            for admin_user in admin_users
        ]
        
        Notification.objects.bulk_create(notifications_to_create)
        
    elif not created and instance.is_answered and instance.answered_by:
        # اگر سوال پرسیده شده بود و ادمین پساخ رو ثبت کرد
        
        content_type = ContentType.objects.get_for_model(instance)
        
        existing_notification = Notification.objects.filter(
            recipient=instance.user,
            content_type=content_type,
            object_id=instance.pk,
            message__contains="پاسخ سوال شما داده شد",
            is_read=False
        ).exists()
        
        if not existing_notification:
            prescription_title = instance.prescription.title
            message = f"پاسخ سوال شما در مورد نسخه «{prescription_title}» داده شد."
            
            Notification.objects.create(
                recipient=instance.user,
                message=message,
                content_type=content_type,
                object_id=instance.pk,
                is_read=False
            )
        