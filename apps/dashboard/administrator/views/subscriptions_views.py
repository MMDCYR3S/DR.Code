from django.views.generic import View
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Max
from datetime import timedelta

from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from apps.subscriptions.models import Subscription, Plan, SubscriptionStatusChoicesModel
from apps.subscriptions.services import sync_user_profile

User = get_user_model()

# ================================================== #
# ========= SUBSCRIPTION CREATE VIEW ========= #
# ================================================== #
class SubscriptionCreateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """
    ایجاد اشتراک جدید برای کاربر.
    اگر برای همان membership یک اشتراک فعال وجود داشته باشد، اجازه نمی‌دهد
    و ادمین باید از تمدید استفاده کند.
    """

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get('user_id')
        plan_id = request.POST.get('plan_id')
        payment_amount = request.POST.get('payment_amount')

        if not all([user_id, plan_id, payment_amount]):
            return JsonResponse({
                'success': False,
                'message': 'تمام فیلدها الزامی هستند.'
            }, status=400)

        try:
            user = get_object_or_404(User, pk=user_id)
            plan = get_object_or_404(Plan, pk=plan_id)

            # فقط چک می‌کنیم برای همون membership اشتراک فعال نباشه
            has_active_same_membership = Subscription.objects.filter(
                user=user,
                status=SubscriptionStatusChoicesModel.active.value,
                end_date__gt=timezone.now(),
                plan__membership_id=plan.membership_id,
            ).exists()

            if has_active_same_membership:
                return JsonResponse({
                    'success': False,
                    'message': f'کاربر در حال حاضر یک اشتراک فعال برای «{plan.membership.title}» دارد. لطفاً از گزینه تمدید استفاده کنید.'
                }, status=400)

            start_date = timezone.now()
            end_date = start_date + timedelta(days=plan.duration_days)

            with transaction.atomic():
                subscription = Subscription.objects.create(
                    user=user,
                    plan=plan,
                    payment_amount=payment_amount,
                    status=SubscriptionStatusChoicesModel.active.value,
                    end_date=end_date,
                )
                sync_user_profile(user)

            return JsonResponse({
                'success': True,
                'message': f'اشتراک «{plan.membership.title}» برای {user.full_name} با موفقیت ایجاد شد.',
                'subscription': {
                    'id': subscription.id,
                    'plan_name': subscription.plan.name,
                    'start_date': subscription.shamsi_start_date,
                    'end_date': subscription.shamsi_end_date,
                    'status': subscription.get_status_display(),
                    'days_remaining': subscription.days_remaining
                }
            }, status=201)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در ایجاد اشتراک: {str(e)}'
            }, status=500)


