from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.prescriptions.models import Prescription

import jdatetime

# ======== Question Model ======== #
class Question(models.Model):
    """
    مدل برای ثبت سوالات کاربران ویژه در مورد نسخه‌های مختلف.
    هر سوال به یک کاربر و یک نسخه خاص مرتبط است.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="کاربر سوال‌کننده"
    )
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="نسخه مربوطه"
    )
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answered_questions',
        verbose_name="پاسخ‌دهنده"
    )
    question_text = models.TextField(verbose_name="متن سوال")
    answer_text = models.TextField(blank=True, null=True, verbose_name="متن پاسخ ادمین")
    is_answered = models.BooleanField(default=False, verbose_name="پاسخ داده شده؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت سوال")
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ ثبت پاسخ")
    
    @property
    def shamsi_created_at(self):
        if self.created_at is None:
            return "—"
        
        jdate = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")

    @property
    def shamsi_answered_at(self):
        if self.answered_at is None:
            return "—"
            
        jdate = jdatetime.datetime.fromgregorian(datetime=self.answered_at)
        return jdate.strftime("%Y/%m/%d - %H:%M")


    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_answered']),
            models.Index(fields=['prescription', 'is_answered']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"سوال {self.user.username} در مورد نسخه «{self.prescription.title}»"

    def save(self, *args, **kwargs):
        """
        متد save را بازنویسی می‌کنیم تا اگر پاسخی ثبت شد،
        فیلدهای is_answered و answered_at به طور خودکار بروز شوند.
        """
        if self.answer_text and not self.is_answered:
            self.is_answered = True
            self.answered_at = timezone.now()
        super().save(*args, **kwargs)

    
    def clean(self):
        """اعتبارسنجی مدل"""
        super().clean()
        
        # بررسی اینکه کاربر اشتراک فعال داشته باشد
        if self.user and not self.user.profile.role == "premium":
            raise ValidationError("فقط کاربران با اشتراک فعال می‌توانند سوال بپرسند.")
        
        # بررسی طول سوال
        if self.question_text and len(self.question_text.strip()) < 10:
            raise ValidationError("سوال باید حداقل ۱۰ کاراکتر باشد.")
        
    def save(self, *args, **kwargs):
        """
        متد save را بازنویسی می‌کنیم تا اگر پاسخی ثبت شد،
        فیلدهای is_answered و answered_at به طور خودکار بروز شوند.
        """
        # اعتبارسنجی قبل از ذخیره
        self.full_clean()
        
        # اگر پاسخ جدید ثبت شده
        if self.answer_text and not self.is_answered:
            self.is_answered = True
            self.answered_at = timezone.now()
        
        # اگر پاسخ حذف شده
        elif not self.answer_text and self.is_answered:
            self.is_answered = False
            self.answered_at = None
            self.answered_by = None
        
        super().save(*args, **kwargs)
        
    @property
    def status_display(self):
        """ نمایش وضعیت سوال """
        return "پاسخ داده شده" if self.is_answered else "در انتظار پاسخ"

    @property
    def is_recent(self):
        """ بررسی اینکه سوال جدید است (کمتر از 24 ساعت) """
        return (timezone.now() - self.created_at).days < 1

    def get_response_time(self):
        """ محاسبه زمان پاسخ‌دهی """
        if self.answered_at:
            delta = self.answered_at - self.created_at
            if delta.days > 0:
                return f"{delta.days} روز"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} ساعت"
            else:
                minutes = delta.seconds // 60
                return f"{minutes} دقیقه"
        return None