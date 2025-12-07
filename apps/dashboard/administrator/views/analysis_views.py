from django.views.generic import TemplateView, View
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from datetime import datetime, timedelta
from collections import defaultdict

from apps.accounts.models import User, Profile
from apps.subscriptions.models import Subscription, Plan, Membership, SubscriptionStatusChoicesModel
from apps.payment.models import Payment
from apps.dashboard.administrator.services.google_analytics_service import GoogleAnalyticsService

# ====== ANALYSIS DASHBOARD VIEW ====== #
class AnalysisDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/analysis/analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # آمار کاربران
        context.update(self.get_user_stats())
        
        # آمار پرداخت‌ها
        context.update(self.get_payment_stats())
        
        # آمار اشتراک‌ها
        context.update(self.get_subscription_stats())
        
        return context
    
    def get_user_stats(self):
        """آمار مربوط به کاربران"""
        # تعداد ادمین‌ها
        admin_count = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True) | Q(profile__role="admin")).count()
        
        # کاربران عادی (غیر ادمین و غیر سوپر یوزر)
        regular_users = User.objects.filter(
            is_staff=False, 
            is_superuser=False,
            profile__role__in=['visitor', 'regular']
        )
        regular_user_count = regular_users.count()
        
        # کاربران ویژه (پریمیوم)
        premium_user_count = User.objects.filter(
            profile__role='premium'
        ).count()
        
        return {
            'admin_count': admin_count,
            'regular_user_count': regular_user_count,
            'premium_user_count': premium_user_count,
        }
    
    def get_payment_stats(self):
        """آمار مربوط به پرداخت‌ها"""
        # کل درآمد
        total_income = Payment.objects.filter(
            status='COMPLETED'
        ).aggregate(total=Sum('final_amount'))['total'] or 0
        
        # درآمد امروز
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_income = Payment.objects.filter(
            status='COMPLETED',
            created_at__gte=today_start
        ).aggregate(total=Sum('final_amount'))['total'] or 0
        
        # درآمد این ماه
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_income = Payment.objects.filter(
            status='COMPLETED',
            created_at__gte=month_start
        ).aggregate(total=Sum('final_amount'))['total'] or 0
        
        return {
            'total_income': total_income,
            'today_income': today_income,
            'month_income': month_income,
        }
    
    def get_subscription_stats(self):
        """آمار مربوط به اشتراک‌ها"""
        # تعداد کل مشترکین
        total_subscribers = Subscription.objects.filter(
            status=SubscriptionStatusChoicesModel.active.value
        ).values('user').distinct().count()
        
        # تعداد پلن‌های خریداری شده
        total_plans_sold = Subscription.objects.filter(
            status=SubscriptionStatusChoicesModel.active.value).count()
        
        # مشترکین جدید این ماه
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_subscribers_this_month = Subscription.objects.filter(
            status=SubscriptionStatusChoicesModel.active.value,
            start_date__gte=month_start
        ).values('user').distinct().count()
        
        return {
            'total_subscribers': total_subscribers,
            'total_plans_sold': total_plans_sold,
            'new_subscribers_this_month': new_subscribers_this_month,
        }

# ====== USER STATS DETAIL VIEW ====== #
class UserStatsDetailView(LoginRequiredMixin, View):
    """جزئیات آمار کاربران"""
    
    def get(self, request, *args, **kwargs):
        user_type = request.GET.get('type')
        
        if user_type == 'admin':
            return self.get_admin_users()
        elif user_type == 'regular':
            return self.get_regular_users()
        elif user_type == 'premium':
            return self.get_premium_users()
        else:
            return JsonResponse({'error': 'نوع کاربر نامعتبر است'}, status=400)
    
    def get_admin_users(self):
        """لیست ادمین‌ها"""
        admins = User.objects.filter(
            Q(is_staff=True) |
            Q(is_superuser=True) |
            Q(profile__role="admin")
        ).select_related('profile').order_by('-date_joined')
        
        data = []
        for admin in admins:
            data.append({
                'id': admin.id,
                'full_name': admin.full_name,
                'phone_number': admin.phone_number,
                'email': admin.email,
                'date_joined': admin.shamsi_date_joined,
            })
        
        return JsonResponse({'users': data, 'type': 'admin'})
    
    def get_regular_users(self):
        """لیست کاربران عادی"""
        regular_users = User.objects.filter(
            is_staff=False,
            is_superuser=False,
            profile__role__in=['visitor', 'regular']
        ).select_related('profile').order_by('-date_joined')
        
        data = []
        for user in regular_users:
            data.append({
                'id': user.id,
                'full_name': user.full_name,
                'phone_number': user.phone_number,
                'email': user.email,
                'medical_code': user.profile.medical_code or '—',
                'date_joined': user.shamsi_date_joined,
            })
        
        return JsonResponse({'users': data, 'type': 'regular'})
    
    def get_premium_users(self):
        """لیست کاربران ویژه"""
        premium_users = User.objects.filter(
            profile__role='premium'
        ).select_related('profile').prefetch_related(
            'subscriptions__plan__membership'
        ).order_by('-date_joined')
        
        data = []
        for user in premium_users:
            # آخرین اشتراک فعال
            active_subscription = user.subscriptions.filter(
                status=SubscriptionStatusChoicesModel.active.value,
                end_date__gt=timezone.now()
            ).first()
            
            plan_info = None
            if active_subscription:
                plan_info = {
                    'plan_name': active_subscription.plan.name,
                    'membership': active_subscription.plan.membership.title,
                    'price': active_subscription.payment_amount,
                    'start_date': active_subscription.shamsi_start_date,
                    'end_date': active_subscription.shamsi_end_date,
                    'days_remaining': active_subscription.days_remaining,
                }
            
            data.append({
                'id': user.id,
                'full_name': user.full_name,
                'phone_number': user.phone_number,
                'email': user.email,
                'active_subscription': plan_info,
            })
        
        return JsonResponse({'users': data, 'type': 'premium'})

