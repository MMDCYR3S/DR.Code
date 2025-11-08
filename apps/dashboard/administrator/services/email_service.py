import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

# ====== Send Email Task ====== #
def _send_email_task(subject, to_email, html_template_name, context=None):
    """
    تابع اصلی ارسال ایمیل با پشتیبانی از هر دو فرمت HTML و Plain Text.
    """
    if context is None:
        context = {}
    
    try:
        html_message = render_to_string(html_template_name, context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"ایمیل با موفقیت به {to_email} ارسال شد")
    except Exception as e:
        logger.error(f"ارسال ایمیل به {to_email} با خطا مواجه شد: {e}", exc_info=True)

# ====== Send Email In Background ====== #
def send_email_in_background(subject, to_email, template_name, context=None):
    """
    نسخه‌ی موقت: بدون Thread، ارسال هم‌زمان برای تست سرعت.
    """
    logger.info(f"شروع ارسال ایمیل به {to_email} با موضوع: {subject}")
    _send_email_task(subject, to_email, template_name, context)


def send_contact_response_email(contact):
    if not contact.email:
        logger.warning(f"پیام تماس {contact.id} ایمیل برای ارسال پاسخ ندارد.")
        return

    subject = f"پاسخ به پیام شما - {contact.subject_display}"
    context = {'contact': contact, 'site_name': 'دکتر کد'}
    send_email_in_background(subject, contact.email, 'email/contact_response.html', context)


def send_welcome_email(user):
    if not user.email:
        logger.warning(f"کاربر {user.id} ایمیل برای ارسال خوشامدگویی ندارد.")
        return

    subject = "به دکتر کد خوش آمدید!"
    context = {'user': user, 'site_name': 'دکتر کد'}
    send_email_in_background(subject, user.email, 'email/welcome.html', context)


def resend_auth_email(user):
    if not user.email:
        return

    subject = "رد احزار هویت - دکتر کد"
    context = {'user': user, 'site_name': 'دکتر کد', 'reason': user.profile.rejection_reason}
    send_email_in_background(subject, user.email, 'email/resend_auth.html', context)


def send_auth_checked_email(user):
    if not user.email:
        return

    subject = "به جمع ما خوش آمدید - دکتر کد"
    context = {'user': user, 'site_name': 'دکتر کد'}
    send_email_in_background(subject, user.email, 'email/auth_checked.html', context)


def send_email_to_answered_question(user):
    if not user.email:
        return

    subject = "پاسخ به سؤال شما - دکتر کد"
    context = {'user': user, 'site_name': 'دکتر کد'}
    send_email_in_background(subject, user.email, 'email/question_answered.html', context)


def send_password_reset_email(user):
    if not user.email:
        logger.warning(f"کاربر {user.id} ایمیلی برای ارسال لینک بازیابی رمز عبور ندارد.")
        return

    token_generator = PasswordResetTokenGenerator()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = token_generator.make_token(user)

    reset_path = f"/password/reset/confirm/{uid}/{token}/"
    reset_url = f"https://drcode-med.ir{reset_path}"

    subject = "بازیابی رمز عبور - دکتر کد"
    context = {"user": user, "site_name": "دکتر کد", "reset_url": reset_url}
    send_email_in_background(subject, user.email, "email/password_reset_email.html", context)
