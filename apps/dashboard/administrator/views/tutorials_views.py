from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from apps.home.models import Tutorial
import json
import logging

logger = logging.getLogger(__name__)

# ================================================ #
# ============= TUTORIALS LIST VIEW ============= #
# ================================================ #
# ================================================ #
# ============= TUTORIALS LIST VIEW ============= #
# ================================================ #
class TutorialsListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, TemplateView):
    template_name = 'dashboard/tutorials/tutorials.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            tutorials = Tutorial.objects.all().order_by('-created_at')
            
            logger.info(f"Found {tutorials.count()} tutorials")
            
            # محاسبه آمار
            tutorials_count = tutorials.count()
            recent_tutorials_count = sum(1 for t in tutorials if t.is_recent)
            total_views = 0
            
            # آماده‌سازی داده برای JavaScript - بدون aparat_url
            tutorials_data = []
            for tutorial in tutorials:
                try:
                    created_at = tutorial.created_at
                    updated_at = tutorial.updated_at
                    
                    if timezone.is_naive(created_at):
                        created_at = timezone.make_aware(created_at)
                    if timezone.is_naive(updated_at):
                        updated_at = timezone.make_aware(updated_at)
                    
                    tutorials_data.append({
                        'id': tutorial.id,
                        'title': tutorial.title,
                        'shamsi_created_at': tutorial.shamsi_created_at,
                        'shamsi_updated_at': tutorial.shamsi_updated_at,
                        'created_at': created_at.isoformat(),
                        'updated_at': updated_at.isoformat(),
                    })
                except Exception as e:
                    logger.error(f"Error processing tutorial {tutorial.id}: {e}")
                    continue
            
            logger.info(f"Prepared {len(tutorials_data)} tutorials for JSON")
            
            tutorials_json = json.dumps(tutorials_data, ensure_ascii=False)
            
            context.update({
                'tutorials_json': tutorials_json,
                'tutorials_count': tutorials_count,
                'recent_tutorials_count': recent_tutorials_count,
                'total_views': total_views,
            })
            
        except Exception as e:
            logger.error(f"Error in TutorialsListView: {e}")
            context.update({
                'tutorials_json': '[]',
                'tutorials_count': 0,
                'recent_tutorials_count': 0,
                'total_views': 0,
            })
        
        return context

# ================================================== #
# ============= TUTORIALS CREATE VIEW ============= #
# ================================================== #
@method_decorator(csrf_exempt, name='dispatch')
class TutorialCreateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def post(self, request):
        try:
            # خواندن داده از body
            data = json.loads(request.body.decode('utf-8'))
            
            logger.info(f"Creating tutorial with data: {data.get('title', 'NO TITLE')}")
            
            title = data.get('title', '').strip()
            aparat_url = data.get('aparat_url', '').strip()
            
            # بررسی خالی نبودن فیلدها
            if not title:
                return JsonResponse({
                    'success': False,
                    'errors': {'title': ['عنوان نمی‌تواند خالی باشد']}
                }, status=400)
            
            if not aparat_url:
                return JsonResponse({
                    'success': False,
                    'errors': {'aparat_url': ['کد embed نمی‌تواند خالی باشد']}
                }, status=400)
            
            # ایجاد ویدیو جدید
            tutorial = Tutorial(
                title=title,
                aparat_url=aparat_url
            )
            
            # اعتبارسنجی
            tutorial.full_clean()
            tutorial.save()
            
            logger.info(f"Tutorial created successfully: {tutorial.id}")
            
            # آماده‌سازی پاسخ
            created_at = tutorial.created_at
            updated_at = tutorial.updated_at
            
            if timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)
            if timezone.is_naive(updated_at):
                updated_at = timezone.make_aware(updated_at)
            
            tutorial_data = {
                'id': tutorial.id,
                'title': tutorial.title,
                'aparat_url': tutorial.aparat_url,
                'shamsi_created_at': tutorial.shamsi_created_at,
                'shamsi_updated_at': tutorial.shamsi_updated_at,
                'created_at': created_at.isoformat(),
                'updated_at': updated_at.isoformat(),
            }
            
            return JsonResponse({
                'success': True,
                'message': 'ویدیو آموزشی با موفقیت ایجاد شد',
                'tutorial': tutorial_data
            })
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return JsonResponse({
                'success': False,
                'errors': e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': [str(e)]}
            }, status=400)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'فرمت داده ارسالی نامعتبر است'
            }, status=400)
        except Exception as e:
            logger.error(f"Error creating tutorial: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'خطا در ایجاد ویدیو: {str(e)}'
            }, status=500)


