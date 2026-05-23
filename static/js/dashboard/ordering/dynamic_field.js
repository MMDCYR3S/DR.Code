/**
 * DynamicFieldManager
 * مدیریت گروه‌های پویا (پیش‌بالینی): Group → SubGroup → Item (KEY-VALUE)
 * 
 * سبک کد: دقیقاً شبیه SectionItemManager
 */

const DynamicFieldManager = {
    counter: 0,
    orderId: null,
    syncUrl: null,
    colors: [],
    groupsSortable: null,

    // ─────────────────────────────────────────────────────────────────
    //  INIT
    // ─────────────────────────────────────────────────────────────────

    init(config = {}) {
        this.orderId  = config.orderId  || null;
        this.syncUrl  = config.syncUrl  || null;
        this.colors   = config.colors   || [];

        this.attachEventListeners();
        this.initGroupsSortable();
        console.log('✅ DynamicFieldManager initialized');
    },

    generateId() {
        return `tmp_${Date.now()}_${++this.counter}`;
    },

    // ─────────────────────────────────────────────────────────────────
    //  SORTABLE
    // ─────────────────────────────────────────────────────────────────

    initGroupsSortable() {
        const container = document.getElementById('dynamicGroupsContainer');
        if (!container || typeof Sortable === 'undefined') return;
        if (this.groupsSortable) this.groupsSortable.destroy();
        this.groupsSortable = Sortable.create(container, {
            animation: 150,
            handle: '.drag-handle-group',
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
        });
    },

    // ─────────────────────────────────────────────────────────────────
    //  EVENT LISTENERS
    // ─────────────────────────────────────────────────────────────────

    attachEventListeners() {
        document.addEventListener('click', (e) => {
            // افزودن گروه
            if (e.target.closest('#addGroupBtn') || e.target.closest('#addFirstGroupBtn')) {
                e.preventDefault();
                this.addGroup();
            }
            // حذف گروه
            if (e.target.closest('.delete-group-btn')) {
                e.preventDefault();
                this.handleDeleteGroup(e.target.closest('.dynamic-group'));
            }
            // افزودن زیرگروه
            if (e.target.closest('.add-subgroup-btn')) {
                e.preventDefault();
                this.addSubgroup(e.target.closest('.dynamic-group'));
            }
            // حذف زیرگروه
            if (e.target.closest('.delete-subgroup-btn')) {
                e.preventDefault();
                this.handleDeleteSubgroup(e.target.closest('.subgroup-block'));
            }
            // افزودن آیتم
            if (e.target.closest('.add-item-btn')) {
                e.preventDefault();
                this.addItem(e.target.closest('.subgroup-block'));
            }
            // حذف آیتم
            if (e.target.closest('.delete-item-btn')) {
                e.preventDefault();
                this.handleDeleteItem(e.target.closest('.item-kv'));
            }
            // ذخیره یکجا
            if (e.target.closest('#dynamicSaveBtn')) {
                e.preventDefault();
                this.syncAll();
            }
        });
    },

    // ─────────────────────────────────────────────────────────────────
    //  ADD GROUP
    // ─────────────────────────────────────────────────────────────────

    addGroup() {
        const container = document.getElementById('dynamicGroupsContainer');
        if (!container) return;

        // حذف empty state
        container.querySelector('#dynamicEmptyState')?.remove();

        const colorOptions = this.colors.map(([val, label]) =>
            `<option value="${val}">${this.escapeHtml(label)}</option>`
        ).join('');

        const html = `
        <div class="dynamic-group bg-white border border-gray-200 rounded-xl shadow-sm"
             data-group-id="">
            <div class="flex items-center gap-3 p-4 border-b border-gray-100">
                <div class="drag-handle-group text-gray-300 hover:text-blue-500 cursor-grab">
                    <i class="fas fa-grip-vertical"></i>
                </div>
                <div class="flex-1">
                    <input type="text" dir="rtl" placeholder="عنوان گروه..."
                           class="group-title w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm font-semibold text-gray-800 bg-gray-50 focus:bg-white focus:border-blue-400 focus:outline-none transition">
                </div>
                <select class="group-color text-xs px-2 py-1.5 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:border-blue-400 transition" dir="ltr">
                    <option value="">— رنگ —</option>
                    ${colorOptions}
                </select>
                <button type="button" class="add-subgroup-btn text-xs px-2.5 py-1 bg-teal-600 text-white rounded hover:bg-teal-700 transition font-medium">
                    <i class="fas fa-plus ml-1"></i>زیرگروه
                </button>
                <button type="button" class="delete-group-btn text-red-400 hover:text-red-600 p-1.5 rounded hover:bg-red-50 transition">
                    <i class="fas fa-trash text-sm"></i>
                </button>
            </div>
            <div class="subgroups-list p-4 space-y-4">
                <div class="empty-subgroups text-center text-gray-400 text-xs py-4">زیرگروهی اضافه نشده</div>
            </div>
        </div>`;

        container.insertAdjacentHTML('beforeend', html);
        container.lastElementChild.querySelector('.group-title')?.focus();
        this.initGroupsSortable();
    },

    // ─────────────────────────────────────────────────────────────────
    //  ADD SUBGROUP
    // ─────────────────────────────────────────────────────────────────

    addSubgroup(groupEl) {
        if (!groupEl) return;
        const list = groupEl.querySelector('.subgroups-list');
        if (!list) return;
        list.querySelector('.empty-subgroups')?.remove();

        const html = `
        <div class="subgroup-block" data-subgroup-id="">
            <div class="flex items-center gap-2 mb-3">
                <i class="fas fa-folder-open text-amber-500 text-sm"></i>
                <input type="text" dir="rtl" placeholder="عنوان زیرگروه..."
                       class="subgroup-title flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 bg-gray-50 focus:bg-white focus:border-teal-400 focus:outline-none transition">
                <button type="button" class="add-item-btn text-xs px-2 py-1 bg-amber-500 text-white rounded hover:bg-amber-600 transition font-medium">
                    <i class="fas fa-plus ml-1"></i>آیتم
                </button>
                <button type="button" class="delete-subgroup-btn text-red-400 hover:text-red-600 p-1 rounded hover:bg-red-50 transition">
                    <i class="fas fa-times text-sm"></i>
                </button>
            </div>
            <div class="items-list space-y-2 mr-6">
                <div class="empty-items text-center text-gray-400 text-xs py-3">آیتمی اضافه نشده</div>
            </div>
        </div>`;

        list.insertAdjacentHTML('beforeend', html);
        list.lastElementChild.querySelector('.subgroup-title')?.focus();
    },

    // ─────────────────────────────────────────────────────────────────
    //  ADD ITEM (KEY-VALUE)
    // ─────────────────────────────────────────────────────────────────

    addItem(subgroupEl) {
        if (!subgroupEl) return;
        const list = subgroupEl.querySelector('.items-list');
        if (!list) return;
        list.querySelector('.empty-items')?.remove();

        const html = `
        <div class="item-kv flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg p-2"
             data-item-id="">
            <input type="text" dir="ltr" placeholder="کلید (key)..."
                   class="item-key w-1/3 px-2 py-1 border border-gray-200 rounded text-xs bg-white focus:border-blue-400 focus:outline-none transition">
            <span class="text-gray-400 text-xs">:</span>
            <textarea dir="ltr" rows="1"
                      placeholder="مقدار (value)..."
                      class="item-value flex-1 px-2 py-1 border border-gray-200 rounded text-xs bg-white focus:border-blue-400 focus:outline-none transition resize-none"></textarea>
            <button type="button" class="delete-item-btn text-red-400 hover:text-red-600 p-1 rounded hover:bg-red-50 transition shrink-0">
                <i class="fas fa-trash text-xs"></i>
            </button>
        </div>`;

        list.insertAdjacentHTML('beforeend', html);
        list.lastElementChild.querySelector('.item-key')?.focus();
    },

    // ─────────────────────────────────────────────────────────────────
    //  DELETE HANDLERS
    // ─────────────────────────────────────────────────────────────────

    handleDeleteGroup(groupEl) {
        if (!groupEl) return;
        if (!confirm('آیا از حذف این گروه و تمام زیرمجموعه‌هایش اطمینان دارید؟')) return;
        groupEl.remove();
    },

    handleDeleteSubgroup(subgroupEl) {
        if (!subgroupEl) return;
        if (!confirm('آیا از حذف این زیرگروه اطمینان دارید؟')) return;
        subgroupEl.remove();
    },

    handleDeleteItem(itemEl) {
        if (!itemEl) return;
        itemEl.remove();
    },

    // ─────────────────────────────────────────────────────────────────
    //  COLLECT PAYLOAD
    // ─────────────────────────────────────────────────────────────────

    collectPayload() {
        const groups = [];
        document.querySelectorAll('#dynamicGroupsContainer .dynamic-group').forEach((groupEl, gi) => {
            const groupId = groupEl.dataset.groupId ? parseInt(groupEl.dataset.groupId) : null;
            const title   = groupEl.querySelector('.group-title')?.value?.trim() || '';
            const color   = groupEl.querySelector('.group-color')?.value || '';
            if (!title) return;

            const subgroups = [];
            groupEl.querySelectorAll('.subgroup-block').forEach((sgEl, si) => {
                const sgId    = sgEl.dataset.subgroupId ? parseInt(sgEl.dataset.subgroupId) : null;
                const sgTitle = sgEl.querySelector('.subgroup-title')?.value?.trim() || '';
                if (!sgTitle) return;

                const items = [];
                sgEl.querySelectorAll('.item-kv').forEach((itemEl, ii) => {
                    const itemId = itemEl.dataset.itemId ? parseInt(itemEl.dataset.itemId) : null;
                    const key    = itemEl.querySelector('.item-key')?.value?.trim() || '';
                    const value  = itemEl.querySelector('.item-value')?.value?.trim() || '';
                    if (!key) return;
                    items.push({ id: itemId, key, value, order_index: ii });
                });

                subgroups.push({ id: sgId, title: sgTitle, order_index: si, items });
            });

            groups.push({ id: groupId, title, color, order_index: gi, subgroups });
        });
        return groups;
    },

    // ─────────────────────────────────────────────────────────────────
    //  SYNC — ذخیره یکجا
    // ─────────────────────────────────────────────────────────────────

    async syncAll() {
        if (!this.syncUrl) return;

        const btn = document.getElementById('dynamicSaveBtn');
        const groups = this.collectPayload();

        this._setLoading(btn, true);
        try {
            const res = await fetch(this.syncUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this._getCsrf(),
                },
                body: JSON.stringify({ groups }),
            });
            const data = await res.json();
            if (data.success) {
                this._showToast('فیلدهای پویا ذخیره شدند.', 'success');
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
        const colors = {
            success: 'bg-green-600',
            error:   'bg-red-600',
            info:    'bg-blue-600',
        };
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

window.DynamicFieldManager = DynamicFieldManager;