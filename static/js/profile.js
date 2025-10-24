// مدیریت صفحه پروفایل
console.log('👤 Profile.js loading...');

const profileApp = {
    profileData: null,
    profileUpdateData: null,
    loading: true,
    error: null,
    editMode: false,
    showPasswordResetModal: false,
    resetPasswordEmail: '',
    passwordResetLoading: false,
    

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
    },

    async requestPasswordReset() {
        try {
            const email = this.resetPasswordEmail || this.profileUpdateData?.user?.email;
            
            if (!email) {
                throw new Error('ایمیل یافت نشد');
            }

            // نمایش تایید
            const result = await Swal.fire({
                icon: 'question',
                title: 'تغییر رمز عبور',
                html: `لینک بازیابی رمز عبور به ایمیل<br/><strong>${email}</strong><br/>ارسال خواهد شد`,
                showCancelButton: true,
                confirmButtonText: 'ارسال لینک',
                cancelButtonText: 'انصراف',
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33'
            });

            if (!result.isConfirmed) {
                return;
            }

            this.passwordResetLoading = true;

            // استفاده از API.profile.requestPasswordReset
            const data = await API.profile.requestPasswordReset(email);

            // بستن مودال
            this.showPasswordResetModal = false;
            
            // نمایش پیام موفقیت
            await Swal.fire({
                icon: 'success',
                title: 'ارسال شد!',
                html: `لینک بازیابی رمز عبور به ایمیل <strong>${email}</strong> ارسال شد.<br/><br/>لطفاً ایمیل خود را بررسی کنید.`,
                confirmButtonText: 'متوجه شدم',
                confirmButtonColor: '#3085d6'
            });

        } catch (error) {
            console.error('❌ Password reset error:', error);
            Swal.fire({
                icon: 'error',
                title: 'خطا',
                text: error.email?.[0] || error.detail || error.message || 'خطا در ارسال لینک بازیابی',
                confirmButtonText: 'باشه'
            });
        } finally {
            this.passwordResetLoading = false;
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

