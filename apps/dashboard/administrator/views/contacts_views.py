from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, View
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

import logging
import jdatetime
import json

from apps.home.models import Contact
from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from ..services.email_service import send_contact_response_email

logger = logging.getLogger(__name__)

# ================================================== #
# ============= CONTACT LIST VIEW ============= #
# ================================================== #
class ContactsListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
    """ دیدن پیام های ارسال شده از فرم تماس با ما """
    model = Contact
    template_name = 'dashboard/contacts/contacts.html'
    context_object_name = 'contacts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Contact.objects.all().order_by('-created_at')
        
        # فیلتر بر اساس وضعیت
        status_filter = self.request.GET.get('status', 'all')
        if status_filter == 'unread':
            queryset = queryset.filter(admin_response__isnull=True)
        elif status_filter == 'read':
            queryset = queryset.filter(admin_response__isnull=False)
        elif status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', 'all')

        for contact in context['contacts']:
            if contact.created_at:
                jalali_date = jdatetime.datetime.fromgregorian(
                    datetime=contact.created_at.replace(tzinfo=None)
                )
                contact.jalali_date = jalali_date.strftime('%Y/%m/%d - %H:%M')
                
        return context
    
    
# ================================================== #
# ============= CONTACT DETAIL VIEW ============= #
# ================================================== #
class ContactDetailView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, DetailView):
    """ خواندن پیام های ارسال شده از فرم تماس با ما و جواب دادن به آن ها """
    model = Contact
    template_name = 'dashboard/contacts/contacts-detail.html'
    context_object_name = 'contact'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = context['contact']
        if contact.created_at:
            jalali_date = jdatetime.datetime.fromgregorian(
                datetime=contact.created_at.replace(tzinfo=None)
            )
        if contact.responded_at:
            jalali_response = jdatetime.datetime.fromgregorian(
                datetime=contact.responded_at.replace(tzinfo=None)
            )
            contact.jalali_date = jalali_date.strftime('%Y/%m/%d - %H:%M')
            contact.jalali_response = jalali_response.strftime('%Y/%m/%d - %H:%M')
        return context
    

    def post(self, request, *args, **kwargs):
        """پردازش ارسال پاسخ"""
        contact = self.get_object()
        
        admin_response = request.POST.get('admin_response', '').strip()
        
        if not admin_response:
            messages.error(request, 'متن پاسخ نمی‌تواند خالی باشد.')
            return redirect('dashboard:contacts:contact_detail', pk=contact.id)
        
        try:
            # ذخیره پاسخ در دیتابیس
            with transaction.atomic():
                contact.admin_response = admin_response
                contact.responded_by = request.user
                contact.responded_at = timezone.now()
                contact.status = 'answered'
                contact.save()
                
                if contact.email:
                    send_contact_response_email(contact)
            
            messages.success(request, 'پاسخ شما با موفقیت ارسال شد.')
            return redirect('dashboard:contacts:contact_detail', pk=contact.id)
            
        except Exception as e:
            messages.error(request, f'خطا در ارسال پاسخ: {str(e)}')
            return redirect('dashboard:contacts:contact_detail', pk=contact.id)

# ================================================== #
# ============= CONTACT MARK READ VIEW ============= #
# ================================================== #
class ContactMarkReadView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """علامت‌گذاری پیام به عنوان خوانده شده"""
    
    def post(self, request, pk):
        try:
            contact = get_object_or_404(Contact, pk=pk)
            
            if contact.status != 'closed':
                contact.status = 'closed'
                contact.save(update_fields=['status', 'updated_at'])
                
                messages.success(request, 'پیام به عنوان بسته شده علامت‌گذاری شد.')
            else:
                messages.info(request, 'این پیام قبلاً بسته شده است.')
            
            return redirect('dashboard:contacts:contact_detail', pk=contact.id)
            
        except Exception as e:
            messages.error(request, f'خطا در علامت‌گذاری پیام: {str(e)}')
            return redirect('dashboard:contacts:contacts_list')

# ================================================== #
# ============= CONTACT DELETE VIEW ============= #
# ================================================== #
class ContactDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """حذف پیام تماس"""
    
    def post(self, request, pk):
        try:
            contact = get_object_or_404(Contact, pk=pk)
            contact_subject = contact.subject
            
            with transaction.atomic():
                contact.delete()
            
            messages.success(request, f'پیام "{contact_subject}" با موفقیت حذف شد.')
            return redirect('dashboard:contacts:contacts_list')
            
        except Exception as e:
            messages.error(request, f'خطا در حذف پیام: {str(e)}')
            return redirect('dashboard:contacts:contact_detail', pk=pk)        
        
# ================================================== #
# ============= CONTACT BULK DELETE VIEW ============= #
# ================================================== #
@method_decorator(csrf_exempt, name='dispatch')
class ContactsBulkDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """حذف دسته‌جمعی پیام‌ها"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            message_ids = data.get('message_ids', [])
            
            if not message_ids:
                return JsonResponse({
                    'success': False,
                    'error': 'هیچ پیامی انتخاب نشده است'
                })
            
            # حذف پیام‌های انتخاب شده
            deleted_count = Contact.objects.filter(
                id__in=message_ids
            ).delete()[0]
            
            return JsonResponse({
                'success': True,
                'deleted_count': deleted_count,
                'message': f'{deleted_count} پیام با موفقیت حذف شد'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'داده‌های ارسالی نامعتبر است'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'خطا در حذف پیام‌ها: {str(e)}'
            })