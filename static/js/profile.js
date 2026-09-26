// مدیریت صفحه پروفایل
console.log('👤 Profile.js loading...');

const profileApp = {
    profileData: null,
    profileUpdateData: null,
    unreadNotificationsCount: 0,
    loading: true,
    error: null,
    editMode: false,

    // --- متغیرهای جدید برای تایید تلفن ---
    showPhoneVerifyModal: false,
    phoneVerifyCode: '',
    phoneVerifyLoading: false,
    phoneVerifyTimer: 0,
    timerInterval: null,

    async init() {
        console.log('🟢 Profile app initializing...');
        
        // چک کن لاگین هست یا نه
        if (!StorageManager.isLoggedIn()) {
            console.log('❌ Not logged in, redirecting to home');
            window.location.href = '/';
            return;
        }

        console.log('✅ User is logged in, loading profile data...');
        await this.loadProfileData();
        await Promise.all([
            this.loadProfileData(),
            this.fetchUnreadNotifications() // ✨ فراخوانی تابع جدید
        ]);

// ✨ چک کردن هش URL برای باز کردن خودکار مودال (برای وقتی از نوار بالا کلیک میشه)
        if (window.location.hash === '#verify-phone' && this.profileData && !this.profileData.is_phone_verified) {
            this.openPhoneVerifyModal();
            // حذف هش از URL تمیزتره
            history.replaceState(null, null, ' ');
        }

    },

// --- توابع جدید ---

    async openPhoneVerifyModal() {
        this.showPhoneVerifyModal = true;
        this.phoneVerifyCode = '';
        // بلافاصله کد رو بفرست
        await this.requestPhoneCode();
    },

    async requestPhoneCode() {
        try {
            this.phoneVerifyLoading = true;
            
            // درخواست GET برای دریافت/ارسال کد
            // طبق مستندات: GET /api/v1/accounts/profile/verify-phone/
            // این باید SMS رو تریگر کنه
            const response = await fetch('/api/v1/accounts/profile/verify-phone/', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('drcode_access_token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // شروع تایمر (مثلاً ۱۲۰ ثانیه)
                this.startTimer(120);
                
                Swal.fire({
                    icon: 'info',
                    title: 'کد ارسال شد',
                    text: 'کد تایید به شماره شما پیامک شد.',
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 3000
                });
            } else {
                throw new Error('خطا در ارسال پیامک');
            }

        } catch (error) {
            console.error(error);
            Swal.fire({
                icon: 'error',
                title: 'خطا',
                text: 'مشکلی در ارسال کد پیش آمد. لطفا دوباره تلاش کنید.'
            });
        } finally {
            this.phoneVerifyLoading = false;
        }
    },

    async submitPhoneVerify() {
        try {
            this.phoneVerifyLoading = true;

            // درخواست POST برای تایید کد
            const response = await fetch('/api/v1/accounts/profile/verify-phone/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('drcode_access_token')}`,
                    'Content-Type': 'application/json',
                    // اضافه کردن CSRF Token اگه جنگو نیاز داره (معمولاً تو هدر یا کوکی هست)
                    'X-CSRFToken': this.getCookie('csrftoken') 
                },
                body: JSON.stringify({ code: this.phoneVerifyCode })
            });

            if (response.ok) {
                // موفقیت
                this.showPhoneVerifyModal = false;
                await this.loadProfileData(); // ریلود کردن اطلاعات برای سبز شدن تیک
                
                Swal.fire({
                    icon: 'success',
                    title: 'تایید شد!',
                    text: 'شماره تلفن شما با موفقیت تایید شد.',
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#10b981'
                });
            } else {
                const data = await response.json();
                throw new Error(data.detail || 'کد وارد شده اشتباه است');
            }

        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'خطا',
                text: error.message
            });
        } finally {
            this.phoneVerifyLoading = false;
        }
    },

    startTimer(seconds) {
        this.phoneVerifyTimer = seconds;
        if (this.timerInterval) clearInterval(this.timerInterval);
        
        this.timerInterval = setInterval(() => {
            if (this.phoneVerifyTimer > 0) {
                this.phoneVerifyTimer--;
            } else {
                clearInterval(this.timerInterval);
            }
        }, 1000);
    },

    formatTimer(seconds) {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    },

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },



    async fetchUnreadNotifications() {
        try {
            // فرض بر این است که API دریافت لیست نوتیفیکیشن‌ها، تعداد خوانده نشده را هم برمی‌گرداند
            // مشابه کاری که در notificationWidget انجام دادید
            const response = await API.notifications.getNotifications();
            if (response.success && response.data) {
                this.unreadNotificationsCount = response.data.unread_count || 0;
            }
        } catch (error) {
            console.error('Error fetching notification count:', error);
        }
    },

    
    async loadProfileData() {
        try {
            this.loading = true;
            this.error = null;

            console.log('📡 Fetching profile data...');

            // دریافت اطلاعات پروفایل
            const profileResponse = await API.profile.getProfile();
            console.log('📦 Profile response:', profileResponse);

            if (profileResponse.success) {
                this.profileData = profileResponse.data;
            } else {
                throw new Error(profileResponse.message || 'خطا در دریافت اطلاعات');
            }


            // دریافت اطلاعات ویرایش
            const updateResponse = await API.profile.getProfileUpdate();
            console.log('📦 Update response:', updateResponse);

            if (updateResponse.success) {
                this.profileUpdateData = updateResponse.data;
                this.resetPasswordEmail = updateResponse.data.user.email;
            }

            console.log('✅ Profile loaded successfully');

        } catch (error) {
            console.error('❌ Profile load error:', error);
            this.error = error.message;

            // اگه خطای authentication بود
            if (error.message.includes('401') || error.message.includes('نشست')) {
                console.log('🔴 Session expired, logging out...');
                StorageManager.clearAll();
                window.location.href = '/';
                return;
            }

            // نمایش خطا
            Swal.fire({
                icon: 'error',
                title: 'خطا',
                text: error.message,
                confirmButtonText: 'باشه'
            });
        } finally {
            this.loading = false;
        }
    },
    
    goToVerification() {
        // آدرس صفحه احراز هویت را اینجا قرار دهید
        window.location.href = '/authentication/'; 
    },

    enableEditMode() {
        this.editMode = true;
    },

    cancelEdit() {
        this.editMode = false;
    },

    async saveProfile() {
        try {
            const formData = {
                first_name: document.getElementById('edit-first-name').value,
                last_name: document.getElementById('edit-last-name').value,
                email: document.getElementById('edit-email').value,
                phone_number: document.getElementById('phone__number').value
            };

            const response = await API.profile.updateProfile(formData);

            if (response.success) {
                await this.loadProfileData();
                this.editMode = false;

                Swal.fire({
                    icon: 'success',
                    title: 'موفق',
                    text: 'اطلاعات ذخیره شد'
                });
            }

        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'خطا',
                text: error.message
            });
        }
    }
};

