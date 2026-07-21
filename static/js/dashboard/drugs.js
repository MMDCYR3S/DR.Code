// drugs.js — مدیریت مودال‌های دارو (Alpine)
// آدرس‌ها از تمپلیت به‌صورت config پاس داده می‌شوند: drugManager({ createUrl, updateUrlTpl, deleteUrlTpl })
document.addEventListener('alpine:init', () => {
    Alpine.data('drugManager', (config) => ({
        showForm: false,
        showDelete: false,
        isEdit: false,
        formAction: config.createUrl,
        deleteAction: '',
        drug: { id: null, title: '', code: '', is_for_order: false },

        openCreate() {
            this.isEdit = false;
            this.drug = { id: null, title: '', code: '', is_for_order: false };
            this.formAction = config.createUrl;
            this.showForm = true;
        },

        openEdit(id, title, code, isForOrder) {
            this.isEdit = true;
            this.drug = { id, title, code, is_for_order: isForOrder };
            this.formAction = config.updateUrlTpl.replace('0', id);
            this.showForm = true;
        },

        openDelete(id, title) {
            this.drug = { id, title, code: '', is_for_order: false };
            this.deleteAction = config.deleteUrlTpl.replace('0', id);
            this.showDelete = true;
        },
    }));
});
