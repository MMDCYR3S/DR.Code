// Payment Verification Page Logic
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
            try {
                this.loading = true;
                this.error = null;
        
                const urlParams = new URLSearchParams(window.location.search);
                
                // ✅ اگه gateway نبود، از Authority تشخیص بده
                let gateway = urlParams.get('gateway');
                const authority = urlParams.get('Authority');
                const status = urlParams.get('Status');
        
                // ✅ اگه Authority داره و gateway نداره = حتماً زرین‌پاله
                if (!gateway && authority) {
                    gateway = 'zarinpal';
                    console.log('✅ Gateway detected from Authority: zarinpal');
                }
        
                console.log('🔍 Payment verification started:', { gateway, authority, status });
        
                // Zarinpal
                if (gateway === 'zarinpal') {
                    if (!authority) {
                        throw new Error('کد Authority یافت نشد');
                    }
        
                    if (status === 'NOK') {
                        this.success = false;
                        this.errorMessage = 'پرداخت توسط کاربر لغو شد';
                        this.loading = false;
                        this.cleanup();
                        return;
                    }
        
                    // ✅ مستقیم با fetch
                    const token = StorageManager.getAccessToken();
                    const url = `http://127.0.0.1:8000/api/v1/payment/zarinpal/verify/?Authority=${authority}&Status=${status}`;
                    
                    console.log('🔗 Verify URL:', url);
        
                    const response = await fetch(url, {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        }
                    });
        
                    console.log('📊 Response Status:', response.status);
        
                    const data = await response.json();
                    console.log('📦 Response Data:', data);
        
                    if (!response.ok) {
                        throw new Error(data.message || data.detail || 'خطا در تایید پرداخت');
                    }
        
                    // ✅ موفقیت!
                    this.success = true;
                    this.paymentData = data;
                    this.refId = data.ref_id || '';
                    this.paymentDate = this.formatDate(new Date());
        
                    console.log('✅ Payment verified successfully!');
        
                    // به‌روزرسانی پروفایل
                    await this.updateUserProfile();
        
                } else {
                    throw new Error('درگاه پرداخت نامعتبر است');
                }
        
            } catch (error) {
                console.error('❌ Payment verification error:', error);
                this.success = false;
                this.errorMessage = error.message || 'خطا در بررسی وضعیت پرداخت';
            } finally {
                this.loading = false;
                this.cleanup();
            }
        }
        
        ,
        

        async updateUserProfile() {
            try {
                console.log('🔄 Updating user profile...');
                
                // فراخوانی API پروفایل برای بروزرسانی نقش کاربر
                const profile = await API.profile.getProfile();
                
                // ذخیره اطلاعات جدید با استفاده از متد موجود
                const currentData = StorageManager.getUserData();
                StorageManager.saveUserData({
                    ...currentData,
                    role: profile.role,
                    subscription_status: profile.subscription_status
                });
                
                console.log('✅ Profile updated successfully');
            } catch (error) {
                console.error('⚠️ Error updating profile:', error);
                // در صورت خطا، باز هم ادامه بده (چون پرداخت موفق بوده)
            }
        },

        cleanup() {
            // پاکسازی localStorage با استفاده مستقیم از localStorage
            localStorage.removeItem('drcode_pending_order');
            localStorage.removeItem('drcode_payment_gateway');
            console.log('🧹 Cleanup completed');
        },

        copyRefId() {
            if (!this.refId) return;

            navigator.clipboard.writeText(this.refId).then(() => {
                // نمایش پیام موفقیت
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
            // بررسی وجود کتابخانه confetti
            if (typeof confetti === 'undefined') {
                console.warn('Confetti library not loaded');
                return;
            }

            // انیمیشن کانفتی
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
