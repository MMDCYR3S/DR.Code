const Auth = {
    
    // ثبت‌نام کاربر
    async register(formData) {
        try {
            // نمایش وضعیت در حال پردازش
            this.showLoading(true);
            
            // ارسال درخواست ثبت‌نام
            const response = await API.register(formData);
            
            if (response.success) {
                
                if (response.data.access_token) {
                    StorageManager.saveTokens({
                        access_token: response.data.access_token,
                        refresh_token: response.data.refresh_token,
                        jti: response.data.jti
                    });
                }
                
                // ذخیره اطلاعات کاربر
                StorageManager.saveUserData({
                    user_id: response.data.user_id,
                    full_name: response.data.full_name,
                    phone_number: response.data.phone_number
                });
                
                StorageManager.saveUserProfile(response.data.profile);
                
                // پیام موفقیت
                this.showMessage('success', response.message);
                
                // بستن مودال و به‌روزرسانی UI
                setTimeout(() => {
                    this.closeAuthModal();
                    this.updateUIForLoggedInUser();
                    if (typeof updateAuthWarningBar === 'function') {
                        updateAuthWarningBar();
                    }
                    window.location.href = '/';
                    window.location.reload();
                }, 1500);
                
                // اگر نیاز به احراز هویت تکمیلی دارد
                if (response.data.next_step === 'authentication') {
                    // فعلاً چیزی نمی‌کنیم (برای بعد)
                }
            }
        } catch (error) {
            this.showMessage('error', error.message);
        } finally {
            this.showLoading(false);
        }
    },

    // ورود کاربر
    async login(formData) {
        try {
            this.showLoading(true);
            
            const response = await API.login(formData);
            
            if (response.success) {
                // ذخیره توکن‌ها
                StorageManager.saveTokens(response.data.tokens);
                
                // ذخیره اطلاعات کاربر
                StorageManager.saveUserData(response.data.user);
                
                
                // ذخیره پروفایل کاربر
                StorageManager.saveUserProfile(response.data.profile);
                
                // پیام موفقیت
                this.showMessage('success', response.message);
                
                // بستن مودال و به‌روزرسانی UI
// بستن مودال و به‌روزرسانی UI
setTimeout(() => {
    this.closeAuthModal();
    this.updateUIForLoggedInUser();

    if (typeof updateAuthWarningBar === 'function') {
        updateAuthWarningBar();
    }

    window.location.href = '/';
    window.location.reload();
}, 1500);
            }
        } catch (error) {
            this.showMessage('error', error.message);
        } finally {
            this.showLoading(false);
        }
    },

// خروج کاربر
async logout() {
    if (confirm('آیا مطمئن هستید که می‌خواهید خارج شوید؟')) {
        try {
            // نمایش لودینگ
            const logoutBtn = event.target.closest('a');
            if (logoutBtn) {
                logoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> در حال خروج...';
                logoutBtn.style.pointerEvents = 'none';
                
            }
            
            // فراخوانی API logout
            await API.logout();
            
            // به‌روزرسانی UI
            this.updateUIForLoggedOutUser();
            
            // نمایش پیام موفقیت
            this.showLogoutMessage();
            
            // ریدایرکت به صفحه اصلی
            setTimeout(() => {
                window.location.href = '/';
                // Reload the page to ensure all state is cleared
                window.location.reload();
            }, 1000);
            
        } catch (error) {
            console.error('Logout error:', error);
            // در صورت ارور هم خروج انجام بشه
            StorageManager.clearAll();
            this.updateUIForLoggedOutUser();
            // ریدایرکت به صفحه اصلی و ریلود صفحه
            window.location.href = '/';
            window.location.reload();
        }
    }
    
},

    // به‌روزرسانی UI برای کاربر لاگین شده
    updateUIForLoggedInUser() {
        const userData = StorageManager.getUserData();
        const profile = StorageManager.getUserProfile();
        
        // تغییر دکمه ثبت‌نام به پروفایل (دسکتاپ)
        const authBtn = document.getElementById('auth-btn');
        if (authBtn) {
            authBtn.innerHTML = `
                <div class="user-menu">
                    <button class="profile-btn" onclick="event.preventDefault(); document.getElementById('user-dropdown').style.display = document.getElementById('user-dropdown').style.display === 'block' ? 'none' : 'block';">
                        <i class="fas fa-user-circle"></i>
                        <span>${userData?.full_name || 'کاربر'}</span>
                        <i class="fas fa-chevron-down"></i>
                    </button>
                    <div class="dropdown-menu" id="user-dropdown" style="display: none;">
                        <a href="/profile">
                            <i class="fas fa-user"></i>
                            پروفایل من
                        </a>
                        <hr>
                        <a href="#" onclick="Auth.logout(); return false;">
                            <i class="fas fa-sign-out-alt"></i>
                            خروج
                        </a>
                    </div>
                </div>
            `;
        }

        // تغییر دکمه موبایل
        const authBtnMobile = document.getElementById('auth-btn-mobile');
        if (authBtnMobile) {
            authBtnMobile.innerHTML = `
                <button class="profile-btn-mobile " onclick="toggleMobileUserMenu()">
                    <i class="fas fa-user-circle"></i>
                    ${userData?.full_name || 'کاربر'}
                </button>
                <div id="mobile-user-menu" class="mobile-dropdown-menu absolute px-8" style="display: none;">
                    <a href="/profile"><i class="fas fa-user"></i> پروفایل</a>
                    <a href="#" onclick="Auth.logout(); return false;">
                        <i class="fas fa-sign-out-alt"></i> خروج
                    </a>
                </div>
            `;
        }
    },

    // به‌روزرسانی UI برای کاربر لاگین نشده
    updateUIForLoggedOutUser() {
        const authBtn = document.getElementById('auth-btn');
        if (authBtn) {
            authBtn.innerHTML = `
                <button class="login-register-btn" onclick="Auth.showAuthModal()">
                    <i class="fas fa-sign-in-alt"></i>
                    ورود / ثبت‌نام
                </button>
            `;
        }

        const authBtnMobile = document.getElementById('auth-btn-mobile');
        if (authBtnMobile) {
            authBtnMobile.innerHTML = `
                <button class="login-register-btn bg-c1 px-4 py-2 rounded-lg text-white" onclick="Auth.showAuthModal()">
                    <i class="fas fa-sign-in-alt"></i>
                    ورود / ثبت‌نام
                </button>
            `;
        }
    },

    // نمایش/مخفی کردن مودال احراز هویت
    showAuthModal() {
        document.getElementById('auth-modal').style.display = 'flex';
        // بستن منوی موبایل اگر باز است
        const mobileNav = document.getElementById('mobile-nav');
        if (mobileNav && mobileNav.classList.contains('show')) {
            mobileNav.classList.remove('show');
        }
    },

    closeAuthModal() {
        document.getElementById('auth-modal').style.display = 'none';
        // پاک کردن پیام‌ها
        const messageBox = document.getElementById('auth-message');
        if (messageBox) {
            messageBox.style.display = 'none';
        }
    },

    // نمایش پیام‌ها
    showMessage(type, message) {
        const messageBox = document.getElementById('auth-message');
        if (messageBox) {
            messageBox.className = `message ${type}`;
            messageBox.textContent = message;
            messageBox.style.display = 'block';
            
            setTimeout(() => {
                messageBox.style.display = 'none';
            }, 5000);
        }
    },

    // نمایش وضعیت در حال پردازش
    showLoading(show) {
        const buttons = document.querySelectorAll('#auth-modal button[type="submit"]');
        buttons.forEach(btn => {
            btn.disabled = show;
            if (show) {
                btn.setAttribute('data-original-text', btn.innerHTML);
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> لطفاً صبر کنید...';
            } else {
                btn.innerHTML = btn.getAttribute('data-original-text') || 'ارسال';
            }
        });
    },
// نمایش پیام خروج موفق
showLogoutMessage() {
    // ایجاد المان پیام
    const messageDiv = document.createElement('div');
    messageDiv.className = 'logout-message';
    messageDiv.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>با موفقیت خارج شدید</span>
    `;
    
    // اضافه کردن به body
    document.body.appendChild(messageDiv);
    
    // حذف بعد از 3 ثانیه
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}
,
    // اولیه‌سازی
    init() {
        // بررسی وضعیت لاگین در بارگذاری صفحه
        if (StorageManager.isLoggedIn()) {
            this.updateUIForLoggedInUser();
        } else {
            this.updateUIForLoggedOutUser();
        }

        if (typeof updateAuthWarningBar === 'function') {
            updateAuthWarningBar();
        }

        // event listener برای کلیک خارج از منو
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.user-menu') && !e.target.closest('.profile-btn')) {
                const dropdown = document.getElementById('user-dropdown');
                if (dropdown) dropdown.style.display = 'none';
            }
            
            if (!e.target.closest('#mobile-user-menu') && !e.target.closest('.profile-btn-mobile')) {
                const mobileMenu = document.getElementById('mobile-user-menu');
                if (mobileMenu) mobileMenu.style.display = 'none';
            }
        });

        // بستن modal با ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && document.getElementById('auth-modal').style.display === 'flex') {
                this.closeAuthModal();
            }
        });
    }
    
};

// اولیه‌سازی در بارگذاری صفحه
document.addEventListener('DOMContentLoaded', () => {
    Auth.init();
});