# ====== PAYMENTS STATS DETAIL VIEW ====== #
class PaymentStatsDetailView(LoginRequiredMixin, View):
    """جزئیات آمار پرداخت‌ها"""
    
    def get(self, request, *args, **kwargs):
        period = request.GET.get('period', 'daily')
        
        if period == 'daily':
            return self.get_daily_stats()
        elif period == 'weekly':
            return self.get_weekly_stats()
        elif period == 'monthly':
            return self.get_monthly_stats()
        else:
            return JsonResponse({'error': 'بازه زمانی نامعتبر است'}, status=400)
    
    def get_daily_stats(self):
        """آمار روزانه"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        payments = Payment.objects.filter(
            status='COMPLETED',
            created_at__range=[start_date, end_date]
        ).extra({
            'date': "DATE(created_at)"
        }).values('date').annotate(
            total_income=Sum('final_amount'),
            payment_count=Count('id')
        ).order_by('date')
        
        # گروه‌بندی بر اساس پلن
        plan_stats = Payment.objects.filter(
            status='COMPLETED',
            created_at__range=[start_date, end_date],
            subscription__isnull=False
        ).select_related('subscription__plan__membership').values(
            'subscription__plan__name',
            'subscription__plan__membership__title'
        ).annotate(
            total_income=Sum('final_amount'),
            sale_count=Count('id')
        ).order_by('-total_income')
        
        return JsonResponse({
            'period': 'daily',
            'payments': list(payments),
            'plan_stats': list(plan_stats),
        })
    
    def get_weekly_stats(self):
        """آمار هفتگی"""
        end_date = timezone.now()
        start_date = end_date - timedelta(weeks=12)
        
        payments = Payment.objects.filter(
            status='COMPLETED',
            created_at__range=[start_date, end_date]
        ).extra({
            'week': "YEARWEEK(created_at)"
        }).values('week').annotate(
            total_income=Sum('final_amount'),
            payment_count=Count('id')
        ).order_by('week')
        
        return JsonResponse({
            'period': 'weekly',
            'payments': list(payments),
        })
    
    def get_monthly_stats(self):
        """آمار ماهانه"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)
        
        payments = Payment.objects.filter(
            status='COMPLETED',
            created_at__range=[start_date, end_date]
        ).extra({
            'month': "DATE_FORMAT(created_at, '%%Y-%%m')"
        }).values('month').annotate(
            total_income=Sum('final_amount'),
            payment_count=Count('id')
        ).order_by('month')
        
        return JsonResponse({
            'period': 'monthly',
            'payments': list(payments),
        })


