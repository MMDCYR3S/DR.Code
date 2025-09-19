from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError

import re
import jdatetime

User = get_user_model()

# ============ CONTACT MODEL ============ #
class Contact(models.Model):
    """
    مدل ذخیره پیام‌های تماس با ما
    """
    SUBJECT_CHOICES = [
        ('support', 'پشتیبانی پزشکی'),
        ('suggestion', 'پیشنهاد'),
        ('complaint', 'شکایت'),
        ('question', 'سوال عمومی'),
        ('cooperation', 'همکاری'),
        ('other', 'سایر موارد'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('in_progress', 'در حال بررسی'),
        ('answered', 'پاسخ داده شده'),
        ('closed', 'بسته شده'),
    ]
    
    # اطلاعات فرستنده
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='کاربر',
        help_text='کاربر ثبت‌نام شده (در صورت وجود)'
    )
    full_name = models.CharField(
        max_length=150,
        verbose_name='نام و نام خانوادگی'
    )
    email = models.EmailField(
        verbose_name='ایمیل',
        validators=[EmailValidator()]
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='شماره تماس'
    )
    
    # محتوای پیام
    subject = models.CharField(
        max_length=20,
        choices=SUBJECT_CHOICES,
        default='other',
        verbose_name='موضوع'
    )
    custom_subject = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='موضوع سفارشی'
    )
    message = models.TextField(
        verbose_name='متن پیام'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    admin_response = models.TextField(
        blank=True,
        null=True,
        verbose_name='پاسخ ادمین'
    )
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_responses',
        verbose_name='پاسخ‌دهنده'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ارسال'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ بروزرسانی'
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ پاسخ'
    )
    
    @property
    def shamsi_created_at(self):
        if self.created_at is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    @property
    def shamsi_updated_at(self):
        if self.updated_at is None:
            return "—"
            
        jdate = jdatetime.datetime.fromgregorian(datetime=self.updated_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")
    
    @property
    def shamsi_responded_at(self):
        if self.responded_at is None:
            return "—"
            
        jdate = jdatetime.datetime.fromgregorian(datetime=self.responded_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    
    class Meta:
        verbose_name = 'پیام تماس'
        verbose_name_plural = 'پیام‌های تماس'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['subject']),
            models.Index(fields=['created_at']),
        ]
    
    def clean(self):
        """اعتبارسنجی مدل"""
        super().clean()
        
        # اعتبارسنجی نام
        if len(self.full_name.strip()) < 2:
            raise ValidationError({'full_name': 'نام باید حداقل ۲ کاراکتر باشد.'})
        
        # بررسی فقط حروف فارسی و انگلیسی برای نام
        if not re.match(r'^[a-zA-Zآ-ی\s]+$', self.full_name.strip()):
            raise ValidationError({'full_name': 'نام فقط می‌تواند شامل حروف فارسی و انگلیسی باشد.'})
        
        # اعتبارسنجی شماره تلفن (در صورت وجود)
        if self.phone:
            phone_clean = re.sub(r'[\s\-\(\)]', '', self.phone)
            if not re.match(r'^(\+98|0)?9\d{9}$', phone_clean):
                raise ValidationError({'phone': 'شماره تلفن معتبر وارد کنید.'})
        
        # اعتبارسنجی طول پیام
        if len(self.message.strip()) < 10:
            raise ValidationError({'message': 'پیام باید حداقل ۱۰ کاراکتر باشد.'})
        
        if len(self.message.strip()) > 2000:
            raise ValidationError({'message': 'پیام نباید بیشتر از ۲۰۰۰ کاراکتر باشد.'})
    
    def save(self, *args, **kwargs):
        # تمیز کردن داده‌ها
        self.full_name = self.full_name.strip()
        if self.phone:
            self.phone = re.sub(r'[\s\-\(\)]', '', self.phone)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.full_name} - {self.get_subject_display()} ({self.created_at.strftime('%Y/%m/%d')})"
    
    @property
    def subject_display(self):
        """نمایش موضوع با در نظر گیری موضوع سفارشی"""
        if self.subject == 'other' and self.custom_subject:
            return self.custom_subject
        return self.get_subject_display()
    
    def mark_as_answered(self, admin_user, response_text):
        """علامت‌گذاری به عنوان پاسخ داده شده"""
        from django.utils import timezone
        
        self.status = 'answered'
        self.admin_response = response_text
        self.responded_by = admin_user
        self.responded_at = timezone.now()
        self.save()