# ================================================== #
# ============= TUTORIALS UPDATE VIEW ============= #
# ================================================== #
@method_decorator(csrf_exempt, name='dispatch')
class TutorialUpdateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def put(self, request, tutorial_id):
        try:
            # یافتن ویدیو
            tutorial = get_object_or_404(Tutorial, id=tutorial_id)
            
            # خواندن داده
            data = json.loads(request.body.decode('utf-8'))
            
            logger.info(f"Updating tutorial {tutorial_id}")
            
            title = data.get('title', '').strip()
            aparat_url = data.get('aparat_url', '').strip()
            
            # بررسی خالی نبودن فیلدها
            if not title:
                return JsonResponse({
                    'success': False,
                    'errors': {'title': ['عنوان نمی‌تواند خالی باشد']}
                }, status=400)
            
            if not aparat_url:
                return JsonResponse({
                    'success': False,
                    'errors': {'aparat_url': ['کد embed نمی‌تواند خالی باشد']}
                }, status=400)
            
            # بروزرسانی فیلدها
            tutorial.title = title
            tutorial.aparat_url = aparat_url
            
            # اعتبارسنجی و ذخیره
            tutorial.full_clean()
            tutorial.save()
            
            logger.info(f"Tutorial {tutorial_id} updated successfully")
            
            # آماده‌سازی پاسخ
            created_at = tutorial.created_at
            updated_at = tutorial.updated_at
            
            if timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)
            if timezone.is_naive(updated_at):
                updated_at = timezone.make_aware(updated_at)
            
            tutorial_data = {
                'id': tutorial.id,
                'title': tutorial.title,
                'aparat_url': tutorial.aparat_url,
                'shamsi_created_at': tutorial.shamsi_created_at,
                'shamsi_updated_at': tutorial.shamsi_updated_at,
                'created_at': created_at.isoformat(),
                'updated_at': updated_at.isoformat(),
            }
            
            return JsonResponse({
                'success': True,
                'message': 'ویدیو آموزشی با موفقیت بروزرسانی شد',
                'tutorial': tutorial_data
            })
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return JsonResponse({
                'success': False,
                'errors': e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': [str(e)]}
            }, status=400)
        except Tutorial.DoesNotExist:
            logger.error(f"Tutorial {tutorial_id} not found")
            return JsonResponse({
                'success': False,
                'message': 'ویدیو مورد نظر یافت نشد'
            }, status=404)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'فرمت داده ارسالی نامعتبر است'
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating tutorial: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'خطا در بروزرسانی ویدیو: {str(e)}'
            }, status=500)


# ================================================== #
# ============= TUTORIALS DELETE VIEW ============= #
# ================================================== #
@method_decorator(csrf_exempt, name='dispatch')
class TutorialDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def delete(self, request, tutorial_id):
        try:
            # یافتن ویدیو
            tutorial = get_object_or_404(Tutorial, id=tutorial_id)
            tutorial_title = tutorial.title
            
            logger.info(f"Deleting tutorial {tutorial_id}: {tutorial_title}")
            
            # حذف ویدیو
            tutorial.delete()
            
            logger.info(f"Tutorial {tutorial_id} deleted successfully")
            
            return JsonResponse({
                'success': True,
                'message': f'ویدیو "{tutorial_title}" با موفقیت حذف شد'
            })
            
        except Tutorial.DoesNotExist:
            logger.error(f"Tutorial {tutorial_id} not found")
            return JsonResponse({
                'success': False,
                'message': 'ویدیو مورد نظر یافت نشد'
            }, status=404)
        except Exception as e:
            logger.error(f"Error deleting tutorial: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'خطا در حذف ویدیو: {str(e)}'
            }, status=500)

# ================================================== #
# ============= TUTORIALS EMBED VIEW ============= #
# ================================================== #
class TutorialEmbedView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def get(self, request, tutorial_id):
        try:
            tutorial = get_object_or_404(Tutorial, id=tutorial_id)
            return JsonResponse({
                'success': True,
                'aparat_url': tutorial.aparat_url
            })
        except Tutorial.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'ویدیو مورد نظر یافت نشد'
            }, status=404)
        except Exception as e:
            logger.error(f"Error getting embed code: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'خطا در دریافت کد embed'
            }, status=500)

