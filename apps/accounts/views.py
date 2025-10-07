from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

# ========== REGISTER VIEW ========== #
class RegisterView(TemplateView):
    """
    صفحه ثبت‌نام کاربر جدید
    """
    template_name = 'accounts/register.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ثبت‌نام در دکتر کد'
        context['page_description'] = 'ثبت‌نام و عضویت در سامانه نسخه‌نویسی دکتر کد'
        return context

# ========== LOGIN VIEW ========== #
class LoginView(TemplateView):
    """
    صفحه ورود کاربر
    """
    template_name = 'accounts/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ورود به دکتر کد'
        context['page_description'] = 'ورود به حساب کاربری'
        return context

# ========== AUTHENTICATION VIEW ========== #
class AuthenticationView(TemplateView):
    """
    صفحه احراز هویت دو مرحله‌ای
    """
    template_name = 'accounts/authentication.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'احراز هویت'
        context['page_description'] = 'تایید هویت پزشکی برای دسترسی کامل'
        return context

# ========== PROFILE VIEW ========== #
class ProfileView(LoginRequiredMixin, TemplateView):
    """
    صفحه پروفایل کاربر - نیاز به احراز هویت
    """
    template_name = 'profile/profile.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
    
# ========== PROFILE MESSAGES VIEW ========== #
class ProfileMessagesView(LoginRequiredMixin, TemplateView):
    """
    صفحه پروفایل کاربر - نیاز به احراز هویت
    """
    template_name = 'profile/profile-messages.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
    
# ========== PROFILE SAVED PRESCRIPTIONS VIEW ========== #
class ProfileSavedPrescriptionsView(LoginRequiredMixin, TemplateView):
    """
    صفحه پروفایل کاربر - نیاز به احراز هویت
    """
    template_name = 'profile/saved-prescriptions.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
    
# ========== PROFILE NOTIFICATIONS ========== #
class ProfileNotificationsView(LoginRequiredMixin, TemplateView):
    """
    صفحه پروفایل کاربر - نیاز به احراز هویت
    """
    template_name = 'profile/notifications.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

# ========== CHECK AUTH STATUS VIEW ========== #
class CheckAuthStatusView(LoginRequiredMixin, TemplateView):
    """
    صفحه بررسی وضعیت احراز هویت - نیاز به احراز هویت
    """
    template_name = 'accounts/check_auth_status.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'وضعیت احراز هویت'
        context['page_description'] = 'بررسی وضعیت تایید هویت پزشکی'
        context['user'] = self.request.user
        return context
