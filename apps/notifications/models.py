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
    
    def shamsi_created_at(self):
        if self.created_at is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")
    