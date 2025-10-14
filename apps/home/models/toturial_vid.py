from django.db import models
from django.core.exceptions import ValidationError
from django.core.cache import cache

import jdatetime
from django.utils import timezone
from datetime import timedelta

# =========== TUTORIAL MODEL =========== # 
class Tutorial(models.Model):
    """
    مدل ساده ویدیوهای آموزشی از آپارات
    """
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان ویدیو'
    )
    aparat_url = models.TextField(
        verbose_name='آدرس آپارات',
        help_text='لینک کامل ویدیو در آپارات'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ساخت'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='زمان بروزرسانی'
    )
    
    @property
    def shamsi_created_at(self):
        """تاریخ شمسی ایجاد"""
        if self.created_at is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    @property
    def shamsi_updated_at(self):
        """تاریخ شمسی بروزرسانی"""
        if self.updated_at is None:
            return "—"
            
        jdate = jdatetime.datetime.fromgregorian(datetime=self.updated_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    @property
    def is_recent(self):
        """بررسی اینکه آیا ویدیو در 7 روز گذشته ایجاد شده است"""
        if not self.created_at:
            return False
            
        created_at = self.created_at
        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at)
            
        now = timezone.now()
        return created_at >= (now - timedelta(days=7))

    class Meta:
        verbose_name = 'ویدیوی آموزشی'
        verbose_name_plural = 'ویدیوهای آموزشی'
        ordering = ['-created_at']

    def clean(self):
        """اعتبارسنجی مدل"""
        super().clean()
        
        # اعتبارسنجی لینک آپارات (انعطاف‌پذیر برای iframe و script)
        if self.aparat_url and 'aparat' not in self.aparat_url.lower():
            raise ValidationError({
                'aparat_url': 'کد embed باید مربوط به آپارات باشد.'
            })

    def save(self, *args, **kwargs):
        """ذخیره با پاک کردن کش"""
        super().save(*args, **kwargs)
        
        # پاک کردن کش مربوط به ویدیوها
        cache.delete('tutorials_list')
        cache.delete('api_tutorials_list')
        cache.delete(f'tutorial_detail_{self.id}')

    def delete(self, *args, **kwargs):
        """حذف با پاک کردن کش"""
        tutorial_id = self.id
        super().delete(*args, **kwargs)
        
        # پاک کردن کش
        cache.delete('tutorials_list')
        cache.delete('api_tutorials_list')
        cache.delete(f'tutorial_detail_{tutorial_id}')

    def __str__(self):
        return self.title

    @classmethod
    def get_all_tutorials(cls):
        """دریافت تمام ویدیوها مستقیم از دیتابیس"""
        return cls.objects.all().order_by('-created_at')
