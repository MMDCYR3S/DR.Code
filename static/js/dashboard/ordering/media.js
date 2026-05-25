/**
 * MediaManager
 * مدیریت فایل‌های پیوست (تصاویر و ویدیوها)
 * سبک کد: دقیقاً شبیه DynamicFieldManager
 */

const MediaManager = {
    orderId: null,
    addImageUrl: null,
    bulkImageUrl: null,
    addVideoUrl: null,
    updateImageUrlTemplate: null,
    deleteImageUrlTemplate: null,
    updateVideoUrlTemplate: null,
    deleteVideoUrlTemplate: null,

    // ─────────────────────────────────────────────────────────────────
    //  INIT
    // ─────────────────────────────────────────────────────────────────

    init(config = {}) {
        this.orderId        = config.orderId        || null;
        this.addImageUrl    = config.addImageUrl    || null;
        this.bulkImageUrl   = config.bulkImageUrl   || null;
        this.addVideoUrl    = config.addVideoUrl    || null;

        // URL templates (با placeholder <id>)
        this.updateImageUrlTemplate = config.updateImageUrl || `/orders/media/image/<id>/update/`;
        this.deleteImageUrlTemplate = config.deleteImageUrl || `/orders/media/image/<id>/delete/`;
        this.updateVideoUrlTemplate = config.updateVideoUrl || `/orders/media/video/<id>/update/`;
        this.deleteVideoUrlTemplate = config.deleteVideoUrl || `/orders/media/video/<id>/delete/`;

        this.attachEventListeners();
        this._initUploadZone();
        console.log('✅ MediaManager initialized');
    },

    // ─────────────────────────────────────────────────────────────────
    //  EVENT LISTENERS
    // ─────────────────────────────────────────────────────────────────

    attachEventListeners() {
        // آپلود تصویر از input
        document.getElementById('imageUploadInput')?.addEventListener('change', (e) => {
            const files = [...e.target.files];
            if (files.length) this._uploadImages(files);
            e.target.value = '';
        });

        // نمایش فرم افزودن ویدیو
        document.getElementById('addVideoBtn')?.addEventListener('click', () => {
            const form = document.getElementById('addVideoForm');
            if (form) {
                form.classList.toggle('hidden');
                if (!form.classList.contains('hidden')) {
                    document.getElementById('newVideoUrl')?.focus();
                }
            }
        });

        // تأیید افزودن ویدیو
        document.getElementById('confirmAddVideoBtn')?.addEventListener('click', () => {
            this._addVideo();
        });

        // انصراف فرم ویدیو
        document.getElementById('cancelAddVideoBtn')?.addEventListener('click', () => {
            document.getElementById('addVideoForm')?.classList.add('hidden');
            this._clearVideoForm();
        });

        // event delegation برای دکمه‌های تصویر و ویدیو
        document.addEventListener('click', (e) => {
            // ذخیره caption تصویر
            if (e.target.closest('.save-caption-btn')) {
                const card = e.target.closest('.media-image-card');
                if (card) this._saveCaption(card);
                return;
            }
            // حذف تصویر
            if (e.target.closest('.delete-image-btn')) {
                const card = e.target.closest('.media-image-card');
                if (card) this._deleteImage(card);
                return;
            }
            // ذخیره ویدیو
            if (e.target.closest('.save-video-btn')) {
                const card = e.target.closest('.video-card');
                if (card) this._saveVideo(card);
                return;
            }
            // حذف ویدیو
            if (e.target.closest('.delete-video-btn')) {
                const card = e.target.closest('.video-card');
                if (card) this._deleteVideo(card);
                return;
            }
        });
    },

    // ─────────────────────────────────────────────────────────────────
    //  UPLOAD ZONE — Drag & Drop
    // ─────────────────────────────────────────────────────────────────

    _initUploadZone() {
        const zone = document.getElementById('uploadZone');
        if (!zone) return;

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });
        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const files = [...e.dataTransfer.files].filter(f => f.type.startsWith('image/'));
            if (files.length) this._uploadImages(files);
        });
    },

    // ─────────────────────────────────────────────────────────────────
    //  IMAGE — آپلود چند تصویر
    // ─────────────────────────────────────────────────────────────────

    async _uploadImages(files) {
        if (!this.bulkImageUrl) return;

        const progressEl = document.getElementById('uploadProgress');
        const progressText = document.getElementById('uploadProgressText');

        if (progressEl) progressEl.classList.remove('hidden');
        if (progressText) progressText.textContent = `در حال آپلود ${files.length} تصویر...`;

        const formData = new FormData();
        files.forEach(f => formData.append('images', f));

        try {
            const res = await fetch(this.bulkImageUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': this._getCsrf() },
                body: formData,
            });
            const data = await res.json();
            if (data.success && data.images) {
                data.images.forEach(img => this._appendImageCard(img));
                this._updateImageCount();
                document.getElementById('imagesEmptyState')?.remove();
                this._showToast(`${data.images.length} تصویر آپلود شد.`, 'success');
            } else {
                this._showToast(data.error || 'خطا در آپلود', 'error');
            }
        } catch (err) {
            console.error(err);
            this._showToast('خطا در ارتباط با سرور', 'error');
        } finally {
            if (progressEl) progressEl.classList.add('hidden');
        }
    },

    _appendImageCard(img) {
        const grid = document.getElementById('imagesGrid');
        if (!grid) return;

        const count = grid.querySelectorAll('.media-image-card').length + 1;
        const html = `
            <div class="media-image-card relative group rounded-xl overflow-hidden border border-gray-200 shadow-sm"
                 data-image-id="${img.id}">
                <div class="aspect-square bg-gray-100">
                    <img src="${this.escapeHtml(img.url)}" alt="${this.escapeHtml(img.caption || '')}"
                         class="w-full h-full object-cover">
                </div>
                <div class="p-2">
                    <input type="text" dir="rtl" value="${this.escapeHtml(img.caption || '')}" placeholder="کپشن..."
                           class="image-caption w-full text-xs px-2 py-1 border border-gray-200 rounded focus:border-purple-400 focus:outline-none bg-gray-50">
                </div>
                <div class="absolute top-2 left-2 hidden group-hover:flex gap-1">
                    <button type="button" class="save-caption-btn bg-green-500 text-white p-1.5 rounded-lg text-xs hover:bg-green-600 transition shadow" title="ذخیره کپشن">
                        <i class="fas fa-check"></i>
                    </button>
                    <button type="button" class="delete-image-btn bg-red-500 text-white p-1.5 rounded-lg text-xs hover:bg-red-600 transition shadow" title="حذف تصویر">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="absolute top-2 right-2 bg-black bg-opacity-50 text-white text-xs px-1.5 py-0.5 rounded">
                    ${count}
                </div>
            </div>`;
        grid.insertAdjacentHTML('beforeend', html);
    },

    async _saveCaption(card) {
        const imageId = card.dataset.imageId;
        const caption = card.querySelector('.image-caption')?.value?.trim() || '';
        const url = this.updateImageUrlTemplate.replace('<id>', imageId);

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrf() },
                body: JSON.stringify({ caption }),
            });
            const data = await res.json();
            if (data.success) {
                this._showToast('کپشن ذخیره شد.', 'success');
            } else {
                this._showToast(data.error || 'خطا در ذخیره', 'error');
            }
        } catch (err) {
            this._showToast('خطا در ارتباط با سرور', 'error');
        }
    },

    async _deleteImage(card) {
        if (!confirm('آیا از حذف این تصویر اطمینان دارید؟')) return;
        const imageId = card.dataset.imageId;
        const url = this.deleteImageUrlTemplate.replace('<id>', imageId);

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': this._getCsrf() },
            });
            const data = await res.json();
            if (data.success) {
                card.remove();
                this._updateImageCount();
                this._showToast('تصویر حذف شد.', 'success');
            } else {
                this._showToast(data.error || 'خطا در حذف', 'error');
            }
        } catch (err) {
            this._showToast('خطا در ارتباط با سرور', 'error');
        }
    },

    _updateImageCount() {
        const grid = document.getElementById('imagesGrid');
        const count = grid ? grid.querySelectorAll('.media-image-card').length : 0;
        const el = document.getElementById('imageCount');
        if (el) el.textContent = `(${count} تصویر)`;
    },

    // ─────────────────────────────────────────────────────────────────
    //  VIDEO — افزودن / ذخیره / حذف
    // ─────────────────────────────────────────────────────────────────

    async _addVideo() {
        const url   = document.getElementById('newVideoUrl')?.value?.trim();
        const title = document.getElementById('newVideoTitle')?.value?.trim() || '';
        const desc  = document.getElementById('newVideoDesc')?.value?.trim() || '';

        if (!url) {
            document.getElementById('newVideoUrl')?.focus();
            this._showToast('لینک ویدیو اجباری است.', 'error');
            return;
        }
        if (!this.addVideoUrl) return;

        try {
            const res = await fetch(this.addVideoUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrf() },
                body: JSON.stringify({ video_url: url, title, description: desc }),
            });
            const data = await res.json();
            if (data.success && data.video) {
                this._appendVideoCard(data.video);
                document.getElementById('videosEmptyState')?.remove();
                this._updateVideoCount();
                document.getElementById('addVideoForm')?.classList.add('hidden');
                this._clearVideoForm();
                this._showToast('ویدیو اضافه شد.', 'success');
            } else {
                this._showToast(data.error || 'خطا در افزودن ویدیو', 'error');
            }
        } catch (err) {
            this._showToast('خطا در ارتباط با سرور', 'error');
        }
    },

    _appendVideoCard(video) {
        const list = document.getElementById('videosList');
        if (!list) return;
        const html = `
            <div class="video-card bg-gray-50 border border-gray-200 rounded-xl p-4"
                 data-video-id="${video.id}">
                <div class="flex items-start gap-3">
                    <div class="w-10 h-10 bg-pink-100 rounded-lg flex items-center justify-center shrink-0">
                        <i class="fas fa-video text-pink-500"></i>
                    </div>
                    <div class="flex-1 space-y-2">
                        <input type="text" dir="rtl" value="${this.escapeHtml(video.title || '')}" placeholder="عنوان ویدیو..."
                               class="video-title w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm bg-white focus:border-pink-400 focus:outline-none transition">
                        <input type="url" dir="ltr" value="${this.escapeHtml(video.video_url)}" placeholder="لینک embed..."
                               class="video-url w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm bg-white focus:border-pink-400 focus:outline-none transition">
                        <textarea dir="rtl" rows="2" placeholder="توضیحات (اختیاری)..."
                                  class="video-description w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm bg-white focus:border-pink-400 focus:outline-none transition resize-none">${this.escapeHtml(video.description || '')}</textarea>
                    </div>
                    <div class="flex flex-col gap-1">
                        <button type="button" class="save-video-btn text-xs px-2.5 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition font-medium">
                            <i class="fas fa-save ml-1"></i>ذخیره
                        </button>
                        <button type="button" class="delete-video-btn text-red-400 hover:text-red-600 p-1.5 rounded hover:bg-red-50 transition text-center">
                            <i class="fas fa-trash text-sm"></i>
                        </button>
                    </div>
                </div>
            </div>`;
        list.insertAdjacentHTML('beforeend', html);
    },

    async _saveVideo(card) {
        const videoId = card.dataset.videoId;
        const title       = card.querySelector('.video-title')?.value?.trim() || '';
        const video_url   = card.querySelector('.video-url')?.value?.trim() || '';
        const description = card.querySelector('.video-description')?.value?.trim() || '';
        const url = this.updateVideoUrlTemplate.replace('<id>', videoId);

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrf() },
                body: JSON.stringify({ title, video_url, description }),
            });
            const data = await res.json();
            if (data.success) {
                this._showToast('ویدیو ذخیره شد.', 'success');
            } else {
                this._showToast(data.error || 'خطا در ذخیره', 'error');
            }
        } catch (err) {
            this._showToast('خطا در ارتباط با سرور', 'error');
        }
    },

    async _deleteVideo(card) {
        if (!confirm('آیا از حذف این ویدیو اطمینان دارید؟')) return;
        const videoId = card.dataset.videoId;
        const url = this.deleteVideoUrlTemplate.replace('<id>', videoId);

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': this._getCsrf() },
            });
            const data = await res.json();
            if (data.success) {
                card.remove();
                this._updateVideoCount();
                this._showToast('ویدیو حذف شد.', 'success');
            } else {
                this._showToast(data.error || 'خطا در حذف', 'error');
            }
        } catch (err) {
            this._showToast('خطا در ارتباط با سرور', 'error');
        }
    },

    _updateVideoCount() {
        const list = document.getElementById('videosList');
        const count = list ? list.querySelectorAll('.video-card').length : 0;
        const el = document.getElementById('videoCount');
        if (el) el.textContent = `(${count} ویدیو)`;
    },

    _clearVideoForm() {
        const ids = ['newVideoTitle', 'newVideoUrl', 'newVideoDesc'];
        ids.forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
    },

    // ─────────────────────────────────────────────────────────────────
    //  UTILITIES
    // ─────────────────────────────────────────────────────────────────

    _getCsrf() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value
            || document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1]
            || '';
    },

    _showToast(msg, type = 'success') {
        const colors = { success: 'bg-green-600', error: 'bg-red-600', info: 'bg-blue-600' };
        const toast = document.createElement('div');
        toast.className = `fixed bottom-6 left-6 ${colors[type] || colors.info} text-white text-sm px-4 py-3 rounded-lg shadow-xl z-50 flex items-center gap-2`;
        toast.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>${this.escapeHtml(msg)}`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3500);
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};

window.MediaManager = MediaManager;