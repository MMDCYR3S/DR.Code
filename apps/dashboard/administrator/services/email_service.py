import logging
import threading
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

logger = logging.getLogger(__name__)
print(f"The name of the email service logger is: {__name__}")
# SEND EMAIL TASK
def _send_email_task(subject, to_email, template_name, context=None):
    """
    این تابع وظیفه اصلی ارسال ایمیل را در یک ترد جداگانه بر عهده دارد.
    این یک تابع داخلی و عمومی است که نباید مستقیماً فراخوانی شود.
    """
    if context is None:
        context = {}
    
    try:
        html_message = render_to_string(template_name, context)
        
        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"ایمیل با موفقیت به {to_email} ارسال شد.")
    except Exception as e:
        logger.error(f"ارسال ایمیل به {to_email} با خطا مواجه شد: {e}", exc_info=True)
        
# SEND EMAIL IN BACKGROUND
def send_email_in_background(subject, to_email, template_name, context=None):
    """
    تابع اصلی برای شروع فرآیند ارسال ایمیل در پس‌زمینه.
    از این تابع در ویوها و بخش‌های دیگر پروژه استفاده کنید.
    
    :param subject: موضوع ایمیل
    :param to_email: آدرس ایمیل گیرنده
    :param template_name: مسیر فایل تمپلیت HTML ایمیل
    :param context: دیکشنری حاوی متغیرهایی که باید در تمپلیت استفاده شوند
    """
    logger.info(f"آماده‌سازی برای ارسال ایمیل به {to_email} با موضوع: {subject}")
    
    email_thread = threading.Thread(
        target=_send_email_task,
        args=(subject, to_email, template_name, context)
    )
    email_thread.daemon = True
    email_thread.start()
    
def send_contact_response_email(contact):
    """ایمیل پاسخ به فرم تماس را آماده و برای ارسال در صف قرار می‌دهد."""
    if not contact.email:
        logger.warning(f"پیام تماس {contact.id} ایمیل برای ارسال پاسخ ندارد.")
        return
        
    subject = f"پاسخ به پیام شما - {contact.subject_display}"
    context = {
        'contact': contact,
        'site_name': 'دکتر کد',
    }
    send_email_in_background(
        subject=subject,
        to_email=contact.email,
        template_name='email/contact_response.html',
        context=context
    )


def send_welcome_email(user):
    """ایمیل خوشامدگویی را برای کاربر جدید آماده و برای ارسال در صف قرار می‌دهد."""
    if not user.email:
        logger.warning(f"کاربر {user.id} ایمیل برای ارسال خوشامدگویی ندارد.")
        return
        
    subject = "به دکتر کد خوش آمدید!"
    context = {
        'user': user,
        'site_name': 'دکتر کد',
    }
    send_email_in_background(
        subject=subject,
        to_email=user.email,
        template_name='email/welcome.html',
        context=context
    )
    
def resend_auth_email(user):
    """ ایمیل عدم احراز هویت """
    
    if not user.email:
        return
    
    subject = "رد احزار هویت - دکتر کد"
    context = {
        'user': user,
        'site_name': 'دکتر کد',
    }
    
    send_email_in_background(
        subject=subject,
        to_email=user.email,
        template_name='email/resend_auth.html',
        context=context
    )
    
def send_auth_checked_email(user):
    """ ایمیل موفقیت آمیز بودن احراز هویت """
    
    if not user.email:
        return
    
    subject = "به جمع ما خوش آمدید - دکتر کد"
    context = {
        'user': user,
        'site_name': 'دکتر کد',
    }
    
    send_email_in_background(
        subject=subject,
        to_email=user.email,
        template_name='email/auth_checked.html',
        context=context
    )
    
def send_email_to_answered_question(user):
    """ ایمیل مربوط به پاسخ به سوال مربوطه برای کاربر ویژه """
    
    if not user.email:
        return
    
    subject = "پاسخ به سؤال شما - دکتر کد"
    context = {
        'user': user,
        'site_name': 'دکتر کد',
    }
    
    send_email_in_background(
        subject=subject,
        to_email=user.email,
        template_name='email/question_answered.html',
        context=context
    )

def send_password_reset_email(user, site_domain, protocol):
    """
    ایمیل بازیابی رمز عبور را برای کاربر ارسال می‌کند.
    این ایمیل حاوی یک لینک یکبار مصرف برای تنظیم مجدد رمز عبور است.
    """
    if not user.email:
        logger.warning(f"کاربر {user.id} ایمیلی برای ارسال لینک بازیابی رمز عبور ندارد.")
        return
    
    token_generator = PasswordResetTokenGenerator()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = token_generator.make_token(user)
    
    reset_path = f'/password/reset/confirm/{uid}/{token}/'
    reset_url = f"{protocol}://{site_domain}{reset_path}"
    
    subject = "بازیابی رمز عبور - دکتر کد"
    context = {
        'user': user,
        'site_name': 'دکتر کد',
        'reset_url': reset_url,
    }
    
    send_email_in_background(
        subject=subject,
        to_email=user.email,
        template_name='email/password_reset_email.html',
        context=context
    )
