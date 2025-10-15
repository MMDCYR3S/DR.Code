// Plans Page Logic
function plansApp() {
    return {
        loading: true,
        plans: [],
        meta: {},
        openFaq: null,

        async init() {
            console.log('🎯 Plans page initialized');
            await this.loadPlans();
        },

        async loadPlans() {
            try {
                this.loading = true;
                console.log('📡 Fetching plans...');

                const response = await API.plans.getPlans();
                
                if (response.success) {
                    this.plans = response.data.results.results || [];
                    this.meta = response.data.meta || {};
                    
                    // Mark recommended plan (یک ساله یا بیشترین مدت)
                    if (this.plans.length > 0) {
                        const maxDuration = Math.max(...this.plans.map(p => p.duration_months));
                        this.plans.forEach(plan => {
                            plan.is_recommended = plan.duration_months === maxDuration;
                        });
                    }
                    
                    console.log('✅ Plans loaded:', this.plans);
                    console.log('📊 Meta:', this.meta);
                } else {
                    throw new Error(response.message || 'خطا در دریافت پلن‌ها');
                }

            } catch (error) {
                console.error('❌ Error loading plans:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'خطا',
                    text: 'خطا در بارگذاری پلن‌ها. لطفاً صفحه را رفرش کنید.',
                    confirmButtonText: 'باشه'
                });
            } finally {
                this.loading = false;
            }
        },

        selectPlan(plan) {
            console.log('🛒 Plan selected:', plan);
            
            // فعلاً فقط لاگ می‌کنیم
            // بعداً این قسمت به صفحه خرید یا مودال متصل می‌شود
            Swal.fire({
                icon: 'info',
                title: 'در حال توسعه',
                html: `
                    <div class="text-right" dir="rtl">
                        <p class="mb-3">پلن انتخابی: <strong>${plan.name}</strong></p>
                        <p class="mb-3">قیمت: <strong>${plan.formatted_price}</strong></p>
                        <p class="text-gray-600 text-sm">این بخش در حال توسعه است و به زودی به درگاه پرداخت متصل خواهد شد.</p>
                    </div>
                `,
                confirmButtonText: 'متوجه شدم',
                confirmButtonColor: '#0ea5e9'
            });
        },

        toggleFaq(id) {
            this.openFaq = this.openFaq === id ? null : id;
        },

        scrollToPlans() {
            const plansSection = document.querySelector('section:nth-of-type(1)');
            if (plansSection) {
                plansSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    };
}
