from django.views.generic import ListView, View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.html import strip_tags
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from apps.accounts.models import User
from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from apps.notifications.models import Notification, Announcement
from ..forms import SingleNotificationForm, AnnouncementForm


# ===== لینک‌های پایه بردکرامب ===== #
BREADCRUMB_HOME = {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')}


def _build_notifications(search='', filter_type='all'):
    """ ساخت لیست ترکیبی اعلان‌های تکی و گروهی با فیلتر سرورساید """
    try:
        announcement_ct = ContentType.objects.get_for_model(Announcement)
    except Exception:
        announcement_ct = None

    single_notifs = Notification.objects.select_related('recipient').exclude(
        content_type=announcement_ct
    ).order_by('-created_at')

    if search:
        single_notifs = single_notifs.filter(
            Q(title__icontains=search) |
            Q(message__icontains=search) |
            Q(recipient__first_name__icontains=search) |
            Q(recipient__last_name__icontains=search)
        )
    if filter_type == 'unread':
        single_notifs = single_notifs.filter(is_read=False)
    elif filter_type == 'read':
        single_notifs = single_notifs.filter(is_read=True)

    combined_list = []

    # --- پیام‌های تکی ---
    for notification in single_notifs:
        combined_list.append({
            'type': 'single',
            'id': notification.id,
            'title': notification.title or 'بدون عنوان',
            'message_preview': strip_tags(notification.message)[:60],
            'full_message': notification.message,
            'recipient_name': notification.recipient.get_full_name() if notification.recipient else 'ناشناس',
            'recipient_initial': (notification.recipient.first_name[:1] if notification.recipient and notification.recipient.first_name else '?'),
            'is_read': notification.is_read,
            'created_at': notification.created_at,
            'created_at_shamsi': notification.shamsi_created_at,
        })

    # --- اطلاعیه‌های گروهی (فقط وقتی فیلتر خوانده/نخوانده فعال نیست) ---
    if announcement_ct and filter_type == 'all':
        announcements = Announcement.objects.all().order_by('-created_at')
        if search:
            announcements = announcements.filter(
                Q(title__icontains=search) | Q(message__icontains=search)
            )

        for ann in announcements:
            related_notifs = Notification.objects.filter(
                content_type=announcement_ct,
                object_id=ann.id
            ).select_related('recipient')

            total_sent = related_notifs.count()
            read_count = related_notifs.filter(is_read=True).count()

            sample_recipients = []
            for n in related_notifs[:5]:
                if n.recipient:
                    sample_recipients.append({
                        'name': n.recipient.get_full_name(),
                        'status': 'خوانده' if n.is_read else 'نخوانده',
                    })

            combined_list.append({
                'type': 'group',
                'id': ann.id,
                'announcement_id': ann.id,
                'title': ann.title,
                'message_preview': strip_tags(ann.message)[:60],
                'full_message': ann.message,
                'total_sent': total_sent,
                'read_count': read_count,
                'read_percent': round(read_count / total_sent * 100) if total_sent else 0,
                'samples': sample_recipients,
                'created_at': ann.created_at,
                'created_at_shamsi': ann.shamsi_created_at,
            })

    combined_list.sort(key=lambda x: x.get('created_at'), reverse=True)
    return combined_list


# ================================================ #
# ============ داشبورد لیست اعلان‌ها ============= #
# ================================================ #
class NotificationDashboardView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
    """ لیست ترکیبی اعلان‌های تکی و گروهی با جستجو/فیلتر سرورساید و صفحه‌بندی """

    template_name = 'dashboard/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 15

    def get_queryset(self):
        search = self.request.GET.get('search', '').strip()
        filter_type = self.request.GET.get('filter', 'all').strip()
        return _build_notifications(search, filter_type)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = Announcement.TARGET_ROLES
        context['breadcrumb'] = [BREADCRUMB_HOME, {'label': 'مدیریت اعلان‌ها', 'url': ''}]
        context['search'] = self.request.GET.get('search', '')
        context['filter_type'] = self.request.GET.get('filter', 'all')

        announcement_ct = ContentType.objects.get_for_model(Announcement)
        total_single = Notification.objects.exclude(content_type=announcement_ct).count()
        context['stats'] = {
            'total_single': total_single,
            'unread': Notification.objects.exclude(content_type=announcement_ct).filter(is_read=False).count(),
            'announcements': Announcement.objects.count(),
        }
        return context


# ================================================ #
# ============ جستجوی کاربر (AJAX) =============== #
# ================================================ #
class UserSearchJsonView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ جستجوی کاربران برای اتوکمپلیت فیلد گیرنده (AJAX) """

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'results': []})

        users = User.objects.select_related('profile').filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(profile__medical_code__icontains=query)
        ).distinct()[:20]

        results = []
        for user in users:
            subtext = user.phone_number
            if user.profile.medical_code:
                subtext += f" | ن.پ: {user.profile.medical_code}"
            results.append({
                'id': user.id,
                'full_name': user.get_full_name() or user.phone_number,
                'subtext': subtext,
                'role': user.profile.get_role_display(),
            })

        return JsonResponse({'results': results})


# ================================================ #
# ============ ایجاد اعلان تکی =================== #
# ================================================ #
class NotificationCreateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ ایجاد اعلان تکی برای یک کاربر (POST + redirect) """

    def post(self, request, *args, **kwargs):
        form = SingleNotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.content_type = ContentType.objects.get_for_model(notification)
            notification.object_id = 0
            notification.save()
            messages.success(request, 'اعلان تکی با موفقیت ارسال شد.')
        else:
            messages.error(request, f'خطا در ثبت اعلان: {form.errors.as_text()}')
        return redirect('dashboard:notifications:notifications_list')


# ================================================ #
# ============ حذف اعلان تکی ===================== #
# ================================================ #
class NotificationDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ حذف اعلان تکی (POST + redirect) """

    def post(self, request, pk, *args, **kwargs):
        notification = get_object_or_404(Notification, pk=pk)
        notification.delete()
        messages.success(request, 'اعلان با موفقیت حذف شد.')
        return redirect('dashboard:notifications:notifications_list')


# ================================================ #
# ============ ایجاد پیام گروهی ================== #
# ================================================ #
class AnnouncementCreateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ ایجاد پیام گروهی و توزیع آن (Fan-out) (POST + redirect) """

    def post(self, request, *args, **kwargs):
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.sender = request.user
            announcement.save()
            count = announcement.send_announcement()
            messages.success(request, f'پیام گروهی ایجاد و برای {count} کاربر ارسال شد.')
        else:
            messages.error(request, f'خطا در ثبت پیام گروهی: {form.errors.as_text()}')
        return redirect('dashboard:notifications:notifications_list')


# ================================================ #
# ============ ویرایش پیام گروهی ================= #
# ================================================ #
class AnnouncementUpdateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ ویرایش پیام گروهی (POST + redirect) """

    def post(self, request, pk, *args, **kwargs):
        ann = get_object_or_404(Announcement, pk=pk)
        form = AnnouncementForm(request.POST, instance=ann)
        if form.is_valid():
            form.save()
            messages.success(request, 'پیام گروهی بروزرسانی شد.')
        else:
            messages.error(request, f'خطا در بروزرسانی: {form.errors.as_text()}')
        return redirect('dashboard:notifications:notifications_list')


# ================================================ #
# ============ حذف پیام گروهی ==================== #
# ================================================ #
class AnnouncementDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ حذف پیام گروهی و تمام اعلان‌های وابسته (POST + redirect) """

    def post(self, request, pk, *args, **kwargs):
        ann = get_object_or_404(Announcement, pk=pk)
        ct = ContentType.objects.get_for_model(Announcement)
        Notification.objects.filter(content_type=ct, object_id=ann.id).delete()
        ann.delete()
        messages.success(request, 'پیام گروهی و تمام اعلان‌های وابسته حذف شدند.')
        return redirect('dashboard:notifications:notifications_list')


# ================================================ #
# ============ جزئیات پیام گروهی (AJAX) ========== #
# ================================================ #
class AnnouncementDetailView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """ برای پر کردن فرم ویرایش در مودال (AJAX) """

    def get(self, request, pk, *args, **kwargs):
        ann = get_object_or_404(Announcement, pk=pk)
        return JsonResponse({
            'success': True,
            'data': {
                'title': ann.title,
                'message': ann.message,
                'target_role': ann.target_role,
                'is_sent': ann.is_sent,
            }
        })
