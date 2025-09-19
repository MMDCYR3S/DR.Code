from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.generic import TemplateView, View
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from apps.home.models import Tutorial
import json

# ================================================ #
# ============= TUTORIALS LIST VIEW ============= #
# ================================================ #
@method_decorator(staff_member_required, name='dispatch')
class TutorialsListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, TemplateView):
    template_name = 'dashboard/tutorials/tutorials.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all tutorials
        tutorials = Tutorial.get_all_tutorials()
        
        # Calculate statistics
        tutorials_count = len(tutorials)
        recent_tutorials_count = len([t for t in tutorials if t.is_recent()])
        total_views = sum([getattr(t, 'views_count', 0) for t in tutorials])
        
        # Prepare tutorials data for JavaScript
        tutorials_data = []
        for tutorial in tutorials:
            # اطمینان از timezone aware بودن datetime ها
            created_at = tutorial.created_at
            updated_at = tutorial.updated_at
            
            if timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)
            if timezone.is_naive(updated_at):
                updated_at = timezone.make_aware(updated_at)
            
            tutorials_data.append({
                'id': tutorial.id,
                'title': tutorial.title,
                'description': tutorial.description,
                'aparat_url': tutorial.aparat_url,
                'shamsi_created_at': tutorial.shamsi_created_at,
                'shamsi_updated_at': tutorial.shamsi_updated_at,
                'created_at': created_at.isoformat(),
                'updated_at': updated_at.isoformat(),
            })
        
        context.update({
            'tutorials_json': json.dumps(tutorials_data, ensure_ascii=False),
            'tutorials_count': tutorials_count,
            'recent_tutorials_count': recent_tutorials_count,
            'total_views': total_views,
        })
        
        return context

# ================================================== #
# ============= TUTORIALS CREATE VIEW ============= #
# ================================================== #
@method_decorator(staff_member_required, name='dispatch')
class TutorialCreateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Create new tutorial
            tutorial = Tutorial(
                title=data.get('title', '').strip(),
                description=data.get('description', '').strip(),
                aparat_url=data.get('aparat_url', '').strip()
            )
            
            # Validate
            tutorial.full_clean()
            tutorial.save()
            
            # Return tutorial data
            created_at = tutorial.created_at
            updated_at = tutorial.updated_at
            
            if timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)
            if timezone.is_naive(updated_at):
                updated_at = timezone.make_aware(updated_at)
            
            tutorial_data = {
                'id': tutorial.id,
                'title': tutorial.title,
                'description': tutorial.description,
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
            return JsonResponse({
                'success': False,
                'errors': e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': [str(e)]}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در ایجاد ویدیو: {str(e)}'
            }, status=400)

# ================================================== #
# ============= TUTORIALS UPDATE VIEW ============= #
# ================================================== #
@method_decorator(staff_member_required, name='dispatch')
class TutorialUpdateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def put(self, request, tutorial_id):
        try:
            tutorial = get_object_or_404(Tutorial, id=tutorial_id)
            data = json.loads(request.body)
            
            # Update tutorial fields
            tutorial.title = data.get('title', tutorial.title).strip()
            tutorial.description = data.get('description', tutorial.description).strip()
            tutorial.aparat_url = data.get('aparat_url', tutorial.aparat_url).strip()
            
            # Validate and save
            tutorial.full_clean()
            tutorial.save()
            
            # Return updated tutorial data
            created_at = tutorial.created_at
            updated_at = tutorial.updated_at
            
            if timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)
            if timezone.is_naive(updated_at):
                updated_at = timezone.make_aware(updated_at)
            
            tutorial_data = {
                'id': tutorial.id,
                'title': tutorial.title,
                'description': tutorial.description,
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
            return JsonResponse({
                'success': False,
                'errors': e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': [str(e)]}
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در بروزرسانی ویدیو: {str(e)}'
            }, status=400)

# ================================================== #
# ============= TUTORIALS DELETE VIEW ============= #
# ================================================== #
@method_decorator(staff_member_required, name='dispatch')
class TutorialDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    def delete(self, request, tutorial_id):
        try:
            tutorial = get_object_or_404(Tutorial, id=tutorial_id)
            tutorial_title = tutorial.title
            tutorial.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'ویدیو "{tutorial_title}" با موفقیت حذف شد'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در حذف ویدیو: {str(e)}'
            }, status=400)
