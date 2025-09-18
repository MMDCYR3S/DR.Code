from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import Profile
from ..forms import UserSearchForm

import jdatetime

User = get_user_model()

# ============= ADMIN USERS LIST VIEW ============= #
class AdminUsersListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """لیست کاربران برای ادمین"""
    
    model = User
    template_name = 'dashboard/users/users.html'
    context_object_name = 'users'
    paginate_by = 15

    def test_func(self):
        """بررسی دسترسی ادمین"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        """ فیلتر و جستجوی کاربران """
        queryset = User.objects.select_related('profile').exclude(
            is_superuser=True
        ).order_by('-date_joined')
        
        search = self.request.GET.get('search', '').strip()
        role = self.request.GET.get('role', '')
        auth_status = self.request.GET.get('auth_status', '')
        sort_by = self.request.GET.get('sort_by', '-date_joined')
        
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(email__icontains=search) |
                Q(profile__medical_code__icontains=search)
            )
            
        if role:
            queryset = queryset.filter(profile__role=role)

        if auth_status:
            queryset = queryset.filter(profile__auth_status=auth_status)

        if sort_by:
            queryset = queryset.order_by(sort_by)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['search_form'] = UserSearchForm(self.request.GET)
        
        context['stats'] = {
            'total_users': User.objects.exclude(is_superuser=True).count(),
            'premium_users': Profile.objects.filter(role='premium').count(),
            'pending_verification': Profile.objects.filter(
                auth_status='PENDING'
            ).count(),
            'approved_users': Profile.objects.filter(
                auth_status='APPROVED'
            ).count(),
        }
        
        for user in context['users']:
            if user.date_joined:
                jalali_date = jdatetime.datetime.fromgregorian(
                    datetime=user.date_joined.replace(tzinfo=None)
                )
                user.jalali_date = jalali_date.strftime('%Y/%m/%d')
        
        return context
    
def get_jalali_date(date_obj):
    """ تبدیل تاریخ میلادی به شمسی """
    if date_obj:
        jalali_date = jdatetime.datetime.fromgregorian(
            datetime=date_obj.replace(tzinfo=None)
        )
        return jalali_date.strftime('%Y/%m/%d')
    return ''