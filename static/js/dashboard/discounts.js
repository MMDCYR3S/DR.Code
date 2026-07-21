document.addEventListener('alpine:init', () => {
    Alpine.data('discountManager', (config) => ({
        showForm: false,
        showDelete: false,
        isEdit: false,
        formAction: config.createUrl,
        deleteAction: '',
        discount: {
            id: null,
            title: '',
            code: '',
            discount_percent: '',
            start_at: '',
            end_at: '',
            max_usage: 100,
            is_active: true
        },

        openCreate() {
            this.isEdit = false;
            this.discount = {
                id: null, title: '', code: '', discount_percent: '',
                start_at: '', end_at: '', max_usage: 100, is_active: true
            };
            this.formAction = config.createUrl;
            this.showForm = true;
        },

        openEdit(id, title, code, percent, startAt, endAt, maxUsage, isActive) {
            this.isEdit = true;
            this.discount = {
                id, title, code,
                discount_percent: percent,
                start_at: startAt,
                end_at: endAt,
                max_usage: maxUsage,
                is_active: isActive
            };
            this.formAction = config.updateUrlTpl.replace('0', id);
            this.showForm = true;
        },

        openDelete(id, title) {
            this.discount = { ...this.discount, title };
            this.deleteAction = config.deleteUrlTpl.replace('0', id);
            this.showDelete = true;
        },
    }));
});