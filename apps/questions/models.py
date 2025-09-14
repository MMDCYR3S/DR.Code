from django.db import models
from django.utils import timezone
from django.conf import settings

from apps.prescriptions.models import Prescription

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
    question_text = models.TextField(verbose_name="متن سوال")
    answer_text = models.TextField(blank=True, null=True, verbose_name="متن پاسخ ادمین")
    is_answered = models.BooleanField(default=False, verbose_name="پاسخ داده شده؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت سوال")
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ ثبت پاسخ")

    class Meta:
        ordering = ['-created_at']

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
