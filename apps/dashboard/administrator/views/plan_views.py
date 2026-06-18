from django.views.generic import ListView, View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
import json
from apps.subscriptions.models import Plan, Membership, Feature, FeatureType
from ..forms import PlanForm, MembershipForm, FeatureForm


# ========================== #
# ========== PLAN ========== #
# ========================== #
class PlanListView(LoginRequiredMixin, ListView):
    model = Plan
    template_name = 'dashboard/plans/plan_list.html'
    context_object_name = 'plans'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['memberships'] = Membership.objects.prefetch_related('features').all() 
        context['features'] = Feature.objects.all()
        context['feature_types'] = FeatureType.choices
        return context

class PlanCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            form = PlanForm(data)
            if form.is_valid():
                plan = form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'پلن جدید با موفقیت ایجاد شد.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'لطفا خطاهای فرم را برطرف کنید.',
                    'errors': form.errors
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در ایجاد پلن: {str(e)}'
            })

class PlanUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            plan = get_object_or_404(Plan, pk=pk)
            data = json.loads(request.body)
            form = PlanForm(data, instance=plan)
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'پلن با موفقیت بروزرسانی شد.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'لطفا خطاهای فرم را برطرف کنید.',
                    'errors': form.errors
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در بروزرسانی پلن: {str(e)}'
            })

class PlanDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            plan = get_object_or_404(Plan, pk=pk)
            plan.delete()
            return JsonResponse({
                'success': True,
                'message': 'پلن با موفقیت حذف شد.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در حذف پلن: {str(e)}'
            })


# ================================ #
# ========== MEMBERSHIP ========== #
# ================================ #
class MembershipDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            membership = get_object_or_404(Membership, pk=pk)
            return JsonResponse({
                'success': True,
                'data': {
                    'title': membership.title,
                    'description': membership.description,
                    'is_active': membership.is_active,
                    'features': list(membership.features.values_list('id', flat=True)) 
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در دریافت اطلاعات: {str(e)}'
            })

class MembershipCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            form = MembershipForm(data)
            if form.is_valid():
                membership = form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Membership جدید با موفقیت ایجاد شد.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'لطفا خطاهای فرم را برطرف کنید.',
                    'errors': form.errors
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در ایجاد membership: {str(e)}'
            })

class MembershipUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            membership = get_object_or_404(Membership, pk=pk)
            data = json.loads(request.body)
            form = MembershipForm(data, instance=membership)
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Membership با موفقیت بروزرسانی شد.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'لطفا خطاهای فرم را برطرف کنید.',
                    'errors': form.errors
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در بروزرسانی membership: {str(e)}'
            })

class MembershipDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            membership = get_object_or_404(Membership, pk=pk)
            membership.delete()
            return JsonResponse({
                'success': True,
                'message': 'Membership با موفقیت حذف شد.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در حذف membership: {str(e)}'
            })

# ویو برای گرفتن اطلاعات پلن
class PlanDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            plan = get_object_or_404(Plan, pk=pk)
            return JsonResponse({
                'success': True,
                'data': {
                    'membership': plan.membership.id,
                    'name': plan.name,
                    'duration_days': plan.duration_days,
                    'price': str(plan.price),
                    'is_active': plan.is_active
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در دریافت اطلاعات پلن: {str(e)}'
            })

# ============================== #
# ========== FEATURES ========== #
# ============================== #
class FeatureCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            form = FeatureForm(data)
            
            if form.is_valid():
                feature = form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'ویژگی با موفقیت اضافه شد.',
                    'data': {
                        'id': feature.id,
                        'name': feature.name,
                        'slug': feature.slug,
                        'feature_type': feature.get_feature_type_display()
                    }
                })
            
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'فرمت JSON نامعتبر است.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطای سرور: {str(e)}'
            }, status=500)


class FeatureDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        feature = get_object_or_404(Feature, pk=pk)
        return JsonResponse({
            'success': True,
            'data': {
                'id': feature.id,
                'name': feature.name,
                'slug': feature.slug,
                'feature_type': feature.feature_type,
                'description': feature.description,
                'is_active': feature.is_active
            }
        })


class FeatureUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            feature = get_object_or_404(Feature, pk=pk)
            data = json.loads(request.body)
            form = FeatureForm(data, instance=feature)
            
            if form.is_valid():
                updated_feature = form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'ویژگی با موفقیت ویرایش شد.',
                    'data': {
                        'id': updated_feature.id,
                        'name': updated_feature.name,
                        'slug': updated_feature.slug,
                        'feature_type': updated_feature.get_feature_type_display()
                    }
                })
            
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'فرمت JSON نامعتبر است.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطای سرور: {str(e)}'
            }, status=500)


class FeatureDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            feature = get_object_or_404(Feature, pk=pk)
            feature_name = feature.name
            feature.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'ویژگی "{feature_name}" با موفقیت حذف شد.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در حذف: {str(e)}'
            }, status=500)
