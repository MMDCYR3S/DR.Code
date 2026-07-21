document.addEventListener('alpine:init', () => {
    Alpine.data('tutorialManager', (config) => ({
        showForm: false,
        showDelete: false,
        showPreview: false,
        isEdit: false,
        formAction: config.createUrl,
        deleteAction: '',
        previewTitle: '',
        tutorial: { id: null, title: '', aparat_url: '' },
        tutorials: [],

        init(data) {
            this.tutorials = data || [];
        },

        openCreate() {
            this.isEdit = false;
            this.tutorial = { id: null, title: '', aparat_url: '' };
            this.formAction = config.createUrl;
            this.showForm = true;
        },

        openEdit(id, title) {
            this.isEdit = true;
            this.tutorial = { id, title, aparat_url: '' };
            this.formAction = config.updateUrlTpl.replace('0', id);

            // بارگذاری کد embed
            fetch(config.embedUrlTpl.replace('0', id), {
                headers: { 'X-CSRFToken': this.getCsrfToken() }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.tutorial.aparat_url = data.aparat_url;
                }
            })
            .catch(() => {});

            this.showForm = true;
        },

        openDelete(id, title) {
            this.tutorial = { id, title, aparat_url: '' };
            this.deleteAction = config.deleteUrlTpl.replace('0', id);
            this.showDelete = true;
        },

        openPreview(id) {
            const tutorial = this.tutorials.find(t => t.id === id);
            if (!tutorial) return;

            this.previewTitle = tutorial.title;
            this.showPreview = true;

            // بارگذاری کد embed
            fetch(config.embedUrlTpl.replace('0', id), {
                headers: { 'X-CSRFToken': this.getCsrfToken() }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const container = document.getElementById('preview-container');
                    if (container) {
                        container.innerHTML = data.aparat_url;
                    }
                }
            })
            .catch(() => {});
        },

        submitForm() {
            const form = document.querySelector('#showForm form');
            if (!form) return;

            const formData = new FormData(form);
            const data = {
                title: formData.get('title'),
                aparat_url: formData.get('aparat_url')
            };

            fetch(this.formAction, {
                method: this.isEdit ? 'PUT' : 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(data)
            })
            .then(res => res.json())
            .then(response => {
                if (response.success) {
                    window.location.reload();
                } else {
                    alert(response.message || 'خطا در ذخیره');
                }
            })
            .catch(() => alert('خطا در ارتباط با سرور'));
        },

        getCsrfToken() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        }
    }));
});