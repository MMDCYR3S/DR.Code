import logging
import jdatetime
from django.utils import timezone
from django.views.generic import ListView, View, DetailView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.contrib import messages
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

# ===== Local Imports ===== #
from apps.accounts.permissions import IsTokenJtiActive, HasAdminAccessPermission
from apps.accounts.models import Profile, AuthStatusChoices
from ..forms import UserSearchForm, UserEditForm, ProfileEditForm, AddUserForm
from ..services.email_service import resend_auth_email, send_auth_checked_email
from apps.accounts.services import AmootSMSService

User = get_user_model()

# تنظیم لاگر اختصاصی که در settings تعریف کردیم
logger = logging.getLogger('user_verification')

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
                role="visitor",
                auth_status=AuthStatusChoices.PENDING.value,
                documents__isnull=False
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
    """ ویو برای دریافت اطلاعات و ویرایش کاربر """
    
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
        """
        queryset = User.objects.select_related('profile').filter(
            profile__auth_status=AuthStatusChoices.PENDING.value,
            profile__documents__isnull=False
        ).order_by('date_joined')
        return queryset

# ================================================== #
# ======== USER VERIFICATION DETAIL VIEW ======== #
# ================================================== #
class UserVerificationDetailView(LoginRequiredMixin, DetailView): # HasAdminAccessPermission را اضافه کنید
    """
    نمایش جزئیات کاربر برای بررسی و مدیریت احراز هویت توسط ادمین.
    """
    model = User
    template_name = 'dashboard/users/user-detail.html'
    context_object_name = 'target_user'
    
    def get_context_data(self, **kwargs):
        """ ارسال اطلاعات پروفایل و مدارک به تمپلیت """
        context = super().get_context_data(**kwargs)
        target_user = self.get_object()
        context['profile'] = get_object_or_404(Profile, user=target_user)
        try:
            context['documents'] = target_user.profile.documents.all()
        except:
            context['documents'] = []
        return context

    def post(self, request, *args, **kwargs):
        """ مدیریت درخواست‌های تایید یا رد هویت """
        user = self.get_object()
        admin_user = request.user
        
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        profile = user.profile
        action = request.POST.get('action')
        
        # ثبت لاگ شروع عملیات
        logger.info(f"Verification Action Started | Admin: {admin_user.email} | Target: {user.phone_number} | Action: {action}")
        
        if action == 'approve':
            
            
            # ===== Approve Logic ===== #
            medical_code = request.POST.get('medical_code', '').strip()
            
            try:
                send_auth_checked_email(user)
                logger.info(f"Auth Email Sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send Auth Email to {user.email}: {e}")
            
            profile.auth_status = AuthStatusChoices.APPROVED
            profile.role = 'regular'
            profile.rejection_reason = None
            if medical_code:
                profile.medical_code = medical_code
            profile.save()
            
            logger.info(f"User {user.phone_number} APPROVED by Admin {admin_user.email}")
            
            success = False
            
            # ===== SMS Notification (UPDATED TO PATTERN) ===== #
            try:
                sms_service = AmootSMSService()
                
                # نام کاربر (اگر خالی بود یک مقدار پیش‌فرض)
                user_name = user.full_name if user.full_name else "همکار گرامی"
                
                # ارسال با پترن 4312
                success = sms_service.send_with_pattern(
                    mobile=str(user.phone_number),
                    pattern_code=4312,
                    values=[user_name]
                )
                
                if success:
                    logger.info(f"Approval SMS (Pattern 4312) sent successfully to {user.phone_number}.")
                else:
                    logger.warning(f"Approval SMS (Pattern 4312) Failed for {user.phone_number}. Check previous logs for details.")
                    
            except Exception as e:
                logger.error(f"Error sending approval SMS to {user.phone_number}: {e}", exc_info=True)

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'احراز هویت کاربر {user.full_name} با موفقیت تایید شد.',
                    'redirect_url': request.path_info
                })
                
        elif action == 'reject':
            # ===== Reject Logic ===== #
            rejection_reason = request.POST.get('rejection_reason', 'دلیل مشخصی ثبت نشده است.')
            profile.auth_status = AuthStatusChoices.REJECTED
            profile.rejection_reason = rejection_reason
            
            try:
                resend_auth_email(user)
                logger.info(f"Rejection Email Sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send Rejection Email to {user.email}: {e}")
                
            profile.save()
            
            logger.info(f"User {user.phone_number} REJECTED by Admin {admin_user.email}. Reason: {rejection_reason}")
            
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
        form = AddUserForm()
        return render(request, 'dashboard/users/add_user.html', {'form': form})
    
    def post(self, request):
        form = AddUserForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # ایجاد کاربر جدید
                    user = User.objects.create_user(
                        phone_number=form.cleaned_data['phone_number'],
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        password=form.cleaned_data['password'],
                        is_active=True
                    )
                    
                    # به‌روزرسانی پروفایل
                    profile = user.profile
                    profile.role = form.cleaned_data['role']
                    profile.medical_code = form.cleaned_data['medical_code'] or "DR-CODE"
                    profile.auth_status = 'APPROVED'
                    profile.save()
                    
                    # ایجاد اشتراک برای کاربران ویژه
                    if form.cleaned_data['role'] == 'premium':
                        subscription_plan_id = request.POST.get('subscription_plan')
                        if subscription_plan_id:
                            try:
                                from apps.subscriptions.models import Plan, Subscription, SubscriptionStatusChoicesModel
                                from datetime import timedelta
                                
                                plan = Plan.objects.get(id=subscription_plan_id)
                                end_date = timezone.now() + timedelta(days=plan.duration_days)
                                
                                Subscription.objects.create(
                                    user=user,
                                    plan=plan,
                                    payment_amount=plan.price,
                                    status=SubscriptionStatusChoicesModel.active.value,
                                    start_date=timezone.now(),
                                    end_date=end_date
                                )
                            except Plan.DoesNotExist:
                                messages.error(request, 'پلن انتخاب شده معتبر نیست.')
                                return render(request, 'dashboard/users/add_user.html', {'form': form})
                    
                messages.success(request, f'کاربر {user.full_name} با موفقیت اضافه شد.')
                return redirect('dashboard:users:admin_users_list')
            
            except Exception as e:
                messages.error(request, f'خطا در ایجاد کاربر: {str(e)}')
        else:
            messages.error(request, 'اطلاعات وارد شده معتبر نیست. لطفاً خطاهای زیر را بررسی کنید.')
            
        return render(request, 'dashboard/users/add_user.html', {'form': form})

# ================================================== #
# ============= EXPORT USERS TO EXCEL ============= #
# ================================================== #
class ExportUsersToExcelView(LoginRequiredMixin, HasAdminAccessPermission, View):
    """ویو برای استخراج اطلاعات کاربران به فرمت Excel"""
    
    def get(self, request):
        role = request.GET.get('role', None)
        
        users = User.objects.select_related('profile').all()
        
        if role:
            users = users.filter(profile__role=role)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "کاربران"
        
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        columns = [
            'نام', 'نام خانوادگی', 'ایمیل', 'شماره تماس',
            'کد نظام پزشکی', 'لینک نظام پزشکی', 'وضعیت احراز هویت',
            'نقش', 'کد معرف', 'دلیل رد هویت', 'تاریخ عضویت'
        ]
        
        for col_num, column_title in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_num, value=column_title)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        for row_num, user in enumerate(users, 2):
            jalali_date = ""
            if user.date_joined:
                jalali_date_obj = jdatetime.datetime.fromgregorian(datetime=user.date_joined)
                jalali_date = jalali_date_obj.strftime('%Y/%m/%d - %H:%M')
            
            row_data = [
                user.first_name,
                user.last_name,
                user.email,
                user.phone_number,
                getattr(user.profile, 'medical_code', '') or '',
                getattr(user.profile, 'auth_link', '') or '',
                getattr(user.profile, 'get_auth_status_display', lambda: '')(),
                getattr(user.profile, 'get_role_display', lambda: '')(),
                getattr(user.profile, 'referral_code', '') or '',
                getattr(user.profile, 'rejection_reason', '') or '',
                jalali_date
            ]
            
            for col_num, cell_value in enumerate(row_data, 1):
                ws.cell(row=row_num, column=col_num, value=str(cell_value))
        
        column_widths = [15, 20, 25, 15, 20, 25, 15, 15, 15, 25, 20]
        for i, column_width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + i)].width = column_width
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        if role:
            filename = f"users_{role}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        else:
            filename = f"all_users_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        
        return response