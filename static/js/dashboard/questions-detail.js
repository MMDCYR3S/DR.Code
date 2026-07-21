document.addEventListener('alpine:init', () => {
    Alpine.data('questionDetailManager', (config) => ({
        showDeleteModal: false,
        answerText: '',

        deleteQuestion() {
            this.showDeleteModal = true;
        },

        confirmDelete() {
            fetch(config.deleteUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: 'action=delete'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = data.redirect_url || '{% url "dashboard:questions:list" %}';
                } else {
                    alert(data.message);
                }
            });
        },

        markAsRead() {
            if (confirm('آیا این سوال را به عنوان خوانده شده علامت‌گذاری می‌کنید؟')) {
                fetch(config.markReadUrl, {
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

        markAsUnread() {
            if (confirm('آیا این سوال را به عنوان خوانده نشده علامت‌گذاری می‌کنید؟')) {
                fetch(config.markUnreadUrl, {
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

        formatText(command) {
            const textarea = document.getElementById('answer-textarea');
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const selectedText = textarea.value.substring(start, end);
            let formattedText = selectedText;
            if (command === 'bold') {
                formattedText = `**${selectedText}**`;
            } else if (command === 'italic') {
                formattedText = `*${selectedText}*`;
            }
            textarea.setRangeText(formattedText, start, end, 'end');
            textarea.focus();
        },

        insertText(text) {
            const textarea = document.getElementById('answer-textarea');
            const start = textarea.selectionStart;
            textarea.setRangeText(text, start, start, 'end');
            textarea.focus();
        },

        submitAnswer() {
            if (this.answerText.trim().length < 10) {
                alert('پاسخ باید حداقل ۱۰ کاراکتر باشد.');
                return;
            }
            document.querySelector('.answer-form').submit();
        }
    }));
});