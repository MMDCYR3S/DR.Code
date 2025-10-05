from django.views.generic import ListView, View, DetailView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.shortcuts import render
from django.db import transaction
from django.contrib import messages

from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from apps.accounts.models import Profile, AuthStatusChoices
from ..forms import UserSearchForm, UserEditForm, ProfileEditForm, AddUserForm
from ..services.email_service import resend_auth_email, send_auth_checked_email

import jdatetime

User = get_user_model()

# ================================================== #
# ============= ADMIN USERS LIST VIEW ============= #
# ================================================== #
class AdminUsersListView(LoginRequiredMixin, IsTokenJtiActive, HasAdminAccessPermission, ListView):
    """لیست کاربران برای ادمین"""
    
    model = User
    template_name = 'dashboard/users/users.html'
    context_object_name = 'users'
    paginate_by = 15

    def get_queryset(self):
        """ فیلتر و جستجوی کاربران """
        queryset = User.objects.select_related('profile').all()
        form = UserSearchForm(self.request.GET)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            role = form.cleaned_data.get('role')
            auth_status = form.cleaned_data.get('auth_status')
            sort_by = form.cleaned_data.get('sort_by')
        
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
        
        context['search_form'] = UserSearchForm(self.request.GET or None)
        
        context['stats'] = {
            'total_users': User.objects.count(),
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

# ================================================== #
# ======== USER UPDATE VIEW ======== #
# ================================================== #
class UserUpdateView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ ویو برای دریافت اطلاعات و ویرایش کاربر (اصلاح شده) """
    
    def get(self, request, pk):
        """ اطلاعات کاربر را برای نمایش در مودال به صورت JSON برمی‌گرداند """
        user = get_object_or_404(User.objects.select_related('profile'), pk=pk)
        data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_active': user.is_active,
            'role': user.profile.role,
            'auth_status': user.profile.auth_status,
        }
        return JsonResponse(data)

    def post(self, request, pk):
        """ اطلاعات ویرایش شده کاربر را ذخیره می‌کند """
        user = get_object_or_404(User.objects.select_related('profile'), pk=pk)
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = ProfileEditForm(request.POST, instance=user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    user_form.save()
                    profile_form.save()
                messages.success(request, f'اطلاعات کاربر "{user.full_name}" با موفقیت بروزرسانی شد.')
            except Exception as e:
                messages.error(request, f'خطا در ذخیره اطلاعات: {e}')
        else:
            all_errors = {**user_form.errors, **profile_form.errors}
            messages.error(request, f'اطلاعات وارد شده معتبر نیست. خطاها: {all_errors}')

        return redirect('dashboard:users:admin_user_detail', pk=pk)
    
# =================================================== #
# ================ USER DELETE VIEW ================ #
# =================================================== #
class UserDeleteView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ویو برای حذف کاربر"""

    def post(self, request, pk):
        """کاربر انتخاب شده را حذف می‌کند"""
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return JsonResponse({'success': True}, status=200)
    
# =================================================== #
# ========= PENDING VERIFICATION LIST VIEW ========= #
# =================================================== #
class PendingVerificationListView(LoginRequiredMixin, HasAdminAccessPermission, ListView):
    """
    لیست کاربرانی که در صف انتظار برای احراز هویت هستند.
    """
    model = User
    template_name = 'dashboard/users/verify-user.html'
    context_object_name = 'pending_users'
    paginate_by = 12
    
    def get_queryset(self):
        """
        فقط کاربرانی را برمی‌گرداند که وضعیت پروفایل آن‌ها 'PENDING' است.
        کاربران به ترتیب تاریخ ثبت‌نام (قدیمی‌ترین در ابتدا) مرتب می‌شوند.
        """
        queryset = User.objects.select_related('profile').filter(
            profile__auth_status=AuthStatusChoices.PENDING.value
        ).order_by('date_joined')
        return queryset

# ================================================== #
# ======== USER VERIFICATION DETAIL VIEW ======== #
# ================================================== #
class UserVerificationDetailView(LoginRequiredMixin, HasAdminAccessPermission, DetailView):
    """
    نمایش جزئیات کاربر برای بررسی و مدیریت احراز هویت توسط ادمین.
    این ویو هم اطلاعات را نمایش می‌دهد (GET) و هم عملیات تایید/رد را پردازش می‌کند (POST).
    """
    model = User
    template_name = 'dashboard/users/user-detail.html'
    context_object_name = 'target_user'
    
    def get_context_data(self, **kwargs):
        """ ارسال اطلاعات پروفایل و مدارک به تمپلیت """
        context = super().get_context_data(**kwargs)
        target_user = self.get_object()
        context['profile'] = get_object_or_404(Profile, user=target_user)
        context['documents'] = target_user.profile.documents.all()
        return context

    def post(self, request, *args, **kwargs):
        """ مدیریت درخواست‌های تایید یا رد هویت """
        user = self.get_object()
        
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        profile = user.profile
        action = request.POST.get('action')
        
        if action == 'approve':
            medical_code = request.POST.get('medical_code', '').strip()
            send_auth_checked_email(user)
            profile.auth_status = AuthStatusChoices.APPROVED
            profile.role = 'regular'
            profile.rejection_reason = None
            if medical_code:
                profile.medical_code = medical_code
            profile.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'احراز هویت کاربر {user.full_name} با موفقیت تایید شد.',
                    'redirect_url': request.path_info
                })
                
        elif action == 'reject':
            resend_auth_email(user)
            rejection_reason = request.POST.get('rejection_reason', 'دلیل مشخصی ثبت نشده است.')
            profile.auth_status = AuthStatusChoices.REJECTED
            profile.rejection_reason = rejection_reason
            profile.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'احراز هویت کاربر {user.full_name} رد شد.',
                    'redirect_url': request.path_info
                })

        return redirect(request.path_info)

# ================================================== #
# ============= ADD USER VIEW ============= #
# ================================================== #
class AddUserView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ویو برای افزودن کاربر جدید"""
    
    def get(self, request):
        """نمایش فرم افزودن کاربر"""
        form = AddUserForm()
        return render(request, 'dashboard/users/add_user.html', {'form': form})
    
    def post(self, request):
        """افزودن کاربر جدید"""
        form = AddUserForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # ایجاد کاربر جدید با استفاده از پسورد ارائه شده
                    user = User.objects.create_user(
                        phone_number=form.cleaned_data['phone_number'],
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        password=form.cleaned_data['password'],
                        is_active=True
                    )
                    
                    # به‌روزرسانی پروفایل کاربر
                    profile = user.profile
                    profile.role = form.cleaned_data['role']
                    profile.medical_code = form.cleaned_data['medical_code'] or None
                    profile.auth_status = 'APPROVED'  # به صورت خودکار تایید شده
                    profile.save()
                    
                messages.success(request, f'کاربر {user.full_name} با موفقیت اضافه شد.')
                return redirect('dashboard:users:admin_users_list')
            
            except Exception as e:
                messages.error(request, f'خطا در ایجاد کاربر: {str(e)}')
        else:
            messages.error(request, 'اطلاعات وارد شده معتبر نیست. لطفاً خطاهای زیر را بررسی کنید.')
            
        return render(request, 'dashboard/users/add_user.html', {'form': form})