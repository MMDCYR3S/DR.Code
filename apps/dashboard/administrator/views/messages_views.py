from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Q, Case, When, BooleanField
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import JsonResponse

import jdatetime

from apps.questions.models import Question
from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from ..services.email_service import send_email_to_answered_question

# ============================================ #
# ============ QUESTION LIST VIEW ============ #
# ============================================ #
class QuestionsListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
    """
    نمایش لیست سوالات دریافت شده از کاربران ویژه
    """
    model = Question
    template_name = 'dashboard/messages/messages.html'
    context_object_name = 'questions'
    paginate_by = 20
    
    def get_queryset(self):
        """
        فیلتر کردن سوالات بر اساس وضعیت
        """
        queryset = Question.objects.select_related(
            'user', 'prescription', 'prescription__category', 'answered_by'
        ).prefetch_related(
            'user__profile'
        ).annotate(
            # اضافه کردن فیلد برای مشخص کردن سوالات جدید (خوانده نشده)
            is_new=Case(
                When(is_answered=False, then=True),
                default=False,
                output_field=BooleanField()
            )
        )

        status_filter = self.request.GET.get('status', 'unread')
        
        if status_filter == 'all':
            # همه سوالات
            pass
        elif status_filter == 'unread':
            # فقط خوانده نشده‌ها (پاسخ داده نشده)
            queryset = queryset.filter(is_answered=False)
        elif status_filter == 'read':
            # فقط خوانده شده‌ها (پاسخ داده شده)
            queryset = queryset.filter(is_answered=True)
            
        # جستجو در متن سوال یا نام کاربر
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(question_text__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(prescription__title__icontains=search_query)
            )
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """
        اضافه کردن داده‌های اضافی به context
        """
        context = super().get_context_data(**kwargs)
        
        # آمارهای کلی
        context['stats'] = {
            'total_questions': Question.objects.count(),
            'unread_questions': Question.objects.filter(is_answered=False).count(),
            'read_questions': Question.objects.filter(is_answered=True).count(),
            'today_questions': Question.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
        }
        
        # وضعیت فعلی فیلتر
        context['current_status'] = self.request.GET.get('status', 'unread')
        
        # جستجوی فعلی
        context['current_search'] = self.request.GET.get('search', '')
        
        for question in context['questions']:
            if question.created_at:
                jalali_date = jdatetime.datetime.fromgregorian(
                    datetime=question.created_at.replace(tzinfo=None)
                )
                question.jalali_date = jalali_date.strftime('%Y/%m/%d')
                question.jalali_time = jalali_date.strftime('%H:%M')
        
        return context
    
    def get_formatted_date(self, date):
        """
        فرمت کردن تاریخ مطابق با طراحی
        """
        now = timezone.now()
        diff = now - date
        
        if diff.days == 0:
            # امروز
            return f"امروز، {date.strftime('%H:%M')}"
        elif diff.days == 1:
            # دیروز
            return f"دیروز، {date.strftime('%H:%M')}"
        elif diff.days <= 7:
            # تا یک هفته
            return f"{diff.days} روز پیش"
        else:
            # بیشتر از یک هفته
            return date.strftime('%Y/%m/%d')

# =============================================== #
# ============ QUESTION DETAIL VIEW ============ #
# =============================================== #
class QuestionDetailView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, DetailView):
    """
    نمایش جزئیات سوال و امکان پاسخ‌دهی
    """
    model = Question
    template_name = 'dashboard/messages/message-detail.html'
    context_object_name = 'question'
    
    def get_queryset(self):
        """
        انتخاب سوال با اطلاعات مرتبط
        """
        return Question.objects.select_related(
            'user', 'prescription', 'prescription__category', 'answered_by'
        ).prefetch_related('user__profile')
    
    def get_context_data(self, **kwargs):
        """
        اضافه کردن داده‌های اضافی به context
        """
        context = super().get_context_data(**kwargs)
        
        # URL برگشت به لیست
        context['back_url'] = self.request.META.get('HTTP_REFERER', reverse_lazy('dashboard:questions:questions_list'))
        
        # فرمت زمان ارسال سوال
        context['formatted_date'] = self.get_formatted_date(self.object.created_at)
        
        # زمان پاسخ (اگر پاسخ داده شده)
        if self.object.answered_at:
            context['formatted_answer_date'] = self.get_formatted_date(self.object.answered_at)
        
        return context
    
    def get_formatted_date(self, date):
        """
        فرمت کردن تاریخ
        """
        now = timezone.now()
        diff = now - date
        
        if diff.days == 0:
            return f"امروز، {date.strftime('%H:%M')}"
        elif diff.days == 1:
            return f"دیروز، {date.strftime('%H:%M')}"
        elif diff.days <= 7:
            return f"{diff.days} روز پیش، {date.strftime('%H:%M')}"
        else:
            return date.strftime('%Y/%m/%d، %H:%M')
    
    def post(self, request, *args, **kwargs):
        """
        پردازش پاسخ ادمین
        """
        question = self.get_object()
        answer_text = request.POST.get('answer_text', '').strip()
        
        if not answer_text:
            messages.error(request, 'متن پاسخ نمی‌تواند خالی باشد.')
            return self.get(request, *args, **kwargs)
        
        if len(answer_text) < 10:
            messages.error(request, 'پاسخ باید حداقل ۱۰ کاراکتر باشد.')
            return self.get(request, *args, **kwargs)
        
        # ثبت پاسخ
        question.answer_text = answer_text
        question.answered_by = request.user
        question.answered_at = timezone.now()
        question.is_answered = True
        question.save()
        send_email_to_answered_question(question.user)
        
        messages.success(request, 'پاسخ شما با موفقیت ثبت شد.')
        return redirect('dashboard:questions:questions_list')

# =============================================== #
# ============ QUESTION ACTION VIEW ============ #
# =============================================== #
@method_decorator(csrf_exempt, name='dispatch')
class QuestionActionView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, DetailView):
    """
    عملیات روی سوالات (حذف، علامت‌گذاری و...)
    """
    model = Question
    
    def post(self, request, *args, **kwargs):
        """
        پردازش عملیات مختلف
        """
        question = self.get_object()
        action = request.POST.get('action')
        
        if action == 'delete':
            return self.delete_question(question)
        elif action == 'mark_unread':
            return self.mark_unread(question)
        elif action == 'mark_read':
            return self.mark_read(question)
        
        return JsonResponse({'success': False, 'message': 'عملیات نامعتبر'})
    
    def delete_question(self, question):
        """
        حذف سوال
        """
        try:
            question.delete()
            return JsonResponse({
                'success': True, 
                'message': 'سوال با موفقیت حذف شد.',
                'redirect_url': reverse_lazy('dashboard:questions:questions_list')
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'خطا در حذف سوال'})
    
    def mark_unread(self, question):
        """
        علامت‌گذاری به عنوان خوانده نشده
        """
        try:
            question.is_answered = False
            question.answer_text = ''
            question.answered_by = None
            question.answered_at = None
            question.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'سوال به عنوان خوانده نشده علامت‌گذاری شد.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'خطا در به‌روزرسانی وضعیت'})
    
    def mark_read(self, question):
        """
        علامت‌گذاری به عنوان خوانده شده (بدون پاسخ)
        """
        try:
            question.is_answered = True
            if not question.answered_at:
                question.answered_at = timezone.now()
            if not question.answered_by:
                question.answered_by = self.request.user
            question.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'سوال به عنوان خوانده شده علامت‌گذاری شد.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'خطا در به‌روزرسانی وضعیت'})
        