# ====== SUBSCRIPTION STATS DETAIL VIEW ====== #
class SubscriptionStatsDetailView(LoginRequiredMixin, View):
    """جزئیات آمار اشتراک‌ها"""
    
    def get(self, request, *args, **kwargs):
        report_type = request.GET.get('type')
        
        if report_type == 'subscribers':
            return self.get_subscribers_detail()
        elif report_type == 'plans':
            return self.get_plans_sales_detail()
        else:
            return JsonResponse({'error': 'نوع گزارش نامعتبر است'}, status=400)
    
    def get_subscribers_detail(self):
        """جزئیات مشترکین"""
        # مشترکین این ماه
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        subscribers_this_month = Subscription.objects.filter(
            status=SubscriptionStatusChoicesModel.active.value,
            start_date__gte=month_start
        ).values('user').distinct().count()
        
        # کل مشترکین
        total_subscribers = Subscription.objects.filter(status=SubscriptionStatusChoicesModel.active.value).values('user').distinct().count()
        
        # روند ماهانه مشترکین جدید
        monthly_trend = []
        for i in range(6):
            month = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i == 0:
                month_end = timezone.now()
            else:
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            count = Subscription.objects.filter(
                status=SubscriptionStatusChoicesModel.active.value,
                start_date__range=[month_start, month_end]
            ).values('user').distinct().count()
            
            monthly_trend.append({
                'month': month_start.strftime('%Y-%m'),
                'subscribers': count,
            })
        
        monthly_trend.reverse()
        
        return JsonResponse({
            'subscribers_this_month': subscribers_this_month,
            'total_subscribers': total_subscribers,
            'monthly_trend': monthly_trend,
        })
    
    def get_plans_sales_detail(self):
        """جزئیات فروش پلن‌ها بر اساس پرداخت‌های موفق"""
        
        # آمار فروش بر اساس membership و پلن - فقط پرداخت‌های موفق
        membership_stats = Membership.objects.filter(
            is_active=True
        ).prefetch_related(
            'plans__subscriptions__payments'
        ).annotate(
            # تعداد پلن‌های فروخته شده با پرداخت موفق
            total_plans_sold=Count(
                'plans__subscriptions',
                filter=Q(plans__subscriptions__payments__status='COMPLETED')
            ),
            # مجموع درآمد از پرداخت‌های موفق
            total_revenue=Sum(
                'plans__subscriptions__payments__final_amount',
                filter=Q(plans__subscriptions__payments__status='COMPLETED')
            )
        ).order_by('-total_revenue')
        
        data = []
        for membership in membership_stats:
            plans_data = []
            for plan in membership.plans.all():
                # تعداد فروش موفق این پلن
                plan_sales = plan.subscriptions.filter(
                    payments__status='COMPLETED'
                ).distinct().count()
                
                # درآمد این پلن از پرداخت‌های موفق
                plan_revenue_result = Payment.objects.filter(
                    subscription__plan=plan,
                    status='COMPLETED'
                ).aggregate(total=Sum('final_amount'))
                plan_revenue = plan_revenue_result['total'] or 0
                
                plans_data.append({
                    'id': plan.id,
                    'name': plan.name,
                    'duration_days': plan.duration_days,
                    'price': plan.price,
                    'sales_count': plan_sales,
                    'revenue': plan_revenue,
                })
            
            data.append({
                'membership_id': membership.id,
                'membership_title': membership.title,
                'total_plans_sold': membership.total_plans_sold or 0,
                'total_revenue': membership.total_revenue or 0,
                'plans': plans_data,
            })
        
        return JsonResponse({'membership_stats': data})
        

    
    def get_users_chart_data(self):
        """داده‌های نمودار کاربران"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # کاربران جدید روزانه
        new_users = User.objects.filter(
            date_joined__range=[start_date, end_date]
        ).extra({
            'date': "DATE(date_joined)"
        }).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        labels = []
        data = []
        
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_str = current_date.strftime('%Y-%m-%d')
            daily_count = 0
            
            for item in new_users:
                if item['date'].strftime('%Y-%m-%d') == date_str:
                    daily_count = item['count']
                    break
            
            labels.append(current_date.strftime('%m/%d'))
            data.append(daily_count)
            current_date += timedelta(days=1)
        
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'کاربران جدید',
                'data': data,
                'borderColor': '#10B981',
                'backgroundColor': 'rgba(16, 185, 129, 0.1)',
            }]
        })
    
    def get_subscriptions_chart_data(self):
        """داده‌های نمودار اشتراک‌ها"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # اشتراک‌های جدید روزانه
        new_subs = Subscription.objects.filter(
            start_date__range=[start_date, end_date]
        ).extra({
            'date': "DATE(start_date)"
        }).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        labels = []
        data = []
        
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_str = current_date.strftime('%Y-%m-%d')
            daily_count = 0
            
            for item in new_subs:
                if item['date'].strftime('%Y-%m-%d') == date_str:
                    daily_count = item['count']
                    break
            
            labels.append(current_date.strftime('%m/%d'))
            data.append(daily_count)
            current_date += timedelta(days=1)
        
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'اشتراک‌های جدید',
                'data': data,
                'borderColor': '#8B5CF6',
                'backgroundColor': 'rgba(139, 92, 246, 0.1)',
            }]
        })

