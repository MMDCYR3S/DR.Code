/**
 * EmergencyManager
 * مدیریت درخت تعیین تکلیف اورژانسی
 * ساختار: EmergencyDisposition → EmergencyNode (recursive)
 *
 * محتوای هر گره از طریق CKEditor 5 (django-ckeditor-5) ویرایش می‌شود.
 * هر بار که گره جدیدی اضافه می‌شود، ادیتور روی textarea آن mount می‌شود.
 */

const EmergencyManager = {
    counter: 0,
    orderId: null,
    syncUrl: null,
    colors: [],

    // نگهداری نگاشت nodeEl → editor instance
    _editors: new WeakMap(),

    // ─────────────────────────────────────────────────────────────────
    //  INIT
    // ─────────────────────────────────────────────────────────────────

    init(config = {}) {
        this.orderId = config.orderId || null;
        this.syncUrl = config.syncUrl || null;
        this.colors  = config.colors  || [];

        // اگر django-ckeditor-5 هنوز در حال init هست، کمی صبر کن
        const initNodes = () => {
            document.querySelectorAll('.emergency-node').forEach(nodeEl => {
                this._mountEditor(nodeEl);
            });
        };

        if (document.readyState === 'complete') {
            initNodes();
        } else {
            window.addEventListener('load', initNodes);
        }

        this.attachEventListeners();
        console.log('✅ EmergencyManager initialized');
    },


    generateId() {
        return `tmp_node_${Date.now()}_${++this.counter}`;
    },

    // ─────────────────────────────────────────────────────────────────
    //  CKEDITOR HELPERS
    // ─────────────────────────────────────────────────────────────────

    _mountEditor(nodeEl) {
        const textarea = nodeEl.querySelector(':scope > div > .flex-1 .node-content');
        if (!textarea || textarea.dataset.editorMounted) return;

        textarea.dataset.editorMounted = '1';

        const EditorClass = window.ClassicEditor;
        if (!EditorClass) {
            console.warn('EmergencyManager: ClassicEditor not found.');
            return;
        }

        EditorClass.create(textarea, {
            licenseKey: 'GPL',
            language: 'fa',
            toolbar: {
                items: [
                    'heading', '|',
                    'bold', 'italic', 'underline', 'strikethrough', '|',
                    'alignment',                    // ← align
                    '|',
                    'bulletedList', 'numberedList', '|',
                    'outdent', 'indent', '|',
                    'blockQuote', 'link', '|',
                    'insertTable', '|',
                    'undo', 'redo',
                ],
            },
            alignment: {
                options: ['left', 'right', 'center', 'justify'],
            },
        })

        .then(editor => {
            this._editors.set(textarea, editor);
            editor.model.document.on('change:data', () => {
                textarea.value = editor.getData();
            });
        })
        .catch(err => console.error('CKEditor5 mount error:', err));
    },



    /**
     * گرفتن محتوای HTML از ادیتور یا مستقیم از textarea (fallback).
     */
    _getEditorData(nodeEl) {
        const textarea = nodeEl.querySelector(':scope > div > .flex-1 .node-content');
        if (!textarea) return '';
        const editor = this._editors.get(textarea);
        if (editor) return editor.getData();
        return textarea.value || '';
    },

    /**
     * destroy کردن ادیتور قبل از حذف گره — جلوگیری از memory leak.
     */
    _destroyEditor(nodeEl) {
        const textarea = nodeEl.querySelector(':scope > div > .flex-1 .node-content');
        if (!textarea) return;
        const editor = this._editors.get(textarea);
        if (editor) {
            editor.destroy().catch(() => {});
            this._editors.delete(textarea);
        }
        // فرزندان را هم destroy کن
        nodeEl.querySelectorAll('.node-content').forEach(ta => {
            const ed = this._editors.get(ta);
            if (ed) {
                ed.destroy().catch(() => {});
                this._editors.delete(ta);
            }
        });
    },

    _waitForCKEditorInit(textarea) {
        let attempts = 0;
        const interval = setInterval(() => {
            attempts++;
            // django-ckeditor-5 معمولاً instance رو روی textarea.ckeditorInstance می‌ذاره
            const editor = textarea.ckeditorInstance
                || (window.CKEDITOR_5_INSTANCES && [...window.CKEDITOR_5_INSTANCES.values()]
                    .find(ed => ed.sourceElement === textarea));

            if (editor) {
                clearInterval(interval);
                textarea.dataset.editorMounted = '1';
                this._editors.set(textarea, editor);
                editor.model.document.on('change:data', () => {
                    textarea.value = editor.getData();
                });
            } else if (attempts > 50) { // 5 ثانیه timeout
                clearInterval(interval);
                console.warn('CKEditor init timeout for', textarea.id);
            }
        }, 100);
    },

    // ─────────────────────────────────────────────────────────────────
    //  EVENT LISTENERS
    // ─────────────────────────────────────────────────────────────────

    attachEventListeners() {
        document.addEventListener('click', (e) => {
            // افزودن گره ریشه
            if (e.target.closest('#addRootNodeBtn') || e.target.closest('#addFirstNodeBtn')) {
                e.preventDefault();
                this.addNode(null);
                return;
            }
            // افزودن زیرگره
            if (e.target.closest('.add-child-node-btn')) {
                e.preventDefault();
                const parentNode = e.target.closest('.emergency-node');
                this.addNode(parentNode);
                return;
            }
            // حذف گره
            if (e.target.closest('.delete-node-btn')) {
                e.preventDefault();
                this.handleDeleteNode(e.target.closest('.emergency-node'));
                return;
            }
            // ذخیره یکجا
            if (e.target.closest('#emergencySaveBtn')) {
                e.preventDefault();
                this.syncAll();
                return;
            }
        });
    },

    // ─────────────────────────────────────────────────────────────────
    //  ADD NODE
    // ─────────────────────────────────────────────────────────────────

    addNode(parentNodeEl) {
        // حذف empty state
        document.getElementById('emergencyEmptyState')?.remove();

        const colorOptions = this.colors.map(([val, label]) =>
            `<option value="${val}">${this.escapeHtml(label)}</option>`
        ).join('');

        const isRoot = !parentNodeEl;
        const depth = isRoot ? 0 : this._getDepth(parentNodeEl) + 1;

        const dotColor = depth === 0 ? 'text-red-400' : depth === 1 ? 'text-orange-400' : 'text-amber-400';
        const marginStyle = depth > 0 ? `style="margin-right:${depth}rem"` : '';

        // شناسه یکتا برای textarea تا CKEditor بتواند mount کند
        const uid = this.generateId();

        const html = `
        <div class="emergency-node bg-white border border-gray-200 rounded-xl shadow-sm" ${marginStyle}
             data-node-id=""
             data-node-order="0">
            <div class="flex items-start gap-3 p-4 border-b border-gray-100">
                <div class="drag-handle-node text-gray-300 hover:text-orange-500 mt-1 cursor-grab">
                    <i class="fas fa-grip-vertical"></i>
                </div>
                <div class="flex-1 space-y-3">
                    <div class="flex items-center gap-2">
                        <i class="fas fa-circle ${dotColor} text-xs mt-0.5 shrink-0"></i>
                        <input type="text" dir="rtl" placeholder="عنوان گره..."
                               class="node-title flex-1 px-2 py-1 border border-gray-200 rounded-lg text-sm font-semibold text-gray-800 bg-gray-50 focus:bg-white focus:border-red-400 focus:outline-none transition">
                        <select class="node-color text-xs px-2 py-1 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:border-red-400 transition" dir="ltr">
                            <option value="">— رنگ —</option>
                            ${colorOptions}
                        </select>
                    </div>
                    <div class="node-content-wrapper">
                        <label class="block text-xs text-gray-400 mb-1">محتوا</label>
                        <textarea class="node-content"
                                  id="node_content_${uid}"
                                  dir="rtl"></textarea>
                    </div>
                </div>
                <div class="flex flex-col gap-1 shrink-0">
                    <button type="button" class="add-child-node-btn text-xs px-2 py-1 bg-orange-500 text-white rounded hover:bg-orange-600 transition font-medium whitespace-nowrap">
                        <i class="fas fa-plus ml-1"></i>زیرگره
                    </button>
                    <button type="button" class="delete-node-btn text-red-400 hover:text-red-600 p-1 rounded hover:bg-red-50 transition text-center">
                        <i class="fas fa-trash text-sm"></i>
                    </button>
                </div>
            </div>
            <div class="node-children p-3 space-y-2 hidden"></div>
        </div>`;

        let newNodeEl;

        if (isRoot) {
            const container = document.getElementById('emergencyNodesContainer');
            if (!container) return;
            container.insertAdjacentHTML('beforeend', html);
            newNodeEl = container.lastElementChild;
            newNodeEl.querySelector('.node-title')?.focus();
        } else {
            const childrenContainer = parentNodeEl.querySelector(':scope > .node-children');
            if (!childrenContainer) return;
            childrenContainer.classList.remove('hidden');
            childrenContainer.insertAdjacentHTML('beforeend', html);
            newNodeEl = childrenContainer.lastElementChild;
            newNodeEl.querySelector('.node-title')?.focus();
        }

        // mount ادیتور روی گره جدید
        if (newNodeEl) {
            this._mountEditor(newNodeEl);
        }
    },

    // ─────────────────────────────────────────────────────────────────
    //  DELETE NODE
    // ─────────────────────────────────────────────────────────────────

    handleDeleteNode(nodeEl) {
        if (!nodeEl) return;
        const hasChildren = nodeEl.querySelector('.emergency-node');
        const msg = hasChildren
            ? 'آیا از حذف این گره و تمام زیرگره‌هایش اطمینان دارید؟'
            : 'آیا از حذف این گره اطمینان دارید؟';
        if (!confirm(msg)) return;

        // destroy تمام ادیتورهای داخل این گره قبل از حذف DOM
        this._destroyEditor(nodeEl);
        nodeEl.remove();
        this._updateEmptyState();
    },

    // ─────────────────────────────────────────────────────────────────
    //  COLLECT PAYLOAD
    // ─────────────────────────────────────────────────────────────────

    collectPayload() {
        const container = document.getElementById('emergencyNodesContainer');
        if (!container) return { title: '', color: '', notes: '', nodes: [] };

        const title = document.getElementById('emergencyTitle')?.value?.trim() || '';
        const color = document.getElementById('emergencyColor')?.value || '';
        const notes = document.getElementById('emergencyNotes')?.value?.trim() || '';

        const rootNodes = [...container.querySelectorAll(':scope > .emergency-node')];
        const nodes = rootNodes.map((el, i) => this._collectNode(el, i));

        return { title, color, notes, nodes };
    },

    _collectNode(nodeEl, index) {
        const nodeId = nodeEl.dataset.nodeId ? parseInt(nodeEl.dataset.nodeId) : null;
        const title   = nodeEl.querySelector(':scope > div > .flex-1 .node-title')?.value?.trim() || '';
        const color   = nodeEl.querySelector(':scope > div > .flex-1 .node-color')?.value || '';

        // محتوا از CKEditor یا مستقیم از textarea
        const content = this._getEditorData(nodeEl);

        const childEls = [...(nodeEl.querySelector(':scope > .node-children')?.querySelectorAll(':scope > .emergency-node') || [])];
        const children = childEls.map((c, i) => this._collectNode(c, i));

        return {
            id: nodeId,
            title,
            content,
            color,
            order_index: index,
            children,
        };
    },

    // ─────────────────────────────────────────────────────────────────
    //  SYNC — ذخیره یکجا
    // ─────────────────────────────────────────────────────────────────

    async syncAll() {
        if (!this.syncUrl) return;

        const btn = document.getElementById('emergencySaveBtn');
        const payload = this.collectPayload();

        this._setLoading(btn, true);
        try {
            const res = await fetch(this.syncUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this._getCsrf(),
                },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            if (data.success) {
                this._showToast('تعیین تکلیف ذخیره شد.', 'success');
            } else {
                this._showToast(data.error || 'خطا در ذخیره', 'error');
            }
        } catch (err) {
            console.error(err);
            this._showToast('خطا در ارتباط با سرور', 'error');
        } finally {
            this._setLoading(btn, false);
        }
    },

    // ─────────────────────────────────────────────────────────────────
    //  UTILITIES
    // ─────────────────────────────────────────────────────────────────

    _getDepth(nodeEl) {
        let depth = 0;
        let el = nodeEl.parentElement;
        while (el) {
            if (el.classList.contains('emergency-node')) depth++;
            el = el.parentElement;
        }
        return depth;
    },

    _updateEmptyState() {
        const container = document.getElementById('emergencyNodesContainer');
        if (!container) return;
        if (!container.querySelector('.emergency-node')) {
            if (!document.getElementById('emergencyEmptyState')) {
                container.insertAdjacentHTML('beforeend', `
                    <div id="emergencyEmptyState" class="text-center py-14">
                        <div class="w-fit mx-auto bg-red-50 rounded-full p-5 mb-4">
                            <i class="fas fa-project-diagram text-4xl text-red-300"></i>
                        </div>
                        <h3 class="text-base font-semibold text-gray-600 mb-2">گره‌ای تعریف نشده</h3>
                        <p class="text-sm text-gray-400 mb-4">اولین گره تعیین تکلیف را ایجاد کنید.</p>
                        <button type="button" id="addFirstNodeBtn"
                                class="px-5 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-semibold text-sm">
                            <i class="fas fa-plus ml-1"></i>افزودن اولین گره
                        </button>
                    </div>`);
            }
        }
    },

    _getCsrf() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value
            || document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1]
            || '';
    },

    _setLoading(btn, loading) {
        if (!btn) return;
        btn.disabled = loading;
        if (loading) {
            btn._original = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin ml-1"></i>در حال ذخیره...';
        } else {
            btn.innerHTML = btn._original || '<i class="fas fa-cloud-upload-alt ml-1"></i>ذخیره یکجا';
        }
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

window.EmergencyManager = EmergencyManager;