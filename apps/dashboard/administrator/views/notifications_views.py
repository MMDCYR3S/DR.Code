import json
from itertools import chain
from operator import itemgetter

from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import strip_tags
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from apps.accounts.models import User
from apps.notifications.models import Notification, Announcement
from ..forms import SingleNotificationForm, AnnouncementForm

# ================================================ #
# ========= Dashboard List View (Combined) ========= #
# ================================================ #
class NotificationDashboardView(TemplateView):
    template_name = 'dashboard/notifications/notifications.html' # مسیر قالب خود را چک کنید

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            announcement_ct = ContentType.objects.get_for_model(Announcement)
        except:
            announcement_ct = None
            
        single_notifs = Notification.objects.select_related('recipient').exclude(
            content_type=announcement_ct
        ).order_by('-created_at')
        
        announcements = Announcement.objects.all().order_by('-created_at')

        combined_list = []
        # --- پردازش پیام‌های تکی ---
        for notification in single_notifs:
            combined_list.append({
                'type': 'single',
                'id': notification.id,
                'title': notification.title or "بدون عنوان",
                'message_preview': strip_tags(notification.message)[:60] + '...',
                'full_message': notification.message,
                'recipient_name': notification.recipient.get_full_name() if notification.recipient else "ناشناس",
                'recipient_initial': (notification.recipient.first_name[:1] if notification.recipient and notification.recipient.first_name else "?"),
                'is_read': notification.is_read,
                'created_at': notification.created_at, 
                'created_at_shamsi': notification.shamsi_created_at,
            })

        # --- پردازش اطلاعیه‌های گروهی ---
        if announcement_ct:
            for ann in announcements:
                related_notifs = Notification.objects.filter(
                    content_type__model='announcement',
                    object_id=ann.id
                ).select_related('recipient')
                
                total_sent = related_notifs.count()
                read_count = related_notifs.filter(is_read=True).count()
                
                # گرفتن 5 نفر اول به عنوان نمونه
                sample_recipients = []
                for n in related_notifs[:5]:
                    if n.recipient:
                        sample_recipients.append({
                            'name': n.recipient.get_full_name(),
                            'status': 'خوانده' if n.is_read else 'نخوانده'
                        })

                combined_list.append({
                    'type': 'group',
                    'id': ann.id,
                    'announcement_id': ann.id,
                    'title': ann.title,
                    'message_preview': strip_tags(ann.message)[:60] + '...',
                    'full_message': ann.message,
                    'total_sent': total_sent,
                    'read_count': read_count,
                    'samples': sample_recipients,
                    'created_at': ann.created_at,
                    'created_at_shamsi': ann.shamsi_created_at,
                    'is_expanded': False,
                })

        combined_list.sort(key=lambda x: x.get("created_at"), reverse=True)
        context['notifications_json'] = json.dumps(combined_list, cls=DjangoJSONEncoder)
        
        return context

# ============================================= #
# ========= User Search Json View (AJAX) ========= #
# ============================================= #
class UserSearchJsonView(View):
    """
    جستجوی کاربران برای استفاده در فیلدهای اتوکمپلیت (AJAX)
    جستجو بر اساس: نام، نام خانوادگی، ایمیل، شماره تلفن، کد نظام پزشکی
    """
    def get(self, request):
        query = request.GET.get('q', '').strip()
        
        # اگر ورودی کمتر از 2 کاراکتر بود، نتیجه خالی برگردان (برای جلوگیری از کوئری‌های سنگین)
        if len(query) < 2:
            return JsonResponse({'results': []})

        # کوئری ترکیبی روی مدل User و Profile
        users = User.objects.select_related('profile').filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(profile__medical_code__icontains=query)
        ).distinct()[:20]  # محدود کردن نتایج به 20 مورد

        results = []
        for user in users:
            # ساخت متن توضیحات (مثلاً: کد نظام پزشکی یا ایمیل)
            subtext = user.phone_number
            if user.profile.medical_code:
                subtext += f" | ن.پ: {user.profile.medical_code}"
            
            results.append({
                'id': user.id,
                'full_name': user.get_full_name() or user.phone_number,
                'subtext': subtext,
                'role': user.profile.get_role_display() # نمایش نقش کاربر
            })

        return JsonResponse({'results': results})
    
# =========================================== #
# ========= Single Notification Actions ========= #
# =========================================== #
class NotificationCreateView(LoginRequiredMixin, View):
    """
    ایجاد اعلان تکی برای یک کاربر
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            form = SingleNotificationForm(data)
            
            if form.is_valid():
                notification= form.save(commit=False)
                
                notification.content_type = ContentType.objects.get_for_model(notification) 
                notification.object_id = 0 
                
                notification.save()
                return JsonResponse({
                    'success': True,
                    'message': 'اعلان تکی با موفقیت ارسال شد.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'خطا در اعتبارسنجی فرم',
                    'errors': form.errors
                })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
        
# ========================================== #
# ========= Single Notification Delete ========= #
# ========================================== #
class NotificationDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            notification = get_object_or_404(Notification, pk=pk)
            notification.delete()
            return JsonResponse({'success': True, 'message': 'اعلان حذف شد.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
        
# ============================================ #
# ========= Announcement Create View ========= #
# ============================================ #
class AnnouncementCreateView(LoginRequiredMixin, View):
    """
    ایجاد پیام گروهی و توزیع آن (Fan-out)
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            form = AnnouncementForm(data)
            
            if form.is_valid():
                announcement = form.save(commit=False)
                announcement.sender = request.user
                announcement.save()
                
                count = announcement.send_announcement()
                
                return JsonResponse({
                    'success': True,
                    'message': f'پیام گروهی ایجاد و برای {count} کاربر ارسال شد.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'خطا در فرم پیام گروهی',
                    'errors': form.errors
                })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
        
# ============================================ #
# ========= Announcement Detail View ========= #
# ============================================ #
class AnnouncementDetailView(LoginRequiredMixin, View):
    """برای پر کردن فرم ویرایش در مودال"""
    def get(self, request, pk, *args, **kwargs):
        try:
            ann = get_object_or_404(Announcement, pk=pk)
            return JsonResponse({
                'success': True,
                'data': {
                    'title': ann.title,
                    'message': ann.message,
                    'target_role': ann.target_role,
                    'is_sent': ann.is_sent
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})        

# ============================================= #
# ========= Announcement Update View ========= #
# ============================================= #
class AnnouncementUpdateView(LoginRequiredMixin, View):
    """
    ویرایش پیام گروهی
    """
    def post(self, request, pk, *args, **kwargs):
        try:
            ann = get_object_or_404(Announcement, pk=pk)
            data = json.loads(request.body)
            form = AnnouncementForm(data, instance=ann)
            
            if form.is_valid():
                form.save()
                return JsonResponse({'success': True, 'message': 'پیام گروهی بروزرسانی شد.'})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
        
# ============================================= #
# ========= Announcement Delete View ========= #
# ============================================= #
class AnnouncementDeleteView(LoginRequiredMixin, View):
    """
    حذف پیام گروهی
    """
    def post(self, request, pk, *args, **kwargs):
        try:
            ann = get_object_or_404(Announcement, pk=pk)
            ct = ContentType.objects.get_for_model(Announcement)
            Notification.objects.filter(content_type=ct, object_id=ann.id).delete()
            
            ann.delete()
            return JsonResponse({'success': True, 'message': 'پیام گروهی و تمام اعلان‌های وابسته حذف شدند.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
