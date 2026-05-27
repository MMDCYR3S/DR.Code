// payment_gateway.js
document.addEventListener('alpine:init', () => {
    Alpine.data('paymentGatewayApp', () => ({
        loading: true,
        submitting: false,
        selectedGateway: null,
        orderData: null,
        planId: null,
        discountCode: '',
        referralCode: '',

        async init() {
            console.log('💳 Payment Gateway page initialized');
            
            // بررسی احراز هویت
            if (!this.checkAuth()) {
                return;
            }
            
            // دریافت اطلاعات سفارش از localStorage یا URL
            this.loadOrderData();
            
            this.loading = false;
        },

        checkAuth() {
            if (!StorageManager.isLoggedIn()) {
                Swal.fire({
                    icon: 'warning',
                    title: 'لطفاً وارد شوید',
                    text: 'برای ادامه خرید باید وارد حساب کاربری خود شوید',
                    confirmButtonText: 'ورود',
                    confirmButtonColor: '#0077b6'
                }).then(() => {
                    window.location.href = '/';
                });
                return false;
            }

            let profile = JSON.parse(localStorage.getItem('drcode_user_profile'));
            console.log(profile);
            
            if (!profile || profile.data.auth_status !== 'APPROVED') {
                Swal.fire({
                    icon: 'error',
                    title: 'احراز هویت لازم است',
                    text: 'برای خرید اشتراک باید احراز هویت شما تایید شده باشد',
                    confirmButtonText: 'رفتن به پروفایل',
                    confirmButtonColor: '#0077b6'
                }).then(() => {
                    window.location.href = '/profile';
                });
                return false;
            }

            return true;
        },

        loadOrderData() {
            // دریافت اطلاعات از localStorage (که از صفحه قبل ذخیره شده)
            const savedOrder = localStorage.getItem('drcode_pending_order');
            
            if (savedOrder) {
                try {
                    this.orderData = JSON.parse(savedOrder);
                    this.planId = this.orderData.plan_id;
                    this.discountCode = this.orderData.discount_code || '';
                    this.referralCode = this.orderData.referral_code || '';
                    
                    console.log('✅ Order data loaded:', this.orderData);
                } catch (error) {
                    console.error('❌ Error parsing order data:', error);
                    this.showError('خطا در بارگذاری اطلاعات سفارش');
                }
            } else {
                // اگر اطلاعات نبود، به صفحه قبل برگرد
                Swal.fire({
                    icon: 'warning',
                    title: 'اطلاعات سفارش یافت نشد',
                    text: 'لطفاً دوباره تلاش کنید',
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#0077b6'
                }).then(() => {
                    window.location.href = '/plan/';
                });
            }
        },

        selectGateway(gateway) {
            this.selectedGateway = gateway;
            console.log('🏦 Selected gateway:', gateway);
        },

        async proceedToPayment() {
            if (!this.selectedGateway) {
                Swal.fire({
                    icon: 'warning',
                    title: 'انتخاب درگاه',
                    text: 'لطفاً یک درگاه پرداخت را انتخاب کنید',
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#0077b6'
                });
                return;
            }

            try {
                this.submitting = true;
                console.log('💳 Processing payment...');

                let response;
                
                // بسته به درگاه انتخابی، API مناسب رو صدا می‌زنیم
                if (this.selectedGateway === 'zarinpal') {
                    response = await API.payment.createZarinpalPayment({
                        plan_id: this.planId,
                        discount_code: this.discountCode
                    });
                } else if (this.selectedGateway === 'parspal') {
                    response = await API.payment.createParspalPayment({
                        plan_id: this.planId,
                        discount_code: this.discountCode
                    });
                }

                if (response.success) {
                    console.log('✅ Payment created:', response);
                    


                    // ذخیره payment_id در localStorage
                    localStorage.setItem('drcode_payment_id', response.payment_id);
                    
                    // نمایش پیام موفقیت و انتقال به درگاه
                    Swal.fire({
                        icon: 'success',
                        title: 'در حال انتقال',
                        text: 'در حال انتقال به درگاه پرداخت...',
                        timer: 2000,
                        showConfirmButton: false
                    }).then(() => {
                        // انتقال به درگاه پرداخت
                        window.location.href = response.payment_url;
                    });
                } else {
                    throw new Error(response.message || 'خطا در ایجاد درخواست پرداخت');
                }

            } catch (error) {
                console.error('❌ Payment error:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'خطا در پرداخت',
                    text: error.message || 'لطفاً دوباره تلاش کنید',
                    confirmButtonText: 'باشه'
                });
            } finally {
                this.submitting = false;
            }
        },

        showError(message) {
            Swal.fire({
                icon: 'error',
                title: 'خطا',
                text: message,
                confirmButtonText: 'باشه'
            });
        }
    }));
});