# ================================================== #
# ========= SUBSCRIPTION UPDATE VIEW ========= #
# ================================================== #
class SubscriptionUpdateView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """
    ویو برای ویرایش اشتراک موجود کاربر.
    """
    
    def get(self, request, pk, *args, **kwargs):
        """دریافت اطلاعات اشتراک برای نمایش در مودال"""
        try:
            subscription = get_object_or_404(
                Subscription.objects.select_related('user', 'plan'),
                pk=pk
            )
            
            return JsonResponse({
                'success': True,
                'subscription': {
                    'id': subscription.id,
                    'user_id': subscription.user.id,
                    'user_name': subscription.user.full_name,
                    'plan_id': subscription.plan.id,
                    'plan_name': subscription.plan.name,
                    'payment_amount': str(subscription.payment_amount),
                    'status': subscription.status,
                    'start_date': subscription.shamsi_start_date,
                    'end_date': subscription.shamsi_end_date,
                    'days_remaining': subscription.days_remaining
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در دریافت اطلاعات اشتراک: {str(e)}'
            }, status=500)
    
    def post(self, request, pk, *args, **kwargs):
        """ ویرایش اطلاعات اشتراک """
        try:
            subscription = get_object_or_404(
                Subscription.objects.select_related('user', 'plan', 'user__profile'),
                pk=pk
            )
            
            plan_id = request.POST.get('plan_id')
            payment_amount = request.POST.get('payment_amount')
            status = request.POST.get('status')
            duration_days = request.POST.get('duration_days')
            
            with transaction.atomic():
                # بروزرسانی پلن (در صورت تغییر)
                if plan_id and str(subscription.plan.id) != plan_id:
                    plan = get_object_or_404(Plan, pk=plan_id)
                    subscription.plan = plan
                    # محاسبه مجدد تاریخ انقضا بر اساس پلن جدید
                    subscription.end_date = subscription.start_date + timedelta(days=plan.duration_days)

                    profile = subscription.user.profile
                    profile.subscription_end_date = subscription.end_date
                    profile.save()
                
                # بروزرسانی مبلغ
                if payment_amount:
                    subscription.payment_amount = payment_amount
                
                # بروزرسانی وضعیت
                if status and status in dict(SubscriptionStatusChoicesModel.choices):
                    old_status = subscription.status
                    subscription.status = status
                    
                    # اگر وضعیت به expired یا canceled تغییر کرد، نقش کاربر را برگردان
                    if status in [SubscriptionStatusChoicesModel.expired.value, 
                                SubscriptionStatusChoicesModel.canceled.value]:
                        profile = subscription.user.profile
                        profile.role = 'regular'
                        profile.save()
                    # اگر وضعیت به active تغییر کرد، نقش را به premium تغییر بده
                    elif status == SubscriptionStatusChoicesModel.active.value and \
                            old_status != SubscriptionStatusChoicesModel.active.value:
                        profile = subscription.user.profile
                        profile.subscription_end_date = subscription.end_date
                        if not profile.role == 'admin':
                            profile.role = 'premium'
                        profile.save()
                
                # تمدید اشتراک (اضافه کردن روز)
                if duration_days:
                    try:
                        days = int(duration_days)
                        subscription.end_date = subscription.end_date + timedelta(days=days)
                        # 🔥 اینجا هم باید بروزرسانی کنی
                        profile = subscription.user.profile
                        profile.subscription_end_date = subscription.end_date
                        profile.save()
                    except ValueError:
                        pass
                
                subscription.save()
            
            return JsonResponse({
                'success': True,
                'message': f'اشتراک کاربر {subscription.user.full_name} با موفقیت بروزرسانی شد.',
                'subscription': {
                    'id': subscription.id,
                    'plan_name': subscription.plan.name,
                    'start_date': subscription.shamsi_start_date,
                    'end_date': subscription.shamsi_end_date,
                    'status': subscription.get_status_display(),
                    'days_remaining': subscription.days_remaining
                }
            })
            
        except Subscription.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'اشتراک مورد نظر یافت نشد.'
            }, status=404)
        except Plan.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'پلن مورد نظر یافت نشد.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در بروزرسانی اشتراک: {str(e)}'
            }, status=500)



# ================================================== #
# ========= SUBSCRIPTION DELETE VIEW ========= #
# ================================================== #
class SubscriptionDeleteView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):

    def post(self, request, pk, *args, **kwargs):
        try:
            subscription = get_object_or_404(
                Subscription.objects.select_related('user'),
                pk=pk
            )
            user = subscription.user
            user_name = user.full_name

            with transaction.atomic():
                subscription.delete()
                sync_user_profile(user)

            return JsonResponse({
                'success': True,
                'message': f'اشتراک {user_name} با موفقیت حذف شد.'
            })

        except Subscription.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'اشتراک مورد نظر یافت نشد.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در حذف اشتراک: {str(e)}'
            }, status=500)


