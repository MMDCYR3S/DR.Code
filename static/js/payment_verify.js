/**
 * Payment Verification Logic
 * Supports both Server-Side Data (SSR) and Client-Side Fetching (CSR)
 */
function paymentVerifyApp(serverData = null) {
    return {
        // وضعیت‌های اصلی
        loading: true,
        success: false,
        errorMessage: '',
        
        // داده‌های نمایش
        refId: '',
        paymentDate: '',
        paymentGateway: '',
        
        // قفل برای جلوگیری از درخواست تکراری
        isVerifying: false,

        async init() {
            console.log('🎬 Payment Verify App Initialized');

            // -----------------------------------------------------------
            // سناریوی ۱: داده‌ها از سمت سرور (Django) تزریق شده‌اند (SSR)
            // -----------------------------------------------------------
            if (serverData && typeof serverData.success !== 'undefined') {
                console.log('⚡ Using Server-Side Data (Fast Render)');
                
                this.loading = false; // لودینگ نداریم چون دیتا آماده است
                this.success = serverData.success;
                this.refId = serverData.refId || '';
                this.errorMessage = serverData.errorMessage || '';
                this.paymentDate = serverData.paymentDate || this.formatDate(new Date());
                this.paymentGateway = 'zarinpal'; // یا از سرور پاس داده شود

                // عملیات پس از موفقیت
                if (this.success) {
                    this.showConfetti();
                    // نکته مهم: حتی اگر سرور تایید کرده، باید لوکال استوریج کاربر آپدیت شود
                    // تا منوها و دسترسی‌های فرانت‌اند باز شوند.
                    await this.syncUserProfile();
                }
                
                // پاکسازی دیتاهای موقت خرید
                this.cleanup();
                return;
            }

            // -----------------------------------------------------------
            // سناریوی ۲: داده‌ای نیست، باید از API استعلام بگیریم (CSR)
            // (مثلاً ریدایرکت پارس‌پال یا رفرش صفحه بدون کانتکست)
            // -----------------------------------------------------------
            console.log('globe Using Client-Side Fetching (Fallback)');
            
            const token = localStorage.getItem('drcode_access_token');

            if (!token) {
                console.warn('⚠️ User not logged in, redirecting...');
                // ذخیره آدرس فعلی برای بازگشت بعد از لاگین
                window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname + window.location.search);
                return;
            }

            // شروع پروسه استعلام سمت کلاینت
            await this.verifyPayment(token);
        },

        // ==========================================
        // متدهای استعلام سمت کلاینت (Legacy/Fallback)
        // ==========================================
        async verifyPayment(token) {
            const urlParams = new URLSearchParams(window.location.search);
            
            const gateway = urlParams.get('gateway');
            const authority = urlParams.get('Authority') || urlParams.get('authority');
            const order_id = urlParams.get('order_id');
            const status = urlParams.get('Status') || urlParams.get('status');

            console.log('🔎 Params:', { gateway, authority, status });

            try {
                this.loading = true;

                // تشخیص درگاه و هدایت به متد مربوطه
                if (authority || gateway === 'zarinpal') {
                    await this.verifyZarinpal(authority, status, token);
                }
                else if (order_id || gateway === 'parspal') {
                    await this.verifyParspal(order_id, status, token);
                }
                else {
                    // اگر هیچ پارامتری نبود اما کاربر دستی وارد شده
                    this.loading = false;
                    this.errorMessage = 'اطلاعات پرداخت معتبر نیست.';
                }

            } catch (error) {
                console.error('❌ Verification Error:', error);
                this.success = false;
                this.errorMessage = error.message || 'خطا در بررسی وضعیت پرداخت';
                this.loading = false;
            } finally {
                this.cleanup();
            }
        },

        async verifyZarinpal(authority, status, token) {
            if (this.isVerifying) return;
            this.isVerifying = true;

            try {
                if (status === 'NOK') throw new Error('پرداخت توسط کاربر لغو شد');

                // فراخوانی متد موجود در api.js
                // مطمئن شو API.verifyZarinpalPayment درست ایمپورت/تعریف شده باشد
                const result = await API.payment.verifyZarinpalPayment(authority, status);

                if (result.success) {
                    this.success = true;
                    this.refId = result.data.ref_id;
                    this.paymentDate = this.formatDate(new Date());
                    
                    this.showConfetti();
                    await this.syncUserProfile();
                } else {
                    throw new Error(result.message || 'خطا در تایید پرداخت');
                }

            } catch (error) {
                console.error('Verify Error:', error);
                this.success = false;
                this.errorMessage = error.message;
            } finally {
                this.loading = false;
                this.isVerifying = false;
            }
        },

        async verifyParspal(order_id, status_code, token) {
            if (this.isVerifying) return;
            this.isVerifying = true;

            try {
                // اگر بک‌اند در کال‌بک استاتوسی غیر از 100 را با موفقیت همراه نکرده باشد
                if (status_code && status_code !== '100' && status_code !== 'SUCCESSFUL') {
                    throw new Error('پرداخت لغو شد یا ناموفق بود.');
                }

                // فراخوانی متد تایید پارس‌پال
                // مطمئن شوید متد verifyParspalPayment در فایل api.js درخواست POST به /payments/parspal/verify/ می‌زند
                const result = await API.payment.verifyParspalPayment(order_id);

                if (result.success) {
                    this.success = true;
                    // استخراج شماره رسید بر اساس خروجی بک‌اند شما
                    this.refId = result.data.receipt_number || result.data.reference_number || order_id;
                    this.paymentDate = this.formatDate(new Date());
                    this.paymentGateway = 'parspal';
                    
                    this.showConfetti();
                    await this.syncUserProfile(); // همگام‌سازی برای آپدیت دسترسی‌ها
                } else {
                    throw new Error(result.message || 'خطا در تایید نهایی پرداخت پارس‌پال');
                }

            } catch (error) {
                console.error('❌ ParsPal Verify Error:', error);
                this.success = false;
                this.errorMessage = error.message || 'خطای نامشخص در تایید پرداخت';
            } finally {
                this.loading = false;
                this.isVerifying = false;
            }
        },

        // ==========================================
        // متدهای کمکی و ابزارها
        // ==========================================

        /**
         * همگام‌سازی پروفایل کاربر در LocalStorage
         * این متد حیاتی است تا بعد از پرداخت موفق، هدر سایت و دسترسی‌ها آپدیت شوند
         */
        async syncUserProfile() {
            try {
                console.log('🔄 Syncing user profile...');
                // فرض بر این است که API.profile.getProfile در api.js تعریف شده
                const profile = await API.profile.getProfile();
                
                // بروزرسانی drcode_user_data
                let currentData = {};
                const stored = localStorage.getItem('drcode_user_data');
                if (stored) currentData = JSON.parse(stored);
                
                const newData = {
                    ...currentData,
                    role: profile.role, // مثلاً premium
                    subscription_status: profile.subscription_status,
                    subscription_end_date: profile.subscription_end_date
                };

                localStorage.setItem('drcode_user_data', JSON.stringify(newData));
                console.log('✅ Local storage updated with new subscription data');
                
            } catch (error) {
                console.error('⚠️ Failed to sync profile:', error);
                // ارور اینجا نباید مانع نمایش پیام موفقیت پرداخت شود
            }
        },

        cleanup() {
            localStorage.removeItem('drcode_pending_order');
            localStorage.removeItem('drcode_payment_gateway');
        },

        copyRefId() {
            if (!this.refId) return;
            navigator.clipboard.writeText(this.refId).then(() => {
                // چک کردن وجود SweetAlert
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'success',
                        title: 'کپی شد!',
                        timer: 2000,
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false
                    });
                } else {
                    // فال‌بک ساده
                    const btn = document.querySelector('button span'); 
                    if(btn) {
                        const originalText = btn.innerText;
                        btn.innerText = 'کپی شد!';
                        setTimeout(() => btn.innerText = originalText, 2000);
                    }
                }
            });
        },

        formatDate(dateInput) {
            if (!dateInput) return '';
            const date = new Date(dateInput);
            return new Intl.DateTimeFormat('fa-IR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(date);
        },

        showConfetti() {
            if (typeof confetti === 'undefined') return;
            
            const duration = 3000;
            const end = Date.now() + duration;
            const colors = ['#0077b6', '#00b4d8', '#90e0ef', '#48cae4'];

            (function frame() {
                confetti({
                    particleCount: 4,
                    angle: 60,
                    spread: 55,
                    origin: { x: 0 },
                    colors: colors
                });
                confetti({
                    particleCount: 4,
                    angle: 120,
                    spread: 55,
                    origin: { x: 1 },
                    colors: colors
                });

                if (Date.now() < end) {
                    requestAnimationFrame(frame);
                }
            }());
        },

        // نویگیشن‌ها
        goToProfile() { window.location.href = '/profile/'; },
        goToPrescriptions() { window.location.href = '/dashboard/prescriptions/'; },
        goToPlans() { window.location.href = '/pricing/'; },
        goToHome() { window.location.href = '/'; }
    };
}