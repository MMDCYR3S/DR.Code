/**
 * EmergencyManager
 * مدیریت درخت تعیین تکلیف اورژانسی
 * ساختار: EmergencyDisposition → EmergencyNode (recursive)
 *
 * سبک کد: دقیقاً شبیه DynamicFieldManager
 */

const EmergencyManager = {
    counter: 0,
    orderId: null,
    syncUrl: null,
    colors: [],

    // ─────────────────────────────────────────────────────────────────
    //  INIT
    // ─────────────────────────────────────────────────────────────────

    init(config = {}) {
        this.orderId = config.orderId || null;
        this.syncUrl = config.syncUrl || null;
        this.colors  = config.colors  || [];

        this.attachEventListeners();
        console.log('✅ EmergencyManager initialized');
    },

    generateId() {
        return `tmp_node_${Date.now()}_${++this.counter}`;
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
        const marginClass = depth > 0 ? `mr-${Math.min(depth * 4, 16)}` : '';

        const html = `
        <div class="emergency-node bg-white border border-gray-200 rounded-xl shadow-sm ${marginClass}"
             data-node-id=""
             data-node-order="0">
            <div class="flex items-start gap-3 p-4 border-b border-gray-100">
                <div class="drag-handle-node text-gray-300 hover:text-orange-500 mt-1 cursor-grab">
                    <i class="fas fa-grip-vertical"></i>
                </div>
                <div class="flex-1 space-y-2">
                    <div class="flex items-center gap-2">
                        <i class="fas fa-circle ${dotColor} text-xs mt-0.5 shrink-0"></i>
                        <input type="text" dir="rtl" placeholder="عنوان گره..."
                               class="node-title flex-1 px-2 py-1 border border-gray-200 rounded-lg text-sm font-semibold text-gray-800 bg-gray-50 focus:bg-white focus:border-red-400 focus:outline-none transition">
                        <select class="node-color text-xs px-2 py-1 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:border-red-400 transition" dir="ltr">
                            <option value="">— رنگ —</option>
                            ${colorOptions}
                        </select>
                    </div>
                    <textarea dir="ltr" rows="2" placeholder="محتوا / متن گره..."
                              class="node-content w-full px-2 py-1.5 border border-gray-200 rounded-lg text-xs bg-gray-50 focus:bg-white focus:border-red-400 focus:outline-none transition resize-none"></textarea>
                    <input type="text" dir="rtl" placeholder="توضیحات داخلی (اختیاری)..."
                           class="node-notes w-full px-2 py-1 border border-gray-200 rounded-lg text-xs bg-gray-50 focus:bg-white focus:border-amber-400 focus:outline-none transition">
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

        if (isRoot) {
            const container = document.getElementById('emergencyNodesContainer');
            if (!container) return;
            container.insertAdjacentHTML('beforeend', html);
            container.lastElementChild.querySelector('.node-title')?.focus();
        } else {
            const childrenContainer = parentNodeEl.querySelector(':scope > .node-children');
            if (!childrenContainer) return;
            childrenContainer.classList.remove('hidden');
            childrenContainer.insertAdjacentHTML('beforeend', html);
            childrenContainer.lastElementChild.querySelector('.node-title')?.focus();
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
        nodeEl.remove();
        this._updateEmptyState();
    },

    // ─────────────────────────────────────────────────────────────────
    //  COLLECT PAYLOAD
    // ─────────────────────────────────────────────────────────────────

    collectPayload() {
        const container = document.getElementById('emergencyNodesContainer');
        if (!container) return { title: '', color: '', notes: '', nodes: [] };

        // فیلدهای Disposition
        const title = document.getElementById('emergencyTitle')?.value?.trim() || '';
        const color = document.getElementById('emergencyColor')?.value || '';
        const notes = document.getElementById('emergencyNotes')?.value?.trim() || '';

        // فقط گره‌های ریشه (مستقیم فرزند container)
        const rootNodes = [...container.querySelectorAll(':scope > .emergency-node')];
        const nodes = rootNodes.map((el, i) => this._collectNode(el, i));

        return { title, color, notes, nodes };
    },

    _collectNode(nodeEl, index) {
        const nodeId = nodeEl.dataset.nodeId ? parseInt(nodeEl.dataset.nodeId) : null;
        const title   = nodeEl.querySelector(':scope > div > .flex-1 .node-title')?.value?.trim() || '';
        const content = nodeEl.querySelector(':scope > div > .flex-1 .node-content')?.value?.trim() || '';
        const notes   = nodeEl.querySelector(':scope > div > .flex-1 .node-notes')?.value?.trim() || '';
        const color   = nodeEl.querySelector(':scope > div > .flex-1 .node-color')?.value || '';

        const childEls = [...(nodeEl.querySelector(':scope > .node-children')?.querySelectorAll(':scope > .emergency-node') || [])];
        const children = childEls.map((c, i) => this._collectNode(c, i));

        return {
            id: nodeId,
            title,
            content,
            internal_notes: notes,
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