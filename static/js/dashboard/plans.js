document.addEventListener('alpine:init', () => {
    Alpine.data('planManager', (config) => ({
        // ===== State =====
        isMembershipModalOpen: false,
        isPlanModalOpen: false,
        isFeatureModalOpen: false,
        showDelete: false,
        isEditMode: false,
        isLoading: false,
        editingId: null,
        deleteType: null, // 'membership', 'plan', 'feature'
        deleteId: null,
        deleteTitle: '',

        // ===== Forms =====
        membershipForm: { title: '', description: '', features: [], is_active: true },
        planForm: { membership: '', name: '', tag: '', duration_days: '', price: '', is_active: true },
        featureForm: { name: '', feature_type: '', description: '', is_active: true },

        // ===== Membership Methods =====
        openAddMembershipModal() {
            this.isEditMode = false;
            this.editingId = null;
            this.membershipForm = { title: '', description: '', features: [], is_active: true };
            this.isMembershipModalOpen = true;
        },

        openEditMembershipModal(id, title, description, isActive, features) {
            this.isEditMode = true;
            this.editingId = id;
            this.membershipForm = { title, description, features: features || [], is_active: isActive };
            this.isMembershipModalOpen = true;
        },

        closeMembershipModal() {
            this.isMembershipModalOpen = false;
        },

        get membershipModalTitle() {
            return this.isEditMode ? 'ویرایش Membership' : 'افزودن Membership جدید';
        },

        get membershipFormSubmitText() {
            return this.isEditMode ? 'بروزرسانی' : 'ایجاد';
        },

        async submitMembershipForm() {
            this.isLoading = true;
            const url = this.isEditMode
                ? config.membershipUpdateUrlTpl.replace('0', this.editingId)
                : config.membershipCreateUrl;
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(this.membershipForm)
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

        openDeleteMembership(id, title) {
            this.deleteType = 'membership';
            this.deleteId = id;
            this.deleteTitle = title;
            this.showDelete = true;
        },

        // ===== Plan Methods =====
        openAddPlanModal() {
            this.isEditMode = false;
            this.editingId = null;
            this.planForm = { membership: '', name: '', tag: '', duration_days: '', price: '', is_active: true };
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
                    },
                    body: JSON.stringify(this.planForm)
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

        // ===== Feature Methods =====
        openAddFeatureModal() {
            this.isEditMode = false;
            this.editingId = null;
            this.featureForm = { name: '', feature_type: '', description: '', is_active: true };
            this.isFeatureModalOpen = true;
        },

        openEditFeatureModal(id) {
            fetch(config.featureDetailUrlTpl.replace('0', id), {
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
                    this.featureForm = {
                        name: data.data.name,
                        feature_type: data.data.feature_type,
                        description: data.data.description || '',
                        is_active: data.data.is_active
                    };
                    this.isFeatureModalOpen = true;
                } else {
                    this.showNotification('error', data.message || 'خطا در دریافت اطلاعات');
                }
            })
            .catch(error => {
                console.error('Error loading feature:', error);
                this.showNotification('error', 'خطا در دریافت اطلاعات ویژگی');
            });
        },

        closeFeatureModal() {
            this.isFeatureModalOpen = false;
        },

        get featureModalTitle() {
            return this.isEditMode ? 'ویرایش ویژگی' : 'افزودن ویژگی جدید';
        },

        get featureFormSubmitText() {
            return this.isEditMode ? 'بروزرسانی' : 'ایجاد';
        },

        async submitFeatureForm() {
            this.isLoading = true;
            const url = this.isEditMode
                ? config.featureUpdateUrlTpl.replace('0', this.editingId)
                : config.featureCreateUrl;
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(this.featureForm)
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

        openDeleteFeature(id, title) {
            this.deleteType = 'feature';
            this.deleteId = id;
            this.deleteTitle = title;
            this.showDelete = true;
        },

        // ===== Delete Confirmation =====
        get deleteModalTitle() {
            const map = { membership: 'حذف Membership', plan: 'حذف پلن', feature: 'حذف ویژگی' };
            return map[this.deleteType] || 'حذف';
        },

        get deleteModalMessage() {
            return `آیا از حذف "${this.deleteTitle}" مطمئن هستید؟`;
        },

        async confirmDelete() {
            const urls = {
                membership: config.membershipDeleteUrlTpl.replace('0', this.deleteId),
                plan: config.planDeleteUrlTpl.replace('0', this.deleteId),
                feature: config.featureDeleteUrlTpl.replace('0', this.deleteId)
            };
            try {
                const res = await fetch(urls[this.deleteType], {
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
                    setTimeout(() => window.location.reload(), 1000);
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