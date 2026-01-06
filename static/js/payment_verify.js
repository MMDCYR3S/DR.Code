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
            
            // بررسی لاگین بودن
            if (!StorageManager.isLoggedIn()) {
                console.warn('⚠️ User not logged in, redirecting...');
                window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                return;
            }

            await this.verifyPayment();
        },

        async verifyPayment() {
            const urlParams = new URLSearchParams(window.location.search);
            
            // 🔍 تشخیص درگاه
            const gateway = urlParams.get('gateway');
            const authority = urlParams.get('Authority');
            const order_id = urlParams.get('order_id');
            const status = urlParams.get('Status') || urlParams.get('status');

            console.log('🔎 Payment Parameters:', { 
                gateway, 
                authority, 
                order_id, 
                status 
            });

            try {
                this.loading = true;

                // ✅ زرین‌پال
                if (authority || gateway === 'zarinpal') {
                    await this.verifyZarinpal(authority, status);
                }
                // ✅ پارس‌پال
                else if (order_id || gateway === 'parspal') {
                    await this.verifyParspal(order_id, status);
                }
                // ❌ درگاه نامشخص
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
        async verifyZarinpal(authority, status) {
            console.log('🟢 Verifying ZarinPal...');

            if (!authority) {
                throw new Error('کد Authority یافت نشد');
            }

            if (status === 'NOK') {
                throw new Error('پرداخت توسط کاربر لغو شد');
            }

            const token = StorageManager.getAccessToken();
            const url = '/api/v1/payment/zarinpal/verify/';

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    authority: authority,
                    status: status
                })
            });

            console.log('📊 ZarinPal Response Status:', response.status);

            const data = await response.json();
            console.log('📦 ZarinPal Response Data:', data);

            if (!response.ok) {
                throw new Error(data.error || data.message || data.detail || 'خطا در تایید پرداخت');
            }

            // ✅ موفقیت!
            this.success = true;
            this.paymentGateway = 'zarinpal';
            this.paymentData = data;
            this.refId = data.ref_id || '';
            this.paymentDate = this.formatDate(new Date());

            console.log('✅ ZarinPal payment verified successfully!');

            this.showConfetti();
            await this.updateUserProfile();
        },

        // ========== پارس‌پال ========== //
        async verifyParspal(order_id, status_code) {
            console.log('🟣 Verifying ParsPal...');

            if (!order_id) {
                throw new Error('شناسه سفارش یافت نشد');
            }

            // بررسی وضعیت
            if (status_code !== '100') {
                const messages = {
                    '99': 'انصراف کاربر از پرداخت',
                    '88': 'پرداخت ناموفق',
                    '77': 'لغو پرداخت توسط کاربر'
                };
                throw new Error(messages[status_code] || 'پرداخت ناموفق');
            }

            const token = StorageManager.getAccessToken();
            const url = '/api/v1/payment/parspal/verify/';

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    order_id: order_id
                })
            });

            console.log('📊 ParsPal Response Status:', response.status);

            const data = await response.json();
            console.log('📦 ParsPal Response Data:', data);

            if (!response.ok) {
                throw new Error(data.message || data.error || data.detail || 'خطا در تایید پرداخت');
            }

            if (!data.success) {
                throw new Error(data.message || 'تایید پرداخت ناموفق بود');
            }

            // ✅ موفقیت!
            this.success = true;
            this.paymentGateway = 'parspal';
            this.paymentData = data.data || data;
            
            // استخراج شماره مرجع
            this.refId = data.data?.reference_number || 
                         data.data?.transaction_id || 
                         data.data?.receipt_number || 
                         order_id;
            
            this.paymentDate = this.formatDate(new Date());

            console.log('✅ ParsPal payment verified successfully!');

            this.showConfetti();
            await this.updateUserProfile();
        },

        async updateUserProfile() {
            try {
                console.log('🔄 Updating user profile...');
                
                const profile = await API.profile.getProfile();
                
                const currentData = StorageManager.getUserData();
                StorageManager.saveUserData({
                    ...currentData,
                    role: profile.role,
                    subscription_status: profile.subscription_status,
                    subscription_end_date: profile.subscription_end_date
                });
                
                console.log('✅ Profile updated successfully');
            } catch (error) {
                console.error('⚠️ Error updating profile:', error);
            }
        },

        cleanup() {
            // پاکسازی localStorage
            localStorage.removeItem('drcode_pending_order');
            localStorage.removeItem('drcode_payment_gateway');
            console.log('🧹 Cleanup completed');
        },

        copyRefId() {
            if (!this.refId) return;

            navigator.clipboard.writeText(this.refId).then(() => {
                Swal.fire({
                    icon: 'success',
                    title: 'کپی شد!',
                    text: 'شماره پیگیری کپی شد',
                    timer: 2000,
                    showConfirmButton: false,
                    toast: true,
                    position: 'top-end'
                });
            }).catch(err => {
                console.error('Error copying:', err);
            });
        },

        formatDate(date) {
            if (!date) return '';
            
            const d = new Date(date);
            return new Intl.DateTimeFormat('fa-IR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(d);
        },

        showConfetti() {
            if (typeof confetti === 'undefined') {
                console.warn('Confetti library not loaded');
                return;
            }

            const duration = 3000;
            const end = Date.now() + duration;
            const colors = ['#0077b6', '#00b4d8', '#90e0ef'];

            (function frame() {
                confetti({
                    particleCount: 3,
                    angle: 60,
                    spread: 55,
                    origin: { x: 0 },
                    colors: colors
                });
                confetti({
                    particleCount: 3,
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

        goToProfile() {
            window.location.href = '/profile';
        },

        goToPrescriptions() {
            window.location.href = '/prescriptions';
        },

        goToPlans() {
            window.location.href = '/plan';
        },

        goToHome() {
            window.location.href = '/';
        }
    };
}
