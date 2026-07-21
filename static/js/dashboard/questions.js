document.addEventListener('alpine:init', () => {
    Alpine.data('questionManager', (config) => ({
        showDelete: false,
        deleteAction: '',
        question: { id: null, user: '' },

        openDelete(id, user) {
            this.question = { id, user };
            this.deleteAction = config.deleteUrlTpl.replace('0', id);
            this.showDelete = true;
        },

        markAsRead(id) {
            if (confirm('آیا این سوال را به عنوان خوانده شده علامت‌گذاری می‌کنید؟')) {
                fetch(config.markReadUrlTpl.replace('0', id), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                    body: 'action=mark_read'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert(data.message);
                    }
                });
            }
        },

        markAsUnread(id) {
            if (confirm('آیا این سوال را به عنوان خوانده نشده علامت‌گذاری می‌کنید؟')) {
                fetch(config.markUnreadUrlTpl.replace('0', id), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                    body: 'action=mark_unread'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert(data.message);
                    }
                });
            }
        },
    }));
});