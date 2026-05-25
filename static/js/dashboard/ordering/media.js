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
        this.orderId = config.orderId;
        this.bulkImageUrl = config.bulkImageUrl;
        this.addVideoUrl = config.addVideoUrl;
        this.updateImageUrlTemplate = config.updateImageUrl || `/dashboard/admin/media/image/<id>/update/`;
        this.deleteImageUrlTemplate = config.deleteImageUrl || `/dashboard/admin/media/image/<id>/delete/`;
        this.updateVideoUrlTemplate = config.updateVideoUrl || `/dashboard/admin/media/video/<id>/update/`;
        this.deleteVideoUrlTemplate = config.deleteVideoUrl || `/dashboard/admin/media/video/<id>/delete/`;

        this.attachEventListeners();
        this._initUploadZone();
        this._initSortable(); // مقداردهی Drag and Drop
    },

    // ─────────────────────────────────────────────────────────────────
    //  SORTABLE - Drag & Drop
    // ─────────────────────────────────────────────────────────────────
    _initSortable() {
        const imagesGrid = document.getElementById('imagesGrid');
        if (imagesGrid) {
            new Sortable(imagesGrid, {
                animation: 150,
                ghostClass: 'bg-gray-100',
                onEnd: () => this._syncImagesOrder()
            });
        }

        const videosList = document.getElementById('videosList');
        if (videosList) {
            new Sortable(videosList, {
                animation: 150,
                ghostClass: 'bg-gray-100',
                handle: '.video-drag-handle', // اختیاری: آیکون درگ برای ویدیوها
                onEnd: () => this._syncVideosOrder()
            });
        }
        
        // مرتب‌سازی بصری اولیه بدون ارسال ریکوئست
        this._updateBadgesAndInputs('imagesGrid', '.media-image-card');
        this._updateBadgesAndInputs('videosList', '.video-card');
    },

    _updateBadgesAndInputs(containerId, cardSelector) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.querySelectorAll(cardSelector).forEach((card, index) => {
            const badge = card.querySelector('.order-badge');
            if (badge) badge.textContent = index + 1; // نمایش ظاهری 1, 2, 3...
        });
    },

    // همگام‌سازی ترتیب تصاویر با سرور
    async _syncImagesOrder() {
        this._updateBadgesAndInputs('imagesGrid', '.media-image-card');
        const cards = document.querySelectorAll('#imagesGrid .media-image-card');
        
        // اجرای موازی درخواست‌های آپدیت برای هر تصویر
        const promises = Array.from(cards).map((card, index) => {
            const imageId = card.dataset.imageId;
            const url = this.updateImageUrlTemplate.replace('<id>', imageId);
            return fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrf() },
                body: JSON.stringify({ order_index: index })
            });
        });
        
        await Promise.all(promises);
        this._showToast('ترتیب تصاویر بروزرسانی شد.', 'success');
    },

    // همگام‌سازی ترتیب ویدیوها با سرور
    async _syncVideosOrder() {
        this._updateBadgesAndInputs('videosList', '.video-card');
        const cards = document.querySelectorAll('#videosList .video-card');
        
        const promises = Array.from(cards).map((card, index) => {
            const videoId = card.dataset.videoId;
            const url = this.updateVideoUrlTemplate.replace('<id>', videoId);
            return fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrf() },
                body: JSON.stringify({ order_index: index })
            });
        });
        
        await Promise.all(promises);
        this._showToast('ترتیب ویدیوها بروزرسانی شد.', 'success');
    },

    // ─────────────────────────────────────────────────────────────────
    //  SORT INDEX — شماره‌گذاری اولیه کارت‌های server-rendered
    // ─────────────────────────────────────────────────────────────────

    _initSortIndexes() {
        // تصاویر: مقدار order_index رو از data-order-index بخون
        // (در تمپلیت ست میشه)
        document.querySelectorAll('.media-image-card').forEach(card => {
            const input = card.querySelector('.image-order-index');
            const badge = card.querySelector('.order-badge');
            if (input && badge) badge.textContent = input.value;
        });

        // ویدیوها: همین کار
        document.querySelectorAll('.video-card').forEach(card => {
            const input = card.querySelector('.video-order-index');
            const badge = card.querySelector('.order-badge');
            if (input && badge) badge.textContent = input.value;
        });
    },

    // ─────────────────────────────────────────────────────────────────
    //  EVENT LISTENERS
    // ─────────────────────────────────────────────────────────────────

    attachEventListeners() {
        document.getElementById('imageUploadInput')?.addEventListener('change', (e) => {
            const files = [...e.target.files];
            if (files.length) this._uploadImages(files);
            e.target.value = '';
        });

        document.getElementById('addVideoBtn')?.addEventListener('click', () => {
            const form = document.getElementById('addVideoForm');
            if (form) {
                form.classList.toggle('hidden');
                if (!form.classList.contains('hidden')) {
                    // پیش‌پر کردن order_index با مقدار بعدی
                    const nextIdx = this._nextVideoIndex();
                    const idxInput = document.getElementById('newVideoOrderIndex');
                    if (idxInput) idxInput.value = nextIdx;
                    document.getElementById('newVideoUrl')?.focus();
                }
            }
        });

        document.getElementById('confirmAddVideoBtn')?.addEventListener('click', () => {
            this._addVideo();
        });

        document.getElementById('cancelAddVideoBtn')?.addEventListener('click', () => {
            document.getElementById('addVideoForm')?.classList.add('hidden');
            this._clearVideoForm();
        });

        // Event delegation
        document.addEventListener('click', (e) => {
            if (e.target.closest('.save-image-btn')) {
                const card = e.target.closest('.media-image-card');
                if (card) this._saveImage(card);
                return;
            }
            if (e.target.closest('.delete-image-btn')) {
                const card = e.target.closest('.media-image-card');
                if (card) this._deleteImage(card);
                return;
            }
            if (e.target.closest('.save-video-btn')) {
                const card = e.target.closest('.video-card');
                if (card) this._saveVideo(card);
                return;
            }
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
        zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const files = [...e.dataTransfer.files].filter(f => f.type.startsWith('image/'));
            if (files.length) this._uploadImages(files);
        });
    },

    // ─────────────────────────────────────────────────────────────────
    //  IMAGE — آپلود
    // ─────────────────────────────────────────────────────────────────

    async _uploadImages(files) {
        if (!this.bulkImageUrl) return;

        const progressEl   = document.getElementById('uploadProgress');
        const progressText = document.getElementById('uploadProgressText');

        if (progressEl)   progressEl.classList.remove('hidden');
        if (progressText) progressText.textContent = `در حال آپلود ${files.length} تصویر...`;

        const formData = new FormData();
        files.forEach(f => formData.append('images', f));

        // order_index شروع از بعد از آخرین تصویر موجود
        const startIndex = this._nextImageIndex();
        formData.append('start_order_index', startIndex);

        try {
            const res  = await fetch(this.bulkImageUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': this._getCsrf() },
                body: formData,
            });
            const data = await res.json();
            if (data.success && data.images) {
                document.getElementById('imagesEmptyState')?.remove();
                data.images.forEach(img => this._appendImageCard(img));
                this._updateImageCount();
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

    _nextImageIndex() {
        const cards = document.querySelectorAll('#imagesGrid .media-image-card');
        let max = 0;
        cards.forEach(card => {
            const v = parseInt(card.querySelector('.image-order-index')?.value || '0', 10);
            if (v > max) max = v;
        });
        return max + 1;
    },

    _nextVideoIndex() {
        const cards = document.querySelectorAll('#videosList .video-card');
        let max = 0;
        cards.forEach(card => {
            const v = parseInt(card.querySelector('.video-order-index')?.value || '0', 10);
            if (v > max) max = v;
        });
        return max + 1;
    },

    _appendImageCard(img) {
        const grid = document.getElementById('imagesGrid');
        if (!grid) return;

        const html = `
            <div class="media-image-card relative rounded-xl overflow-hidden border border-gray-200 shadow-sm bg-white cursor-move"
                 data-image-id="${img.id}">
                <div class="aspect-square bg-gray-100">
                    <img src="${this.escapeHtml(img.url)}" alt="${this.escapeHtml(img.caption || '')}" class="w-full h-full object-cover pointer-events-none">
                </div>
                <div class="p-2 space-y-1.5">
                    <input type="text" dir="rtl" value="${this.escapeHtml(img.caption || '')}" placeholder="کپشن..."
                           class="image-caption w-full text-xs px-2 py-1 border border-gray-200 rounded focus:border-purple-400 focus:outline-none bg-gray-50">
                </div>
                <div class="flex gap-1 px-2 pb-2">
                    <button type="button" class="save-image-btn flex-1 bg-green-500 text-white py-1 rounded-lg text-xs hover:bg-green-600 transition shadow flex items-center justify-center gap-1">
                        <i class="fas fa-check"></i>ذخیره
                    </button>
                    <button type="button" class="delete-image-btn bg-red-500 text-white px-2 py-1 rounded-lg text-xs hover:bg-red-600 transition shadow">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="order-badge absolute top-2 right-2 bg-black bg-opacity-60 text-white text-xs px-1.5 py-0.5 rounded font-mono">
                    -
                </div>
            </div>`;
        grid.insertAdjacentHTML('beforeend', html);
        this._updateBadgesAndInputs('imagesGrid', '.media-image-card');
    },

    // ─────────────────────────────────────────────────────────────────
    //  IMAGE — ذخیره (caption + order_index با هم)
    // ─────────────────────────────────────────────────────────────────

    async _saveImage(card) {
        const imageId    = card.dataset.imageId;
        const caption    = card.querySelector('.image-caption')?.value?.trim() || '';
        const orderIndex = parseInt(card.querySelector('.image-order-index')?.value || '0', 10);
        const url        = this.updateImageUrlTemplate.replace('<id>', imageId);

        try {
            const res  = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrf() },
                body: JSON.stringify({ caption, order_index: orderIndex }),
            });
            const data = await res.json();
            if (data.success) {
                // badge رو آپدیت کن
                const badge = card.querySelector('.order-badge');
                if (badge) badge.textContent = data.order_index ?? orderIndex;
                this._showToast('تصویر ذخیره شد.', 'success');
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
        const url     = this.deleteImageUrlTemplate.replace('<id>', imageId);

        try {
            const res  = await fetch(url, {
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
        const grid  = document.getElementById('imagesGrid');
        const count = grid ? grid.querySelectorAll('.media-image-card').length : 0;
        const el    = document.getElementById('imageCount');
        if (el) el.textContent = `(${count} تصویر)`;
    },

    // ─────────────────────────────────────────────────────────────────
    //  VIDEO — افزودن / ذخیره / حذف
    // ─────────────────────────────────────────────────────────────────

    async _addVideo() {
        const url        = document.getElementById('newVideoUrl')?.value?.trim();
        const title      = document.getElementById('newVideoTitle')?.value?.trim() || '';
        const desc       = document.getElementById('newVideoDesc')?.value?.trim() || '';
        const orderIndex = parseInt(document.getElementById('newVideoOrderIndex')?.value || '0', 10);

        if (!url) {
            document.getElementById('newVideoUrl')?.focus();
            this._showToast('لینک ویدیو اجباری است.', 'error');
            return;
        }
        if (!this.addVideoUrl) return;

        try {
            const res  = await fetch(this.addVideoUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrf() },
                body: JSON.stringify({ video_url: url, title, description: desc, order_index: orderIndex }),
            });
            const data = await res.json();
            if (data.success && data.video) {
                document.getElementById('videosEmptyState')?.remove();
                this._appendVideoCard(data.video);
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
            <div class="video-card bg-gray-50 border border-gray-200 rounded-xl p-4 cursor-move"
                 data-video-id="${video.id}">
                <div class="flex items-start gap-3">
                    <div class="video-drag-handle w-10 h-10 bg-pink-100 rounded-lg flex items-center justify-center shrink-0 cursor-move">
                        <i class="fas fa-grip-vertical text-pink-500"></i>
                    </div>
                    <div class="flex-1 space-y-2 min-w-0">
                        <input type="text" dir="rtl" value="${this.escapeHtml(video.title || '')}" placeholder="عنوان ویدیو..."
                               class="video-title w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm bg-white focus:border-pink-400 focus:outline-none transition">
                        <input type="url" dir="ltr" value="${this.escapeHtml(video.video_url)}" placeholder="لینک embed..."
                               class="video-url w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm bg-white focus:border-pink-400 focus:outline-none transition">
                    </div>
                    <div class="order-badge bg-black bg-opacity-10 text-gray-700 text-xs px-2 py-1 rounded font-mono shrink-0">
                        -
                    </div>
                    <div class="flex flex-col gap-1 shrink-0 ml-2">
                        <button type="button" class="save-video-btn text-xs px-2.5 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition font-medium whitespace-nowrap">
                            <i class="fas fa-save ml-1"></i>ذخیره
                        </button>
                        <button type="button" class="delete-video-btn text-red-400 hover:text-red-600 p-1.5 rounded hover:bg-red-50 transition text-center">
                            <i class="fas fa-trash text-sm"></i>
                        </button>
                    </div>
                </div>
            </div>`;
        list.insertAdjacentHTML('beforeend', html);
        this._updateBadgesAndInputs('videosList', '.video-card');
    },

    async _saveVideo(card) {
        const videoId    = card.dataset.videoId;
        const title      = card.querySelector('.video-title')?.value?.trim() || '';
        const video_url  = card.querySelector('.video-url')?.value?.trim() || '';
        const description = card.querySelector('.video-description')?.value?.trim() || '';
        const orderIndex = parseInt(card.querySelector('.video-order-index')?.value || '0', 10);
        const url        = this.updateVideoUrlTemplate.replace('<id>', videoId);

        try {
            const res  = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this._getCsrf() },
                body: JSON.stringify({ title, video_url, description, order_index: orderIndex }),
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
        const url     = this.deleteVideoUrlTemplate.replace('<id>', videoId);

        try {
            const res  = await fetch(url, {
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
        const list  = document.getElementById('videosList');
        const count = list ? list.querySelectorAll('.video-card').length : 0;
        const el    = document.getElementById('videoCount');
        if (el) el.textContent = `(${count} ویدیو)`;
    },

    _clearVideoForm() {
        ['newVideoTitle', 'newVideoUrl', 'newVideoDesc', 'newVideoOrderIndex'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
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
        const toast  = document.createElement('div');
        toast.className = `fixed bottom-6 left-6 ${colors[type] || colors.info} text-white text-sm
                           px-4 py-3 rounded-lg shadow-xl z-50 flex items-center gap-2`;
        toast.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                           ${this.escapeHtml(msg)}`;
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