class ChartDataView(View):
    """داده‌های نمودار"""
    
    def get(self, request, *args, **kwargs):
        chart_type = request.GET.get('type', 'income')
        
        if chart_type == 'income':
            return self.get_income_chart_data()
        elif chart_type == 'users':
            return self.get_users_chart_data()
        elif chart_type == 'subscriptions':
            return self.get_subscriptions_chart_data()
        else:
            return JsonResponse({'error': 'نوع نمودار نامعتبر است'}, status=400)
    
    def get_income_chart_data(self):
        """داده‌های نمودار درآمد"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # داده‌های روزانه
        daily_data = Payment.objects.filter(
            status='COMPLETED',
            created_at__range=[start_date, end_date]
        ).extra({
            'date': "DATE(created_at)"
        }).values('date').annotate(
            amount=Sum('final_amount')
        ).order_by('date')
        
        labels = []
        data = []
        
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_str = current_date.strftime('%Y-%m-%d')
            daily_amount = 0
            
            for item in daily_data:
                if item['date'].strftime('%Y-%m-%d') == date_str:
                    daily_amount = float(item['amount'])
                    break
            
            labels.append(current_date.strftime('%m/%d'))
            data.append(daily_amount)
            current_date += timedelta(days=1)
        
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'درآمد روزانه (ریال)',
                'data': data,
                'borderColor': '#3B82F6',
                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
            }]
        })
    
    def get_users_chart_data(self):
        """داده‌های نمودار کاربران"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # کاربران جدید روزانه
        new_users = User.objects.filter(
            date_joined__range=[start_date, end_date]
        ).extra({
            'date': "DATE(date_joined)"
        }).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        labels = []
        data = []
        
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_str = current_date.strftime('%Y-%m-%d')
            daily_count = 0
            
            for item in new_users:
                if item['date'].strftime('%Y-%m-%d') == date_str:
                    daily_count = item['count']
                    break
            
            labels.append(current_date.strftime('%m/%d'))
            data.append(daily_count)
            current_date += timedelta(days=1)
        
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'کاربران جدید',
                'data': data,
                'borderColor': '#10B981',
                'backgroundColor': 'rgba(16, 185, 129, 0.1)',
            }]
        })
    
    def get_subscriptions_chart_data(self):
        """داده‌های نمودار اشتراک‌ها"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # اشتراک‌های جدید روزانه
        new_subs = Subscription.objects.filter(
            status=SubscriptionStatusChoicesModel.active.value,
            start_date__range=[start_date, end_date]
        ).extra({
            'date': "DATE(start_date)"
        }).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        labels = []
        data = []
        
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_str = current_date.strftime('%Y-%m-%d')
            daily_count = 0
            
            for item in new_subs:
                if item['date'].strftime('%Y-%m-%d') == date_str:
                    daily_count = item['count']
                    break
            
            labels.append(current_date.strftime('%m/%d'))
            data.append(daily_count)
            current_date += timedelta(days=1)
        
        return JsonResponse({
            'labels': labels,
            'datasets': [{
                'label': 'اشتراک‌های جدید',
                'data': data,
                'borderColor': '#8B5CF6',
                'backgroundColor': 'rgba(139, 92, 246, 0.1)',
            }]
        })

# ===== Analytics Data Json View ===== #
class AnalyticsDataJsonView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            ga_service = GoogleAnalyticsService()
            raw_data = ga_service.get_last_7_days_report()
            
            labels = []
            users_data = []
            views_data = []
            new_users_data = []
            
            total_users = 0
            total_views = 0
            total_new_users = 0

            for item in raw_data:
                # تبدیل فرمت تاریخ GA4 از YYYYMMDD به YYYY-MM-DD
                # تا تابع جاوااسکریپتی شما بتواند آن را به شمسی تبدیل کند
                date_obj = datetime.strptime(item['date'], "%Y%m%d")
                formatted_date = date_obj.strftime("%Y-%m-%d")
                
                labels.append(formatted_date)
                users_data.append(item['active_users'])
                views_data.append(item['page_views'])
                new_users_data.append(item['new_users'])
                
                total_users += item['active_users']
                total_views += item['page_views']
                total_new_users += item['new_users']
                

            return JsonResponse({
                'labels': labels,
                'datasets': [
                    {
                        'label': 'کاربران فعال',
                        'data': users_data,
                        'borderColor': 'rgb(59, 130, 246)', # Blue-500
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'fill': True,
                        'tension': 0.3
                    },
                    {
                        'label': 'بازدید صفحات',
                        'data': views_data,
                        'borderColor': 'rgb(16, 185, 129)', # Emerald-500
                        'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                        'fill': True,
                        'tension': 0.3
                    },
                    {
                        'label': 'کاربران جدید',
                        'data': new_users_data,
                        'borderColor': 'rgb(139, 92, 246)', # Purple-500 (بنفش)
                        'backgroundColor': 'rgba(139, 92, 246, 0.1)',
                        'fill': True,
                        'tension': 0.3,
                        'borderDash': [5, 5] # خط‌چین برای تمایز بهتر
                    }
                ],
                'summary': {
                    'total_users': total_users,
                    'total_views': total_views,
                    'total_new_users': total_new_users
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
