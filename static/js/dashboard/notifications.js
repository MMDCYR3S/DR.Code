// notifications.js — مدیریت مودال‌ها و اتوکمپلیت کاربر (Alpine)
// آدرس‌ها از تمپلیت پاس داده می‌شوند:
// notificationManager({ userSearchUrl, singleCreateUrl, groupCreateUrl, singleDeleteTpl, groupDeleteTpl })
document.addEventListener('alpine:init', () => {
    Alpine.data('notificationManager', (config) => ({
        showForm: false,
        showDelete: false,
        mode: 'single',

        // ===== اتوکمپلیت گیرنده ===== //
        userQuery: '',
        userResults: [],
        userSearching: false,
        selectedUser: { id: null, full_name: '' },

        // ===== حذف ===== //
        deleteType: '',
        deleteTitle: '',
        deleteAction: '',

        // ===== آدرس‌ها ===== //
        singleCreateUrl: config.singleCreateUrl,
        groupCreateUrl: config.groupCreateUrl,

        openCreate() {
            this.mode = 'single';
            this.clearUser();
            this.showForm = true;
        },

        searchUsers() {
            const q = this.userQuery.trim();
            if (q.length < 2) {
                this.userResults = [];
                return;
            }
            this.userSearching = true;
            axios.get(config.userSearchUrl, { params: { q } })
                .then(res => { this.userResults = res.data.results || []; })
                .catch(() => { this.userResults = []; })
                .finally(() => { this.userSearching = false; });
        },

        selectUser(user) {
            this.selectedUser = { id: user.id, full_name: user.full_name };
            this.userResults = [];
            this.userQuery = '';
        },

        clearUser() {
            this.selectedUser = { id: null, full_name: '' };
            this.userQuery = '';
            this.userResults = [];
        },

        openDelete(type, id, title) {
            this.deleteType = type;
            this.deleteTitle = title;
            const tpl = type === 'group' ? config.groupDeleteTpl : config.singleDeleteTpl;
            this.deleteAction = tpl.replace('0', id);
            this.showDelete = true;
        },
    }));
});
