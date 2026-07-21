from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, View
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, models
from django.urls import reverse_lazy

import logging
import jdatetime
import json

from apps.home.models import Contact
from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from ..services.email_service import send_contact_response_email

logger = logging.getLogger(__name__)

BREADCRUMB_HOME = {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')}
BREADCRUMB_CONTACTS = {'label': 'مدیریت پیام‌ها', 'url': reverse_lazy('dashboard:contacts:contacts_list')}


class ContactsListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
    model = Contact
    template_name = 'dashboard/contacts/list.html'
    context_object_name = 'contacts'
    paginate_by = 20

    def get_queryset(self):
        queryset = Contact.objects.order_by('-created_at')
        search = self.request.GET.get('search', '').strip()
        status = self.request.GET.get('status', 'all')

        if search:
            queryset = queryset.filter(
                models.Q(full_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(subject__icontains=search)
            )

        if status == 'unread':
            queryset = queryset.filter(admin_response__isnull=True)
        elif status == 'read':
            queryset = queryset.filter(admin_response__isnull=False)
        elif status in ('pending', 'in_progress', 'answered', 'closed'):
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = [BREADCRUMB_HOME, {'label': 'مدیریت پیام‌ها', 'url': ''}]
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', 'all')

        context['stats'] = {
            'total': Contact.objects.count(),
            'unread': Contact.objects.filter(admin_response__isnull=True).count(),
            'answered': Contact.objects.filter(status='answered').count(),
        }

        # تاریخ شمسی برای هر پیام
        for contact in context['contacts']:
            if contact.created_at:
                jalali = jdatetime.datetime.fromgregorian(datetime=contact.created_at.replace(tzinfo=None))
                contact.shamsi_created_at = jalali.strftime('%Y/%m/%d - %H:%M')
            else:
                contact.shamsi_created_at = ''

        return context


class ContactDetailView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, DetailView):
    model = Contact
    template_name = 'dashboard/contacts/detail.html'
    context_object_name = 'contact'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = context['contact']
        context['breadcrumb'] = [
            BREADCRUMB_HOME,
            BREADCRUMB_CONTACTS,
            {'label': contact.subject_display, 'url': ''}
        ]

        if contact.created_at:
            jalali = jdatetime.datetime.fromgregorian(datetime=contact.created_at.replace(tzinfo=None))
            contact.shamsi_created_at = jalali.strftime('%Y/%m/%d - %H:%M')

        if contact.responded_at:
            jalali_resp = jdatetime.datetime.fromgregorian(datetime=contact.responded_at.replace(tzinfo=None))
            contact.shamsi_responded_at = jalali_resp.strftime('%Y/%m/%d - %H:%M')

        return context

    def post(self, request, *args, **kwargs):
        contact = self.get_object()
        admin_response = request.POST.get('admin_response', '').strip()

        if not admin_response:
            messages.error(request, 'متن پاسخ نمی‌تواند خالی باشد.')
            return redirect('dashboard:contacts:contact_detail', pk=contact.pk)

        try:
            with transaction.atomic():
                contact.admin_response = admin_response
                contact.responded_by = request.user
                contact.responded_at = timezone.now()
                contact.status = 'answered'
                contact.save()

                if contact.email:
                    send_contact_response_email(contact)

            messages.success(request, 'پاسخ شما با موفقیت ارسال شد.')
        except Exception as e:
            messages.error(request, f'خطا در ارسال پاسخ: {str(e)}')

        return redirect('dashboard:contacts:contact_detail', pk=contact.pk)


class ContactMarkReadView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def post(self, request, pk):
        contact = get_object_or_404(Contact, pk=pk)
        if contact.status != 'closed':
            contact.status = 'closed'
            contact.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'پیام بسته شد.')
        else:
            messages.info(request, 'این پیام قبلاً بسته شده است.')
        return redirect('dashboard:contacts:contact_detail', pk=pk)


class ContactDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def post(self, request, pk):
        contact = get_object_or_404(Contact, pk=pk)
        title = contact.subject_display
        contact.delete()
        messages.success(request, f'پیام «{title}» با موفقیت حذف شد.')
        return redirect('dashboard:contacts:contacts_list')


@method_decorator(csrf_exempt, name='dispatch')
class ContactsBulkDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            message_ids = data.get('message_ids', [])
            if not message_ids:
                return JsonResponse({'success': False, 'error': 'هیچ پیامی انتخاب نشده است'})

            deleted_count, _ = Contact.objects.filter(id__in=message_ids).delete()
            return JsonResponse({
                'success': True,
                'deleted_count': deleted_count,
                'message': f'{deleted_count} پیام با موفقیت حذف شد'
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'داده‌های ارسالی نامعتبر است'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'خطا در حذف پیام‌ها: {str(e)}'})
