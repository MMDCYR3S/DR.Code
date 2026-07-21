// contacts.js — مدیریت لیست پیام‌ها با Alpine
document.addEventListener('alpine:init', () => {
    Alpine.data('contactManager', (config) => ({
        selectedMessages: [],
        allSelected: false,
        showDeleteModal: false,
        showBulkDeleteModal: false,
        deleteAction: '',
        deleteTitle: '',

        openDelete(id, title) {
            this.deleteAction = config.deleteUrlTpl.replace('0', id);
            this.deleteTitle = title;
            this.showDeleteModal = true;
        },

        openDetail(id) {
            window.location.href = config.detailUrlTpl.replace('0', id);
        },

        toggleSelectAll(checked) {
            const checkboxes = document.querySelectorAll('input[type="checkbox"][x-model="selectedMessages"]');
            if (checked) {
                this.selectedMessages = Array.from(checkboxes).map(cb => parseInt(cb.value));
            } else {
                this.selectedMessages = [];
            }
        },

        async bulkDelete() {
            if (!this.selectedMessages.length) return;
            try {
                const resp = await fetch(config.bulkDeleteUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                    body: JSON.stringify({ message_ids: this.selectedMessages })
                });
                const data = await resp.json();
                if (data.success) {
                    window.location.reload();
                } else {
                    alert('خطا: ' + (data.error || 'عملیات ناموفق'));
                }
            } catch (e) {
                alert('خطا در ارتباط با سرور');
            }
            this.showBulkDeleteModal = false;
        },

        init() {
            this.$watch('selectedMessages', () => {
                const total = document.querySelectorAll('input[type="checkbox"][x-model="selectedMessages"]').length;
                this.allSelected = this.selectedMessages.length > 0 && this.selectedMessages.length === total;
            });
        }
    }));
});