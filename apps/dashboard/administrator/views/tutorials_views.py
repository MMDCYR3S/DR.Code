from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib import messages

from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from apps.home.models import Tutorial
import json
import logging

logger = logging.getLogger(__name__)

BREADCRUMB_HOME = {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')}
BREADCRUMB_TUTORIALS = {'label': 'مدیریت ویدیوهای آموزشی', 'url': reverse_lazy('dashboard:tutorials:tutorial_list')}


# ================================================ #
# ============= TUTORIALS LIST VIEW ============= #
# ================================================ #
class TutorialsListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
    model = Tutorial
    template_name = 'dashboard/tutorials/list.html'
    context_object_name = 'tutorials'
    paginate_by = 20

    def get_queryset(self):
        queryset = Tutorial.objects.all().order_by('-created_at')
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(Q(title__icontains=search))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = [BREADCRUMB_HOME, {'label': 'مدیریت ویدیوهای آموزشی', 'url': ''}]
        context['search'] = self.request.GET.get('search', '')

        # آمار
        total = Tutorial.objects.count()
        recent = Tutorial.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        views = 0  # در صورت وجود فیلد بازدید، محاسبه شود

        context['stats'] = {
            'total': total,
            'recent': recent,
            'views': views,
        }

        # داده‌های JSON برای Alpine
        tutorials_data = []
        for tutorial in context['tutorials']:
            tutorials_data.append({
                'id': tutorial.id,
                'title': tutorial.title,
                'shamsi_created_at': tutorial.shamsi_created_at,
                'shamsi_updated_at': tutorial.shamsi_updated_at,
                'created_at': tutorial.created_at.isoformat(),
            })
        context['tutorials_json'] = json.dumps(tutorials_data, ensure_ascii=False)

        return context


# ================================================== #
# ============= TUTORIALS CREATE VIEW ============= #
# ================================================== #
@method_decorator(csrf_exempt, name='dispatch')
class TutorialCreateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            title = data.get('title', '').strip()
            aparat_url = data.get('aparat_url', '').strip()

            if not title:
                return JsonResponse({'success': False, 'message': 'عنوان نمی‌تواند خالی باشد'}, status=400)
            if not aparat_url:
                return JsonResponse({'success': False, 'message': 'کد embed نمی‌تواند خالی باشد'}, status=400)

            tutorial = Tutorial(title=title, aparat_url=aparat_url)
            tutorial.full_clean()
            tutorial.save()

            return JsonResponse({
                'success': True,
                'message': 'ویدیو با موفقیت ایجاد شد',
                'tutorial': {
                    'id': tutorial.id,
                    'title': tutorial.title,
                    'aparat_url': tutorial.aparat_url,
                    'shamsi_created_at': tutorial.shamsi_created_at,
                    'shamsi_updated_at': tutorial.shamsi_updated_at,
                }
            })

        except ValidationError as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error creating tutorial: {e}")
            return JsonResponse({'success': False, 'message': 'خطا در ایجاد ویدیو'}, status=500)


# ================================================== #
# ============= TUTORIALS UPDATE VIEW ============= #
# ================================================== #
@method_decorator(csrf_exempt, name='dispatch')
class TutorialUpdateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def put(self, request, tutorial_id):
        try:
            tutorial = get_object_or_404(Tutorial, id=tutorial_id)
            data = json.loads(request.body.decode('utf-8'))
            title = data.get('title', '').strip()
            aparat_url = data.get('aparat_url', '').strip()

            if not title:
                return JsonResponse({'success': False, 'message': 'عنوان نمی‌تواند خالی باشد'}, status=400)
            if not aparat_url:
                return JsonResponse({'success': False, 'message': 'کد embed نمی‌تواند خالی باشد'}, status=400)

            tutorial.title = title
            tutorial.aparat_url = aparat_url
            tutorial.full_clean()
            tutorial.save()

            return JsonResponse({
                'success': True,
                'message': 'ویدیو با موفقیت بروزرسانی شد',
                'tutorial': {
                    'id': tutorial.id,
                    'title': tutorial.title,
                    'aparat_url': tutorial.aparat_url,
                    'shamsi_created_at': tutorial.shamsi_created_at,
                    'shamsi_updated_at': tutorial.shamsi_updated_at,
                }
            })

        except ValidationError as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error updating tutorial: {e}")
            return JsonResponse({'success': False, 'message': 'خطا در بروزرسانی ویدیو'}, status=500)


# ================================================== #
# ============= TUTORIALS DELETE VIEW ============= #
# ================================================== #
@method_decorator(csrf_exempt, name='dispatch')
class TutorialDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def delete(self, request, tutorial_id):
        try:
            tutorial = get_object_or_404(Tutorial, id=tutorial_id)
            title = tutorial.title
            tutorial.delete()
            return JsonResponse({'success': True, 'message': f'ویدیو "{title}" با موفقیت حذف شد'})
        except Exception as e:
            logger.error(f"Error deleting tutorial: {e}")
            return JsonResponse({'success': False, 'message': 'خطا در حذف ویدیو'}, status=500)


# ================================================== #
# ============= TUTORIALS EMBED VIEW ============= #
# ================================================== #
class TutorialEmbedView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def get(self, request, tutorial_id):
        try:
            tutorial = get_object_or_404(Tutorial, id=tutorial_id)
            return JsonResponse({'success': True, 'aparat_url': tutorial.aparat_url})
        except Exception as e:
            logger.error(f"Error getting embed: {e}")
            return JsonResponse({'success': False, 'message': 'خطا در دریافت کد embed'}, status=500)
