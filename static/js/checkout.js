// checkout.js
document.addEventListener('alpine:init', () => {
    Alpine.data('checkoutApp', () => ({
        loading: true,
        submitting: false,
        planId: null,
        planData: null,
        discountCode: '',
        referralCode: '',

        async init() {
            console.log('🛒 Checkout page initialized');
            
            // بررسی احراز هویت و لاگین
            if (!this.checkAuth()) {
                return;
            }
            
            // دریافت plan_id از URL
            this.planId = this.getPlanIdFromUrl();
            
            if (!this.planId) {
                this.showError('شناسه پلن یافت نشد');
                setTimeout(() => window.location.href = '/plan', 2000);
                return;
            }
            
            // بارگذاری اطلاعات پلن
            await this.loadPlanDetails();
        },

        checkAuth() {
            // بررسی لاگین بودن
            if (!StorageManager.isLoggedIn()) {
                Swal.fire({
                    icon: 'warning',
                    title: 'لطفاً وارد شوید',
                    text: 'برای خرید اشتراک باید ابتدا وارد حساب کاربری خود شوید',
                    confirmButtonText: 'ورود به حساب',
                    confirmButtonColor: '#0077b6',
                    showCancelButton: true,
                    cancelButtonText: 'بازگشت'
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = '/';
                    } else {
                        window.location.href = '/plan';
                    }
                });
                return false;
            }

            // بررسی احراز هویت
            const profile = JSON.parse(localStorage.getItem("drcode_user_profile")).data
            console.log("AUTH_STATUS: ", profile.auth_status);
            console.log("ROLE: ", profile.role); 
            
            if (!profile || profile.auth_status !== 'APPROVED') {
                Swal.fire({
                    icon: 'error',
                    title: 'احراز هویت لازم است',
                    html: `
                        <div class="text-right" dir="rtl">
                            <p class="mb-3">برای خرید اشتراک، باید احراز هویت شما تایید شده باشد.</p>
                            <p class="text-sm text-gray-600">
                                ${profile?.auth_status === 'PENDING' 
                                    ? 'احراز هویت شما در حال بررسی است. لطفاً منتظر بمانید.' 
                                    : profile?.auth_status === 'REJECTED'
                                    ? 'احراز هویت شما رد شده است. لطفاً مجدداً اقدام کنید.'
                                    : 'لطفاً ابتدا احراز هویت خود را تکمیل کنید.'}
                            </p>
                        </div>
                    `,
                    confirmButtonText: 'رفتن به پروفایل',
                    confirmButtonColor: '#0077b6',
                    showCancelButton: true,
                    cancelButtonText: 'بازگشت'
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = '/authentication';
                    } else {
                        window.location.href = '/plan';
                    }
                });
                return false;
            }

            console.log('✅ Auth check passed');
            return true;
        },

        getPlanIdFromUrl() {
            // استخراج plan_id از URL
            // URL format: /order/checkout/1 یا /order/checkout/1/
            const pathParts = window.location.pathname.split('/').filter(p => p);
            const planId = pathParts[pathParts.length - 1];
            
            console.log('📍 Plan ID from URL:', planId);
            return planId;
        },

        async loadPlanDetails() {
            try {
                this.loading = true;
                console.log('📡 Loading plan details for ID:', this.planId);

                const response = await API.orders.getPlanDetails(this.planId);

                if (response.success) {
                    this.planData = response.data;
                    console.log('✅ Plan details loaded:', this.planData);
                } else {
                    throw new Error(response.message || 'خطا در دریافت اطلاعات پلن');
                }

            } catch (error) {
                console.error('❌ Error loading plan details:', error);
                this.showError('خطا در بارگذاری اطلاعات پلن');
                setTimeout(() => window.location.href = '/plan', 2000);
            } finally {
                this.loading = false;
            }
        },

        async applyDiscountCode() {
            try {
                this.submitting = true;
                console.log('🎟️ Applying discount code...');

                // اگر هیچ کدی وارد نشده
                if (!this.discountCode && !this.referralCode) {
                    Swal.fire({
                        icon: 'warning',
                        title: 'توجه',
                        text: 'لطفاً حداقل یک کد تخفیف یا کد معرف وارد کنید',
                        confirmButtonText: 'باشه',
                        confirmButtonColor: '#0077b6'
                    });
                    return;
                }

                const response = await API.orders.applyDiscountCode(this.planId, {
                    discount_code: this.discountCode || '',
                    referral_code: this.referralCode || ''
                });

                if (response.success) {
                    this.planData = response.data;
                    
                    Swal.fire({
                        icon: 'success',
                        title: 'کد اعمال شد',
                        text: response.message || 'کد با موفقیت اعمال شد',
                        confirmButtonText: 'باشه',
                        confirmButtonColor: '#0077b6'
                    });

                    console.log('✅ Discount applied:', this.planData);
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'خطا',
                        text: response.message || 'کد تخفیف معتبر نیست',
                        confirmButtonText: 'باشه'
                    });
                }

            } catch (error) {
                console.error('❌ Error applying discount:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'خطا',
                    text: 'خطا در اعمال کد. لطفاً دوباره تلاش کنید',
                    confirmButtonText: 'باشه'
                });
            } finally {
                this.submitting = false;
            }
        },

        async proceedToPayment() {
            try {
                this.submitting = true;
                console.log('🛒 Creating order...');

                // آماده‌سازی داده‌های کد تخفیف و ارجاع
                const codes = {
                    discount_code: this.discountCode || '',
                    referral_code: this.referralCode || ''
                };

                // فراخوانی API برای ایجاد سفارش
                const result = await API.orders.createOrder(this.planId, codes);

                if (!result.success) {
                    throw new Error(result.message || 'خطا در ثبت سفارش');
                }

                console.log('✅ Order created successfully:', result.data);

                // ذخیره اطلاعات سفارش برای استفاده در صفحه پرداخت
                const orderData = {
                    plan_id: this.planId,
                    plan_name: this.planData?.plan_info?.name,
                    formatted_price: this.planData?.pricing_info?.formatted_final_price,
                    discount_code: this.discountCode || '',
                    referral_code: this.referralCode || '',
                    has_discount: this.planData?.discount_info?.is_discounted || false,
                    discount_amount: this.planData?.pricing_info?.formatted_savings || '',
                    order_id: result.data?.id || null, // اضافه: شناسه سفارش از سرور
                };

                localStorage.setItem('drcode_pending_order', JSON.stringify(orderData));

                console.log('✅ Order data saved to localStorage:', orderData);

                // هدایت به صفحه پرداخت
                window.location.href = '/payment/request/';

            } catch (error) {
                console.error('❌ Error preparing order:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'خطا',
                    text: error.message || 'خطا در آماده‌سازی سفارش. لطفاً دوباره تلاش کنید',
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
