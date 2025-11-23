import jdatetime

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .notification import Notification
from apps.accounts.models import Profile

# ===== Announcement Model ===== #
class Announcement(models.Model):
    """
    مدلی برای مدیریت و ارسال پیام‌های گروهی (Broadcast).
    """
    
    TARGET_ROLES = [
        ('all', 'همه کاربران'),
        ('visitor', 'بازدیدکنندگان'),
        ('regular', 'کاربران عادی'),
        ('premium', 'کاربران ویژه'),
    ]

    title = models.CharField(max_length=100, verbose_name=_("عنوان"))
    message = models.TextField(verbose_name=_("متن پیام"))
    
    target_role = models.CharField(
        max_length=20,
        choices=TARGET_ROLES,
        verbose_name=_("نقش هدف")
    )
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("ارسال کننده")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False, verbose_name=_("ارسال شده؟"))

    def __str__(self):
        return f"{self.title} - {self.get_target_role_display()}"

    def send_announcement(self):
        """
        ارسال پیام به کاربرها با گروهی کاربرها.
        """
        # ===== اگر قبلا ارسال شده بود ===== #
        if self.is_sent:
            return 0
        # ===== تفکیک کاربران براساس نقش ===== #
        users_query = Profile.objects.select_related("user").exclude(role='admin')
        if self.target_role != 'all':
            users_query = users_query.filter(role=self.target_role)
            
        # ===== جلوگیری از پرشدن حافظه ===== #
        profiles = users_query.iterator()
        
        notifications_to_create = []
        for profile in profiles:
            notification = Notification(
                recipient=profile.user,
                title=self.title,
                message=self.message,
                content_object=self,
            )
            notifications_to_create.append(notification)
            
            # ===== جلوگیری از پر شدن رم و کند شدن سیستم ===== #
            if len(notifications_to_create) >= 5000:
                Notification.objects.bulk_create(notifications_to_create)
                notifications_to_create = []
                
        # ===== اگر پیام ها باقی ماند یا کمتر از 5000 تا بود ===== # 
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)

        # ===== ذخیره پیام ===== #
        self.is_sent = True
        self.save()
        return len(notifications_to_create)
    
    @property
    def shamsi_created_at(self):
        if self.created_at is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")
    
