import jdatetime

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Notification(models.Model):
    """
    مدل برای ثبت اعلان‌ها برای کاربران مختلف سیستم.
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="گیرنده"
    )
    title = models.CharField(max_length=100, verbose_name="عنوان اعلان", default="اعلان جدید")
    message = models.CharField(max_length=255, verbose_name="متن اعلان")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده؟")
    
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"اعلان برای {self.recipient.username}: {self.message[:30]}..."
    
    @property
    def shamsi_created_at(self):
        if self.created_at is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")
    
    @property
    def full_text(self):
        """
        هنگام ارسال پیام های دسته جمعی، نیازمند این هستیم که پیام کامل
        رو ارسال کنیم. اگر زیاد از 255 کاراکتر بود، به بخش فیلد مربوط به
        پیام در مدل announcement وصل میشه.
        """
        if self.content_type and self.content_type.model == 'announcement' and self.content_object:
            return self.content_object.message
        return self.message
    