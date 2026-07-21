// categories.js — مدیریت مودال‌های دسته‌بندی (Alpine)
// آدرس‌ها از تمپلیت به‌صورت config پاس داده می‌شوند: categoryManager({ createUrl, updateUrlTpl, deleteUrlTpl })
document.addEventListener('alpine:init', () => {
    Alpine.data('categoryManager', (config) => ({
        showForm: false,
        showDelete: false,
        isEdit: false,
        formAction: config.createUrl,
        deleteAction: '',
        category: { id: null, title: '', color_code: '' },

        openCreate() {
            this.isEdit = false;
            this.category = { id: null, title: '', color_code: '' };
            this.formAction = config.createUrl;
            this.showForm = true;
        },

        openEdit(id, title, colorCode) {
            this.isEdit = true;
            this.category = { id, title, color_code: colorCode };
            this.formAction = config.updateUrlTpl.replace('0', id);
            this.showForm = true;
        },

        openDelete(id, title) {
            this.category = { id, title, color_code: '' };
            this.deleteAction = config.deleteUrlTpl.replace('0', id);
            this.showDelete = true;
        },
    }));
});
