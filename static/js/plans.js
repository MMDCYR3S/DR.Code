function plansApp() {
    return {
        loading: true,
        groupedPlans: [],
        meta: {},
        openFaq: null,

        async init() {
            await this.loadPlans();
        },

        async loadPlans() {
            try {
                this.loading = true;
                const response = await API.plans.getPlans();

                if (response.success) {
                    const plans = response.data.results.results || [];
                    this.meta = response.data.meta || {};

                    // گروه‌بندی بر اساس membership_name
                    const groups = {};
                    plans.forEach(plan => {
                        const key = plan.membership_name;
                        if (!groups[key]) {
                            groups[key] = { membership_name: key, membership_description: plan.membership_description, plans: [] };
                        }
                        groups[key].plans.push(plan);
                    });

                    this.groupedPlans = Object.values(groups).map(group => {
                        group.plans.sort((a, b) => a.duration_days - b.duration_days);
                        return group;
                    });

                } else {
                    throw new Error(response.message || 'خطا در دریافت پلن‌ها');
                }
            } catch (error) {
                console.error('❌ Error loading plans:', error);
                Swal.fire({ icon: 'error', title: 'خطا', text: 'خطا در بارگذاری پلن‌ها. لطفاً صفحه را رفرش کنید.', confirmButtonText: 'باشه' });
            } finally {
                this.loading = false;
            }
        },

        selectPlan(plan) {
            window.location.href = `/order/checkout/${plan.id}/`;
        },

        toggleFaq(id) {
            this.openFaq = this.openFaq === id ? null : id;
        },

        scrollToPlans() {
            const el = document.querySelector('#plans');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };
}
