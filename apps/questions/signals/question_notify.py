from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.apps import apps

# ایمپورت مدل Question در سطح فایل مشکلی ندارد چون سیگنال مربوط به آن است
# اما Notification را داخل تابع صدا می‌زنیم تا از چرخه جلوگیری کنیم.
from ..models import Question 

User = get_user_model()

@receiver(post_save, sender=Question)
def create_question_notification(sender, instance, created, **kwargs):
    """
    سیگنال مدیریت اعلان‌های مربوط به پرسش و پاسخ.
    اصلاحات: افزودن عنوان (Title)، جلوگیری از ایمپورت چرخشی، هندل کردن خطاهای احتمالی.
    """
    # دریافت مدل Notification به روش Lazy برای جلوگیری از Circular Import
    Notification = apps.get_model('notifications', 'Notification')
    
    if created:
        # --- حالت اول: ثبت سوال جدید (اطلاع به ادمین‌ها) ---
        
        # دریافت ادمین‌ها
        admin_users = User.objects.filter(profile__role="admin", is_active=True)
        if not admin_users.exists():
            return

        # نام کاربر (با هندل کردن حالتی که متد full_name وجود نداشته باشد)
        question_user = getattr(instance.user, 'full_name', instance.user.username)
        
        # متن و عنوان پیام
        title = "پرسش جدید"
        message = f"سؤال جدیدی از طرف {question_user} ثبت گردید."
        
        content_type = ContentType.objects.get_for_model(Question)
        
        notifications_to_create = []
        for admin_user in admin_users:
            notifications_to_create.append(
                Notification(
                    recipient=admin_user,
                    title=title,
                    message=message,
                    content_type=content_type,
                    object_id=instance.pk,
                    is_read=False
                )
            )
        
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)
        
    elif not created and instance.is_answered and instance.answered_by:
        content_type = ContentType.objects.get_for_model(Question)

        already_notified = Notification.objects.filter(
            recipient=instance.user,
            content_type=content_type,
            object_id=instance.pk,
            title="پاسخ به سوال",
            is_read=False
        ).exists()
        
        if not already_notified:
            prescription_title = "ناشناس"
            if hasattr(instance, 'prescription') and instance.prescription:
                prescription_title = instance.prescription.title
            
            title = "پاسخ به سوال"
            message = f"پاسخ سوال شما در مورد نسخه «{prescription_title}» داده شد."
            
            Notification.objects.create(
                recipient=instance.user,
                title=title,
                message=message,
                content_type=content_type,
                object_id=instance.pk,
                is_read=False
            )
