from django.db import models
from django.core.exceptions import ValidationError
from django.core.cache import cache

# =========== TUTORIAL MODEL =========== # 
class Tutorial(models.Model):
    """
    مدل ساده ویدیوهای آموزشی از آپارات
    """
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان ویدیو'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='توضیحات',
        help_text='توضیح اختیاری از محتوای ویدیو'
    )
    aparat_url = models.URLField(
        max_length=255,
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

    class Meta:
        verbose_name = 'ویدیوی آموزشی'
        verbose_name_plural = 'ویدیوهای آموزشی'
        ordering = ['-created_at']

    def clean(self):
        """اعتبارسنجی مدل"""
        super().clean()
        
        # اعتبارسنجی لینک آپارات
        if self.aparat_url and 'aparat.com' not in self.aparat_url:
            raise ValidationError({
                'aparat_url': 'آدرس باید از سایت آپارات (aparat.com) باشد.'
            })

    def save(self, *args, **kwargs):
        """ذخیره با پاک کردن کش"""
        super().save(*args, **kwargs)
        
        # پاک کردن کش مربوط به ویدیوها
        cache.delete('tutorials_list')
        cache.delete(f'tutorial_detail_{self.id}')

    def __str__(self):
        return self.title

    @classmethod
    def get_all_tutorials(cls):
        """دریافت تمام ویدیوها با کش"""
        cache_key = 'tutorials_list'
        tutorials = cache.get(cache_key)
        
        if tutorials is None:
            tutorials = cls.objects.all()
            cache.set(cache_key, tutorials, timeout=1800)
        
        return tutorials