# ================================================== #
# ========= USER SUBSCRIPTION DETAIL VIEW ========= #
# ================================================== #
class UserSubscriptionDetailView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):

    def get(self, request, user_id, *args, **kwargs):
        try:
            user = get_object_or_404(User, pk=user_id)
            now = timezone.now()

            subscriptions = Subscription.objects.filter(
                user=user
            ).select_related('plan', 'plan__membership').order_by('-end_date')

            subscriptions_data = []
            active_subscriptions = []

            for sub in subscriptions:
                item = {
                    'id': sub.id,
                    'plan_name': sub.plan.name,
                    'membership_id': sub.plan.membership_id,
                    'membership_title': sub.plan.membership.title,
                    'payment_amount': str(sub.payment_amount),
                    'status': sub.status,
                    'status_display': sub.get_status_display(),
                    'start_date': sub.shamsi_start_date,
                    'end_date': sub.shamsi_end_date,
                    'days_remaining': sub.days_remaining,
                    'is_active': sub.is_active,
                }
                subscriptions_data.append(item)
                if sub.is_active:
                    active_subscriptions.append(item)

            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'full_name': user.full_name,
                    'role': user.profile.get_role_display()
                },
                'active_count': len(active_subscriptions),
                'has_active_subscription': len(active_subscriptions) > 0,
                'active_subscriptions': active_subscriptions,
                'subscriptions': subscriptions_data,
                'total_count': len(subscriptions_data)
            })

        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'کاربر مورد نظر یافت نشد.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در دریافت اطلاعات: {str(e)}'
            }, status=500)


# ================================================== #
# ========= GET AVAILABLE PLANS VIEW ========= #
# ================================================== #
class GetAvailablePlansView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):
    """
    ویو برای دریافت لیست پلن‌های موجود برای انتخاب.
    """
    
    def get(self, request, *args, **kwargs):
        """دریافت لیست پلن‌های فعال"""
        try:
            plans = Plan.objects.filter(
                is_active=True
            ).select_related('membership').order_by('duration_days')
            
            plans_data = []
            for plan in plans:
                plans_data.append({
                    'id': plan.id,
                    'name': plan.name,
                    'membership': plan.membership.title,
                    'duration_days': plan.duration_days,
                    'duration_months': plan.duration_months,
                    'price': str(plan.price)
                })
            
            return JsonResponse({
                'success': True,
                'plans': plans_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در دریافت لیست پلن‌ها: {str(e)}'
            }, status=500)


# ================================================== #
# ========= SUBSCRIPTION EXTEND VIEW ========= #
# ================================================== #
class SubscriptionExtendView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, View):

    def post(self, request, pk, *args, **kwargs):
        try:
            subscription = get_object_or_404(
                Subscription.objects.select_related('user'),
                pk=pk
            )

            days_to_add = request.POST.get('days_to_add')
            if not days_to_add:
                return JsonResponse({
                    'success': False,
                    'message': 'تعداد روز برای تمدید مشخص نشده است.'
                }, status=400)

            try:
                days = int(days_to_add)
                if days <= 0:
                    raise ValueError("تعداد روز باید مثبت باشد.")
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'message': f'تعداد روز معتبر نیست: {str(e)}'
                }, status=400)

            with transaction.atomic():
                # اگر اشتراک قبلاً منقضی شده، از الان شروع کن
                if subscription.end_date < timezone.now():
                    subscription.start_date = timezone.now()
                    subscription.end_date = timezone.now() + timedelta(days=days)
                else:
                    subscription.end_date = subscription.end_date + timedelta(days=days)

                subscription.status = SubscriptionStatusChoicesModel.active.value
                subscription.save()
                sync_user_profile(subscription.user)

            return JsonResponse({
                'success': True,
                'message': f'اشتراک {subscription.user.full_name} با موفقیت {days} روز تمدید شد.',
                'subscription': {
                    'id': subscription.id,
                    'end_date': subscription.shamsi_end_date,
                    'days_remaining': subscription.days_remaining
                }
            })

        except Subscription.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'اشتراک مورد نظر یافت نشد.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در تمدید اشتراک: {str(e)}'
            }, status=500)
