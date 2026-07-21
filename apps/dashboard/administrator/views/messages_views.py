from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Q, Case, When, BooleanField
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse

import jdatetime

from apps.questions.models import Question
from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from ..services.email_service import send_email_to_answered_question

BREADCRUMB_HOME = {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')}
BREADCRUMB_QUESTIONS = {'label': 'سوالات کاربران', 'url': reverse_lazy('dashboard:questions:list')}


class QuestionsListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
    model = Question
    template_name = 'dashboard/messages/list.html'
    context_object_name = 'questions'
    paginate_by = 20

    def get_queryset(self):
        queryset = Question.objects.select_related(
            'user', 'prescription', 'prescription__category', 'answered_by'
        ).prefetch_related('user__profile').annotate(
            is_new=Case(
                When(is_answered=False, then=True),
                default=False,
                output_field=BooleanField()
            )
        )

        search = self.request.GET.get('search', '').strip()
        status = self.request.GET.get('status', '').strip()

        if search:
            queryset = queryset.filter(
                Q(question_text__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(prescription__title__icontains=search)
            )
        if status == 'unread':
            queryset = queryset.filter(is_answered=False)
        elif status == 'read':
            queryset = queryset.filter(is_answered=True)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = [BREADCRUMB_HOME, {'label': 'سوالات کاربران', 'url': ''}]
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['stats'] = {
            'total_questions': Question.objects.count(),
            'unread_questions': Question.objects.filter(is_answered=False).count(),
            'read_questions': Question.objects.filter(is_answered=True).count(),
        }
        for question in context['questions']:
            if question.created_at:
                jalali_date = jdatetime.datetime.fromgregorian(
                    datetime=question.created_at.replace(tzinfo=None)
                )
                question.jalali_date = jalali_date.strftime('%Y/%m/%d')
                question.jalali_time = jalali_date.strftime('%H:%M')
        return context


class QuestionDetailView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, DetailView):
    model = Question
    template_name = 'dashboard/messages/detail.html'
    context_object_name = 'question'

    def get_queryset(self):
        return Question.objects.select_related(
            'user', 'prescription', 'prescription__category', 'answered_by'
        ).prefetch_related('user__profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = [
            BREADCRUMB_HOME,
            BREADCRUMB_QUESTIONS,
            {'label': 'جزئیات سوال', 'url': ''}
        ]
        context['formatted_date'] = self.get_formatted_date(self.object.created_at)
        if self.object.answered_at:
            context['formatted_answer_date'] = self.get_formatted_date(self.object.answered_at)
        return context

    def get_formatted_date(self, date):
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
        question = self.get_object()
        answer_text = request.POST.get('answer_text', '').strip()
        if not answer_text:
            messages.error(request, 'متن پاسخ نمی‌تواند خالی باشد.')
            return self.get(request, *args, **kwargs)
        if len(answer_text) < 10:
            messages.error(request, 'پاسخ باید حداقل ۱۰ کاراکتر باشد.')
            return self.get(request, *args, **kwargs)

        question.answer_text = answer_text
        question.answered_by = request.user
        question.answered_at = timezone.now()
        question.is_answered = True
        question.save()
        send_email_to_answered_question(question.user)
        messages.success(request, 'پاسخ شما با موفقیت ثبت شد.')
        return redirect('dashboard:questions:list')


@method_decorator(csrf_exempt, name='dispatch')
class QuestionActionView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, DetailView):
    model = Question

    def post(self, request, *args, **kwargs):
        question = self.get_object()
        action = request.POST.get('action')

        if action == 'delete':
            question.delete()
            return JsonResponse({'success': True, 'message': 'سوال با موفقیت حذف شد.', 'redirect_url': reverse_lazy('dashboard:questions:list')})
        elif action == 'mark_unread':
            question.is_answered = False
            question.answer_text = ''
            question.answered_by = None
            question.answered_at = None
            question.save()
            return JsonResponse({'success': True, 'message': 'سوال به عنوان خوانده نشده علامت‌گذاری شد.'})
        elif action == 'mark_read':
            question.is_answered = True
            if not question.answered_at:
                question.answered_at = timezone.now()
            if not question.answered_by:
                question.answered_by = request.user
            question.save()
            return JsonResponse({'success': True, 'message': 'سوال به عنوان خوانده شده علامت‌گذاری شد.'})
        return JsonResponse({'success': False, 'message': 'عملیات نامعتبر'})
