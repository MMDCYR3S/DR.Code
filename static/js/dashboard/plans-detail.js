document.addEventListener('alpine:init', () => {
    Alpine.data('membershipDetailManager', (config) => ({
        // ===== State =====
        isPlanModalOpen: false,
        showDelete: false,
        isEditMode: false,
        isLoading: false,
        editingId: null,
        deleteType: null,
        deleteId: null,
        deleteTitle: '',

        // ===== برای مودال‌های Membership و Feature (فقط برای جلوگیری از خطا) =====
        isMembershipModalOpen: false,
        isFeatureModalOpen: false,
        membershipForm: { title: '', description: '', features: [], is_active: true },
        featureForm: { name: '', feature_type: '', description: '', is_active: true },

        // ===== Plan Form =====
        planForm: { membership: '', name: '', tag: '', duration_days: '', price: '', is_active: true },

        // ===== Plan Methods =====
        openAddPlanModal() {
            this.isEditMode = false;
            this.editingId = null;
            this.planForm = { membership: '{{ membership.id }}', name: '', tag: '', duration_days: '', price: '', is_active: true };
            this.isPlanModalOpen = true;
        },

        openEditPlanModal(id) {
            fetch(config.planDetailUrlTpl.replace('0', id), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    this.isEditMode = true;
                    this.editingId = id;
                    this.planForm = {
                        membership: data.data.membership,
                        name: data.data.name,
                        tag: data.data.tag || '',
                        duration_days: data.data.duration_days.toString(),
                        price: data.data.price,
                        is_active: data.data.is_active
                    };
                    this.isPlanModalOpen = true;
                } else {
                    this.showNotification('error', data.message || 'خطا در دریافت اطلاعات');
                }
            })
            .catch(error => {
                console.error('Error loading plan:', error);
                this.showNotification('error', 'خطا در دریافت اطلاعات پلن');
            });
        },

        closePlanModal() {
            this.isPlanModalOpen = false;
        },

        get planModalTitle() {
            return this.isEditMode ? 'ویرایش پلن' : 'افزودن پلن جدید';
        },

        get planFormSubmitText() {
            return this.isEditMode ? 'بروزرسانی' : 'ایجاد';
        },

        async submitPlanForm() {
            this.isLoading = true;
            const url = this.isEditMode
                ? config.planUpdateUrlTpl.replace('0', this.editingId)
                : config.planCreateUrl;
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },                    body: JSON.stringify(this.planForm)
                });
                const data = await res.json();
                if (data.success) {
                    this.showNotification('success', data.message);
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    this.showNotification('error', data.message || 'خطا');
                }
            } catch (e) {
                this.showNotification('error', 'خطا در ارتباط با سرور');
            } finally {
                this.isLoading = false;
            }
        },

        openDeletePlan(id, title) {
            this.deleteType = 'plan';
            this.deleteId = id;
            this.deleteTitle = title;
            this.showDelete = true;
        },

        // ===== متدهای ساختگی برای Membership (فقط برای جلوگیری از خطا) =====
        openAddMembershipModal() {},
        openEditMembershipModal() {},
        closeMembershipModal() { this.isMembershipModalOpen = false; },
        submitMembershipForm() {},
        openDeleteMembership() {},

        // ===== متدهای ساختگی برای Feature (فقط برای جلوگیری از خطا) =====
        openAddFeatureModal() {},
        openEditFeatureModal() {},
        closeFeatureModal() { this.isFeatureModalOpen = false; },
        submitFeatureForm() {},
        openDeleteFeature() {},

        // ===== Getterهای ساختگی برای Membership =====
        get membershipModalTitle() { return ''; },
        get membershipFormSubmitText() { return ''; },

        // ===== Getterهای ساختگی برای Feature =====
        get featureModalTitle() { return ''; },
        get featureFormSubmitText() { return ''; },

        // ===== Delete Membership =====
        deleteMembership() {
            this.deleteType = 'membership';
            this.deleteId = '{{ membership.id }}';
            this.deleteTitle = '{{ membership.title|escapejs }}';
            this.showDelete = true;
        },

        // ===== Confirm Delete =====
        get deleteModalTitle() {
            return this.deleteType === 'plan' ? 'حذف پلن' : 'حذف Membership';
        },

        get deleteModalMessage() {
            return `آیا از حذف "${this.deleteTitle}" مطمئن هستید؟`;
        },

        async confirmDelete() {
            const url = this.deleteType === 'plan'
                ? config.planDeleteUrlTpl.replace('0', this.deleteId)
                : config.membershipDeleteUrl;
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                });
                const data = await res.json();
                if (data.success) {
                    this.showNotification('success', data.message);
                    if (this.deleteType === 'membership') {
                        window.location.href = '{% url "dashboard:plans:plan_list" %}';
                    } else {
                        setTimeout(() => window.location.reload(), 1000);
                    }
                } else {
                    this.showNotification('error', data.message);
                }
            } catch (e) {
                this.showNotification('error', 'خطا در حذف');
            }
            this.showDelete = false;
        },

        // ===== Helpers =====
        getCsrfToken() {
            // اول از همه از المنت مخفی در صفحه بخون
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfInput) {
                return csrfInput.value;
            }
            // اگر پیدا نشد، از کوکی (فقط به عنوان fallback)
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, 10) === ('csrftoken' + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(11));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        showNotification(type, message) {
            window.dispatchEvent(new CustomEvent('notify', { detail: { type, message } }));
        }
    }));
});