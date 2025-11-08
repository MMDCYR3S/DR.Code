# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from django.core.cache import cache
from django.db.models.functions import TruncMonth

from datetime import timedelta
from decimal import Decimal

from apps.accounts.models import Profile, AuthStatusChoices
from apps.subscriptions.models import Subscription, SubscriptionStatusChoicesModel
from apps.questions.models import Question
from apps.payment.models import Payment, PaymentStatus
from apps.home.models import Contact

User = get_user_model()

@login_required
def admin_dashboard_view(request):
    """
    ویو داشبورد ادمین با نمایش آمارهای کلیدی
    """
    if not (request.user.is_staff or request.user.is_superuser or getattr(request.user.profile, "role", None) == "admin"):
        return render(request, '403.html', status=403)
    
    cache_key = 'admin_dashboard_stats'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        context = cached_data
    else:
        context = _calculate_dashboard_stats()
        cache.set(cache_key, context, timeout=20)

    context.update(_get_realtime_data())
    
    return render(request, 'dashboard/index/dashboard.html', context)

def _calculate_dashboard_stats():
    """محاسبه آمارهای داشبورد"""
    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    current_month_revenue = (
        Payment.objects
        .filter(
            status=PaymentStatus.COMPLETED,
            paid_at__gte=current_month_start
        )
        .aggregate(
            total=Sum('final_amount')
        )['total'] or Decimal('0')
    )
    
    last_month_revenue = (
        Payment.objects
        .filter(
            status=PaymentStatus.COMPLETED,
            paid_at__gte=last_month_start,
            paid_at__lt=current_month_start,
            subscription__status=SubscriptionStatusChoicesModel.active.value
        )
        .aggregate(
            total=Sum('final_amount')
        )['total'] or Decimal('0')
    )
        
    # محاسبه درصد رشد
    growth_percentage = 0
    if last_month_revenue > 0:
        growth_percentage = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
    
    # تعداد کاربران ویژه فعال
    active_premium_users = User.objects.filter(
        subscriptions__status=SubscriptionStatusChoicesModel.active.value,
        subscriptions__end_date__gt=now
    ).distinct().count()
    
    # کاربران در صف احراز هویت
    pending_verification_count = Profile.objects.filter(
        auth_status=AuthStatusChoices.PENDING.value,
        documents__isnull=False
    ).count()
    
    # سوالات بدون پاسخ
    unanswered_questions_count = Question.objects.filter(
        is_answered=False
    ).count()
    
    # نمودار درآمد ۶ ماه اخیر
    six_months_ago = current_month_start - timedelta(days=180)
    monthly_revenue = Subscription.objects.filter(
        status=SubscriptionStatusChoicesModel.active.value,
        start_date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        revenue=Sum('payment_amount')
    ).order_by('month')
    
    return {
        'current_month_revenue': current_month_revenue,
        'growth_percentage': round(growth_percentage, 1),
        'active_premium_users': active_premium_users,
        'pending_verification_count': pending_verification_count,
        'unanswered_questions_count': unanswered_questions_count,
        'monthly_revenue_chart': list(monthly_revenue),
    }

def _get_realtime_data():
    """داده‌هایی که باید همیشه به‌روز باشند"""
    
    # آخرین کاربران در صف احراز هویت (۳ نفر)
    pending_users = Profile.objects.select_related('user').filter(
        auth_status=AuthStatusChoices.PENDING.value,
        documents__isnull=False
    ).order_by('-created_at')[:3]
    
    # آخرین سوالات بدون پاسخ (۳ سوال)
    recent_questions = Question.objects.select_related(
        'user', 'prescription'
    ).filter(
        is_answered=False
    ).order_by('-created_at')[:3]
    
    # آخرین پیام‌های تماس با ما (۴ پیام)
    recent_contacts = Contact.objects.filter(
        status__in=['pending', 'in_progress']
    ).order_by('-created_at')[:4]
    
    return {
        'pending_users': pending_users,
        'recent_questions': recent_questions,
        'recent_contacts': recent_contacts,
    }
