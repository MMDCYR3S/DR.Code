function paymentVerifyApp() {
    return {
        loading: true,
        success: false,
        errorMessage: '',
        refId: '',
        paymentDate: '',
        paymentGateway: '',
        
        async init() {
            console.log('🎬 Payment Verify initialized');
            
            // ✅ اصلاح شد: دریافت توکن با نام صحیح از عکس شما
            const token = localStorage.getItem('drcode_access_token');

            if (!token) {
                console.warn('⚠️ User not logged in (Token not found), redirecting...');
                // اگر توکن نباشد یعنی کاربر لاگین نیست
                window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                return;
            }

            // توکن رو پاس میدیم به تابع بعدی
            await this.verifyPayment(token);
        },

        async verifyPayment(token) {
            const urlParams = new URLSearchParams(window.location.search);
            
            const gateway = urlParams.get('gateway');
            const authority = urlParams.get('Authority');
            const order_id = urlParams.get('order_id');
            const status = urlParams.get('Status') || urlParams.get('status');

            console.log('🔎 Payment Parameters:', { gateway, authority, order_id, status });

            try {
                this.loading = true;

                if (authority || gateway === 'zarinpal') {
                    await this.verifyZarinpal(authority, status, token);
                }
                else if (order_id || gateway === 'parspal') {
                    await this.verifyParspal(order_id, status, token);
                }
                else {
                    throw new Error('اطلاعات پرداخت نامعتبر است');
                }

            } catch (error) {
                console.error('❌ Payment verification error:', error);
                this.success = false;
                this.errorMessage = error.message || 'خطا در بررسی وضعیت پرداخت';
            } finally {
                this.loading = false;
                this.cleanup();
            }
        },

        // ========== زرین‌پال ========== //
        async verifyZarinpal(authority, status, token) {
            console.log('🟢 Verifying ZarinPal...');

            if (!authority) throw new Error('کد Authority یافت نشد');
            if (status === 'NOK') throw new Error('پرداخت توسط کاربر لغو شد');

            const url = '/api/v1/payment/zarinpal/verify/';

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`, // استفاده از توکن درست
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    authority: authority,
                    status: status
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || data.message || data.detail || 'خطا در تایید پرداخت');
            }

            this.success = true;
            this.paymentGateway = 'zarinpal';
            this.paymentData = data;
            this.refId = data.ref_id || '';
            this.paymentDate = this.formatDate(new Date());

            console.log('✅ ZarinPal verified!');
            this.showConfetti();
            await this.updateUserProfile();
        },

        // ========== پارس‌پال ========== //
        async verifyParspal(order_id, status_code, token) {
            console.log('🟣 Verifying ParsPal...');

            if (!order_id) throw new Error('شناسه سفارش یافت نشد');

            if (status_code !== '100') {
                const messages = { '99': 'انصراف', '88': 'ناموفق', '77': 'لغو کاربر' };
                throw new Error(messages[status_code] || 'پرداخت ناموفق');
            }

            const url = '/api/v1/payment/parspal/verify/';

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`, // استفاده از توکن درست
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ order_id: order_id })
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.message || 'خطا در تایید پرداخت');
            if (!data.success) throw new Error(data.message || 'تایید پرداخت ناموفق بود');

            this.success = true;
            this.paymentGateway = 'parspal';
            this.paymentData = data.data || data;
            
            this.refId = data.data?.reference_number || data.data?.transaction_id || order_id;
            this.paymentDate = this.formatDate(new Date());

            console.log('✅ ParsPal verified!');
            this.showConfetti();
            await this.updateUserProfile();
        },

        async updateUserProfile() {
            try {
                console.log('🔄 Updating user profile...');
                
                // دریافت پروفایل جدید از سرور
                const profile = await API.profile.getProfile();
                
                // ✅ اصلاح شد: خواندن دیتای یوزر از کلید صحیح (drcode_user_data)
                let currentData = {};
                try {
                    const stored = localStorage.getItem('drcode_user_data');
                    if (stored) currentData = JSON.parse(stored);
                } catch (e) { console.error('Error parsing user data', e); }
                
                const newData = {
                    ...currentData,
                    role: profile.role,
                    subscription_status: profile.subscription_status,
                    subscription_end_date: profile.subscription_end_date
                };

                // ✅ اصلاح شد: ذخیره مجدد با کلید صحیح
                localStorage.setItem('drcode_user_data', JSON.stringify(newData));
                
                // آپدیت اختیاری: اگر دیتای پروفایل جداگانه هم دارید
                localStorage.setItem('drcode_user_profile', JSON.stringify(profile));

                console.log('✅ Profile updated in localStorage (drcode_user_data)');
            } catch (error) {
                console.error('⚠️ Error updating profile:', error);
            }
        },

        cleanup() {
            // ✅ اصلاح شد: پاکسازی کلیدهای مربوط به پرداخت با پیشوند صحیح
            localStorage.removeItem('drcode_pending_order');
            // اگر کلید gateway هم پیشوند drcode_ دارد، اینجا اضافه کنید، وگرنه همینطور بماند
            localStorage.removeItem('drcode_payment_gateway'); // حدس زدم اینم باید این شکلی باشه
        },

        copyRefId() {
            if (!this.refId) return;
            navigator.clipboard.writeText(this.refId).then(() => {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({ icon: 'success', title: 'کپی شد!', timer: 2000, toast: true, position: 'top-end', showConfirmButton: false });
                } else { alert('کپی شد'); }
            });
        },

        formatDate(date) {
            if (!date) return '';
            return new Intl.DateTimeFormat('fa-IR', {
                year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
            }).format(new Date(date));
        },

        showConfetti() {
            if (typeof confetti === 'undefined') return;
            const duration = 3000;
            const end = Date.now() + duration;
            const colors = ['#0077b6', '#00b4d8', '#90e0ef'];
            (function frame() {
                confetti({ particleCount: 3, angle: 60, spread: 55, origin: { x: 0 }, colors: colors });
                confetti({ particleCount: 3, angle: 120, spread: 55, origin: { x: 1 }, colors: colors });
                if (Date.now() < end) requestAnimationFrame(frame);
            }());
        },

        goToProfile() { window.location.href = '/profile'; },
        goToPrescriptions() { window.location.href = '/prescriptions'; },
        goToPlans() { window.location.href = '/plan'; },
        goToHome() { window.location.href = '/'; }
    };
}