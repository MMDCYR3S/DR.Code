import logging

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from drf_spectacular.views import extend_schema

from .base_views import BaseAPIView
from apps.home.models import Contact
from ..serializers import ContactListSerializer, ContactSerializer

logger = logging.getLogger(__name__)

# =========== CONTACT VIEW =========== #
@extend_schema(tags=['Contact'])
class ContactView(BaseAPIView):
    """
    ارسال پیام تماس با ما
    
    POST: ارسال پیام جدید
    """
    permission_classes = [permissions.AllowAny] 
    serializer_class = ContactSerializer

    def post(self, request, *args, **kwargs):
        """ارسال پیام جدید"""
        try:
            with transaction.atomic():
                serializer = self.serializer_class(
                    data=request.data,
                    context={'request': request}
                )
                
                if serializer.is_valid():
                    contact = serializer.save()
                    
                    # لاگ ایجاد پیام
                    user_info = f"کاربر: {request.user.phone_number}" if request.user.is_authenticated else "کاربر مهمان"
                    logger.info(f"پیام جدید ایجاد شد - {user_info} - {contact.full_name} - موضوع: {contact.subject_display}")
                    
                    # ارسال اطلاع‌رسانی به ادمین‌ها (اختیاری)
                    self._notify_admins(contact)
                    
                    return Response({
                        'success': True,
                        'message': 'پیام شما با موفقیت ارسال شد. به زودی پاسخ شما را دریافت خواهید کرد.',
                        'data': {
                            'contact_id': contact.id,
                            'full_name': contact.full_name,
                            'subject': contact.subject_display,
                            'created_at': contact.created_at.isoformat(),
                            'status': contact.get_status_display()
                        }
                    }, status=status.HTTP_201_CREATED)
                
                # خطاهای اعتبارسنجی
                error_messages = []
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list):
                        error_messages.extend([f"{field}: {error}" for error in errors])
                    else:
                        error_messages.append(f"{field}: {str(errors)}")
                
                return Response({
                    'success': False,
                    'message': 'خطا در اطلاعات ارسالی',
                    'errors': serializer.errors,
                    'error_details': error_messages
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return self.handle_exception(e)

    def _notify_admins(self, contact):
        """اطلاع‌رسانی به ادمین‌ها (می‌توان توسعه داد)"""
        try:
            # اینجا می‌توان ایمیل، پیامک یا اطلاعیه تلگرام به ادمین‌ها ارسال کرد
            logger.info(f"اطلاع‌رسانی پیام جدید: {contact.id} - {contact.subject_display}")
            
            # TODO: پیاده‌سازی ارسال اطلاعیه
            # - ارسال ایمیل به ادمین‌ها
            # - ارسال پیام تلگرام
            # - ذخیره notification در سیستم
            
        except Exception as e:
            logger.error(f"خطا در اطلاع‌رسانی به ادمین‌ها: {str(e)}")

# ========= CONTACT INFO VIEW  ========= #
@extend_schema(tags=['Contact'])
class ContactInfoView(BaseAPIView):
    """
    دریافت اطلاعات تماس و راهنمایی
    
    GET: دریافت اطلاعات کانال‌های ارتباطی
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        """دریافت اطلاعات تماس"""
        try:
            contact_info = {
                'contact_channels': [
                    {
                        'type': 'telegram_admin',
                        'title': 'ارتباط مستقیم با پشتیبانی',
                        'description': 'پاسخگویی از طریق پیام مستقیم در تلگرام — در سریع‌ترین زمان ممکن',
                        'link': 'https://t.me/Doctor_Code_Admin',
                        'username': '@Doctor_Code_Admin',
                        'recommended': True
                    },
                    {
                        'type': 'telegram_channel',
                        'title': 'کانال تلگرام رسمی',
                        'description': 'آخرین اخبار، آموزش‌ها و اطلاعیه‌های سامانه را از این کانال دنبال کنید',
                        'link': 'https://t.me/DrCode_Med',
                        'username': '@DrCode_Med',
                        'recommended': False
                    },
                    {
                        'type': 'email',
                        'title': 'ایمیل پشتیبانی',
                        'description': 'در صورتی که امکان دسترسی به تلگرام ندارید، از این ایمیل استفاده کنید',
                        'email': 'support@Drcode-med.ir',
                        'link': 'mailto:support@Drcode-med.ir',
                        'recommended': False
                    }
                ],
                'website_info': {
                    'website': 'www.DrCode-med.ir',
                    'aparat_channel': 'آموزش‌های ویدیویی'
                },
                'form_info': {
                    'subjects': [
                        {'value': 'support', 'label': 'پشتیبانی فنی'},
                        {'value': 'suggestion', 'label': 'پیشنهاد'},
                        {'value': 'complaint', 'label': 'شکایت'},
                        {'value': 'question', 'label': 'سوال عمومی'},
                        {'value': 'cooperation', 'label': 'همکاری'},
                        {'value': 'other', 'label': 'سایر موارد'}
                    ],
                    'guidelines': [
                        'لطفاً قبل از ارسال پیام، سوالات متداول (FAQ) را مطالعه کنید.',
                        'برای دریافت پاسخ سریع‌تر، از طریق تلگرام تماس بگیرید.',
                        'پیام‌های ارسالی حداکثر تا ۲۴ ساعت پاسخ داده می‌شوند.',
                        'اطلاعات شما محفوظ و محرمانه نگهداری می‌شود.'
                    ]
                },
                'commitment_statement': 'تیم «دکتر کد» متعهد به پشتیبانی حرفه‌ای، سریع و پاسخ‌گو به نیازهای کاربران عزیز می‌باشد. ما همراه شما هستیم؛ دقیق، سریع و قابل اعتماد.'
            }
            
            return Response({
                'success': True,
                'data': contact_info
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return self.handle_exception(e)
