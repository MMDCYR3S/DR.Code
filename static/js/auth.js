const Auth = {
    
    // ============================================================
    // ============ HELPERS: مدیریت خطای فیلدی ====================
    // ============================================================

    // پاک کردن تمام خطاهای یک فرم
    clearFieldErrors(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        form.querySelectorAll('.field-error').forEach(el => {
            el.textContent = '';
            el.classList.remove('show');
        });

        form.querySelectorAll('input, select, textarea').forEach(el => {
            el.classList.remove('input-error');
        });
    },

    // نمایش خطا زیر یک input خاص
    showFieldError(inputId, message) {
        const input = document.getElementById(inputId);
        if (input) input.classList.add('input-error');

        const errorEl = document.querySelector(`.field-error[data-error-for="${inputId}"]`);
        if (errorEl) {
            // اگر خطا آرایه بود، اولین پیام رو بگیر
            if (Array.isArray(message)) message = message[0];
            errorEl.textContent = message;
            errorEl.classList.add('show');
        }
    },

    // نگاشت کلید خطای API به id input در HTML
    getFieldMap(formType) {
        if (formType === 'login') {
            return {
                phone_number: 'login-phone',
                password: 'login-password',
            };
        }
        // register
        return {
            first_name: 'register-firstname',
            last_name: 'register-lastname',
            phone_number: 'register-phone',
            email: 'register-email',
            password: 'register-password',
            password_confirm: 'register-password-confirm',
        };
    },

    // مدیریت یکپارچه خطاهای بک‌اند
    handleAuthErrors(formType, errors = {}, fallbackMessage = null) {
        const formId = formType === 'login' ? 'login-form' : 'register-form';
        const map = this.getFieldMap(formType);

        let generalMessage = null;

        Object.keys(errors).forEach(key => {
            const value = errors[key];
            const msg = Array.isArray(value) ? value[0] : value;

            if (key === 'non_field_errors' || key === 'detail' || key === 'message') {
                generalMessage = generalMessage || msg;
            } else if (map[key]) {
                this.showFieldError(map[key], msg);
            } else {
                // فیلد ناشناخته - به عنوان خطای کلی نمایش بده
                generalMessage = generalMessage || msg;
            }
        });

        // پیام کلی بالای پنل
        const finalMessage = generalMessage
            || fallbackMessage
            || (formType === 'login' ? 'خطا در ورود به حساب کاربری' : 'خطا در ثبت‌نام');

        this.showMessage('error', finalMessage);

        // انیمیشن shake
        const modalBox = document.querySelector('#auth-modal > div');
        if (modalBox) {
            modalBox.classList.add('animate-shake');
            setTimeout(() => modalBox.classList.remove('animate-shake'), 450);
        }
    },
    
    // ============================================================
    // ==================== REGISTER ==============================
    // ============================================================
    async register(formData) {
        const formId = 'register-form';
        try {
            // پاک‌سازی خطاهای قبلی + پیام کلی
            this.clearFieldErrors(formId);
            this.showMessage('clear');
            this.showLoading(true);

            const response = await API.register(formData);

            if (response.success) {
                if (response.data.access_token) {
                    StorageManager.saveTokens({
                        access_token: response.data.access_token,
                        refresh_token: response.data.refresh_token,
                        jti: response.data.jti
                    });
                }

                StorageManager.saveUserData({
                    user_id: response.data.user_id,
                    full_name: response.data.full_name,
                    phone_number: response.data.phone_number
                });

                StorageManager.saveUserProfile(response.data.profile);

                this.showMessage('success', response.message);

                setTimeout(() => {
                    this.closeAuthModal();
                    this.updateUIForLoggedInUser();
                    if (typeof updateAuthWarningBar === 'function') {
                        updateAuthWarningBar();
                    }
                    window.dispatchEvent(new CustomEvent('user-logged-in'));
                    window.location.href = '/';
                    window.location.reload(true);
                }, 1500);

            } else {
                // مسیر خطا (اگر API به‌جای throw، success:false برگردونه)
                this.handleAuthErrors('register', response.errors || {}, response.message);
            }

        } catch (error) {
            console.error('Register error:', error);
            this.handleAuthErrors('register', error.errors || {}, error.message);
        } finally {
            this.showLoading(false);
        }
    },

    // ============================================================
    // ====================== LOGIN ===============================
    // ============================================================
    async login(formData) {
        const formId = 'login-form';
        try {
            this.clearFieldErrors(formId);
            this.showMessage('clear');
            this.showLoading(true);

            const response = await API.login(formData);

            if (response.success) {
                StorageManager.saveTokens(response.data.tokens);
                StorageManager.saveUserData(response.data.user);
                StorageManager.saveUserProfile(response.data.profile);

                this.showMessage('success', response.message);

                setTimeout(() => {
                    this.closeAuthModal();
                    this.updateUIForLoggedInUser();

                    if (typeof updateAuthWarningBar === 'function') {
                        updateAuthWarningBar();
                    }

                    window.dispatchEvent(new CustomEvent('user-logged-in'));
                    window.location.reload(true);
                }, 1500);
            } else {
                this.handleAuthErrors('login', response.errors || {}, response.message);
            }

        } catch (error) {
            console.error('Login error:', error);
            // error.errors از API.login میاد (بعد از اصلاح قدم ۱)
            this.handleAuthErrors('login', error.errors || {}, error.message);
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
                <button class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-gray-900 to-gray-800 hover:from-c1 hover:to-c1 shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:shadow-[0_4px_20px_rgba(var(--c1-rgb,0,102,204),0.3)] transition-all duration-300 transform hover:-translate-y-0.5 active:translate-y-0" onclick="Auth.showAuthModal()">
                    <i class="fas fa-sign-in-alt text-xs opacity-90"></i>
                    <span>ورود / ثبت‌نام</span>
                </button>
            `;
        }

        const authBtnMobile = document.getElementById('auth-btn-mobile');
        if (authBtnMobile) {
            authBtnMobile.innerHTML = `
                <button class="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-gray-900 to-gray-800 hover:from-c1 hover:to-c1 shadow-[0_4px_12px_rgba(0,0,0,0.1)] hover:shadow-[0_4px_20px_rgba(var(--c1-rgb,0,102,204),0.3)] transition-all duration-300 transform hover:-translate-y-0.5 active:translate-y-0" onclick="Auth.showAuthModal()">
                    <i class="fas fa-sign-in-alt text-xs opacity-90"></i>
                    <span>ورود / ثبت‌نام</span>
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

    // ============================================================
    // ============ بستن مودال - پاک کردن خطاها ====================
    // ============================================================
    closeAuthModal() {
        document.getElementById('auth-modal').style.display = 'none';

        // پاک کردن پیام کلی + خطاهای فیلدی هر دو فرم
        this.showMessage('clear');
        this.clearFieldErrors('login-form');
        this.clearFieldErrors('register-form');
    },

    // ============================================================
    // =================== showMessage (جدید) =====================
    // ============================================================
    showMessage(type, message) {
        const messageBox = document.getElementById('auth-message');
        if (!messageBox) return;

        // حالت پاک کردن
        if (type === 'clear' || type === null) {
            messageBox.style.display = 'none';
            messageBox.innerHTML = '';
            return;
        }

        const styles = {
            error:   'bg-red-50 border-red-200 text-red-700',
            success: 'bg-emerald-50 border-emerald-200 text-emerald-700',
            warning: 'bg-amber-50 border-amber-200 text-amber-700',
            info:    'bg-blue-50 border-blue-200 text-blue-700',
        };
        const icons = {
            error:   'fa-exclamation-circle',
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            info:    'fa-info-circle',
        };

        messageBox.className =
            `p-4 rounded-2xl text-xs font-bold mb-6 border flex items-center justify-center gap-2 ` +
            `${styles[type] || styles.info}`;

        messageBox.innerHTML =
            `<i class="fas ${icons[type] || icons.info}"></i><span>${message}</span>`;

        messageBox.style.display = 'flex';
    },

    // ============================================================
    // ======== سایر متدها (بدون تغییر — فقط برای مرجع) ==========
    // ============================================================
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
    },
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

