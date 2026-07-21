document.addEventListener('alpine:init', () => {
    Alpine.data('prescriptionManager', (config) => ({
        showDelete: false,
        deleteAction: '',
        prescription: { id: null, title: '' },

        openDelete(id, title) {
            this.prescription = { id, title };
            this.deleteAction = config.deleteUrlTpl.replace('0', id);
            this.showDelete = true;
        },
    }));
});