// فقط اگه توی صفحه profile هستیم، init کن
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM loaded');
    
    // چک کن که آیا این صفحه profile هست
    if (window.location.pathname.includes('/profile')) {
        console.log('✅ This is profile page, initializing...');
        
        window.profileApp = profileApp;
        
        // یکم صبر کن تا همه چیز لود بشه
        setTimeout(() => {
            profileApp.init();
        }, 200);
    } else {
        console.log('ℹ️ Not profile page, skipping profile init');
    }
});

console.log('✅ Profile.js loaded');

// ========================================
// Password Reset Confirm App
// ========================================
document.addEventListener('alpine:init', () => {
    Alpine.data('passwordResetApp', () => ({
        formData: {
            password: '',
            password_confirm: '',
            uidb64: '',
            token: ''
        },
        loading: false,
        passwordVisible: {
            new: false,
            confirm: false
        },

        init() {
            console.log('🔄 Initializing password reset confirm...');
            
            // استخراج uidb64 و token از URL
            const pathParts = window.location.pathname.split('/').filter(part => part);
            // URL format: /password/reset/confirm/MQ/cy6dq3-xxx/
            
            if (pathParts.length >= 5) {
                this.formData.uidb64 = pathParts[3]; // MQ
                this.formData.token = pathParts[4];  // cy6dq3-xxx
                
                console.log('✅ Password reset params extracted:', {
                    uidb64: this.formData.uidb64,
                    token: this.formData.token
                });
            } else {
                console.error('❌ Invalid password reset URL format');
                this.showInvalidLinkError();
            }
        },

        togglePasswordVisibility(field) {
            this.passwordVisible[field] = !this.passwordVisible[field];
        },

        validatePassword() {
            // بررسی تطابق رمزها
            if (this.formData.password !== this.formData.password_confirm) {
                throw new Error('رمز عبور و تکرار آن باید یکسان باشند');
            }

            // بررسی طول رمز عبور
            if (this.formData.password.length < 8) {
                throw new Error('رمز عبور باید حداقل 8 کاراکتر باشد');
            }

            // بررسی وجود uidb64 و token
            if (!this.formData.uidb64 || !this.formData.token) {
                throw new Error('لینک بازیابی نامعتبر است');
            }
        },

        async handleSubmit() {
            try {
                // اعتبارسنجی
                this.validatePassword();

                // نمایش تایید
                const result = await Swal.fire({
                    icon: 'question',
                    title: 'تایید تغییر رمز عبور',
                    text: 'آیا از تغییر رمز عبور خود اطمینان دارید؟',
                    showCancelButton: true,
                    confirmButtonText: 'بله، تغییر کن',
                    cancelButtonText: 'انصراف',
                    confirmButtonColor: '#10b981',
                    cancelButtonColor: '#6b7280'
                });

                if (!result.isConfirmed) {
                    return;
                }

                this.loading = true;
                console.log('🔄 Submitting password reset confirm...');

                // ارسال درخواست به API
                const response = await API.profile.confirmPasswordReset(this.formData);
                
                console.log('✅ Password reset successful:', response);

                // نمایش پیام موفقیت و هدایت
                await Swal.fire({
                    icon: 'success',
                    title: 'موفقیت!',
                    html: 'رمز عبور شما با موفقیت تغییر کرد.<br/><br/>اکنون می‌توانید با رمز عبور جدید وارد شوید.',
                    confirmButtonText: 'ورود به حساب',
                    confirmButtonColor: '#10b981',
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });

                // هدایت به صفحه اصلی
                window.location.href = '/';

            } catch (error) {
                console.error('❌ Password reset confirm error:', error);
                
                let errorMessage = 'خطا در تغییر رمز عبور. لطفاً دوباره تلاش کنید.';
                
                // پردازش خطاهای مختلف
                if (error.message) {
                    errorMessage = error.message;
                } else if (error.detail) {
                    errorMessage = error.detail;
                } else if (error.password) {
                    errorMessage = Array.isArray(error.password) 
                        ? error.password[0] 
                        : error.password;
                } else if (error.password_confirm) {
                    errorMessage = Array.isArray(error.password_confirm)
                        ? error.password_confirm[0]
                        : error.password_confirm;
                } else if (error.token) {
                    errorMessage = 'لینک بازیابی نامعتبر یا منقضی شده است';
                } else if (error.uidb64) {
                    errorMessage = 'لینک بازیابی نامعتبر است';
                }

                await Swal.fire({
                    icon: 'error',
                    title: 'خطا',
                    text: errorMessage,
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#ef4444'
                });

            } finally {
                this.loading = false;
            }
        },

        async showInvalidLinkError() {
            await Swal.fire({
                icon: 'error',
                title: 'لینک نامعتبر',
                html: 'لینک بازیابی نامعتبر یا منقضی شده است.<br/><br/>لطفاً دوباره درخواست بازیابی رمز عبور دهید.',
                confirmButtonText: 'بازگشت به صفحه اصلی',
                confirmButtonColor: '#ef4444',
                allowOutsideClick: false,
                allowEscapeKey: false
            });
            
            window.location.href = '/';
        }
    }));
});

