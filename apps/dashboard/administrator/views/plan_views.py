from django.views.generic import ListView, DetailView, View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
import json

from apps.subscriptions.models import Plan, Membership, Feature, FeatureType, PlanTag
from ..forms import PlanForm, MembershipForm, FeatureForm


# ========================== #
# ========== PLAN ========== #
# ========================== #
class PlanListView(LoginRequiredMixin, ListView):
    model = Membership
    template_name = 'dashboard/plans/list.html'
    context_object_name = 'memberships'

    def get_queryset(self):
        return Membership.objects.prefetch_related('plans', 'features').order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['breadcrumb'] = [
            {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')},
            {'label': 'مدیریت پلن‌ها و Membership‌ها', 'url': ''}
        ]

        context['stats'] = {
            'total_memberships': Membership.objects.count(),
            'active_memberships': Membership.objects.filter(is_active=True).count(),
            'total_plans': Plan.objects.count(),
        }

        context['features'] = Feature.objects.all().order_by('feature_type', 'name')
        context['feature_types'] = FeatureType.choices
        context['plan_tags'] = PlanTag.choices

        return context


class PlanCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
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
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'داده‌های ارسالی معتبر نیست.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در ایجاد پلن: {str(e)}'
            }, status=500)


class PlanUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            plan = get_object_or_404(Plan, pk=pk)
            data = json.loads(request.body.decode('utf-8'))
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
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'داده‌های ارسالی معتبر نیست.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در بروزرسانی پلن: {str(e)}'
            }, status=500)


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
            }, status=500)


class PlanDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            plan = get_object_or_404(Plan, pk=pk)
            return JsonResponse({
                'success': True,
                'data': {
                    'membership': plan.membership.id,
                    'name': plan.name,
                    'tag': plan.tag or '',
                    'duration_days': plan.duration_days,
                    'price': str(plan.price),
                    'is_active': plan.is_active
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در دریافت اطلاعات پلن: {str(e)}'
            }, status=500)


# ================================ #
# ========== MEMBERSHIP ========== #
# ================================ #
class MembershipListView(PlanListView):
    pass


class MembershipDetailView(LoginRequiredMixin, DetailView):
    model = Membership
    template_name = 'dashboard/plans/detail.html'
    context_object_name = 'membership'

    def get_queryset(self):
        return Membership.objects.prefetch_related('plans', 'features').select_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['breadcrumb'] = [
            {'label': 'داشبورد', 'url': reverse_lazy('dashboard:index:index')},
            {'label': 'مدیریت پلن‌ها و Membership‌ها', 'url': reverse_lazy('dashboard:plans:plan_list')},
            {'label': self.object.title, 'url': ''}
        ]

        context['all_features'] = Feature.objects.all().order_by('feature_type', 'name')
        context['feature_types'] = FeatureType.choices
        context['plan_tags'] = PlanTag.choices

        return context


class MembershipCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
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
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'داده‌های ارسالی معتبر نیست.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در ایجاد membership: {str(e)}'
            }, status=500)


class MembershipUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            membership = get_object_or_404(Membership, pk=pk)
            data = json.loads(request.body.decode('utf-8'))
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
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'داده‌های ارسالی معتبر نیست.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در بروزرسانی membership: {str(e)}'
            }, status=500)


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
            }, status=500)


# ============================== #
# ========== FEATURES ========== #
# ============================== #
class FeatureCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
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
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'داده‌های ارسالی معتبر نیست.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطای سرور: {str(e)}'
            }, status=500)


class FeatureDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
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
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در دریافت اطلاعات: {str(e)}'
            }, status=500)


class FeatureUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            feature = get_object_or_404(Feature, pk=pk)
            data = json.loads(request.body.decode('utf-8'))
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
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'داده‌های ارسالی معتبر نیست.'
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
