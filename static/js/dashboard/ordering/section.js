/**
 * SectionManager
 * مدیریت Section ها با Drag & Drop، Inline Edit و Bulk Sync
 *
 * جریان ایجاد:
 *   1. کاربر فرم Order را submit می‌کند (JSON fetch).
 *   2. سرور order_id برمی‌گرداند.
 *   3. صفحه بلافاصله panel مدیریت Section را باز می‌کند.
 *   4. کاربر Section ها را می‌سازد.
 *   5. دکمه «ذخیره یکجا» همه را به /orders/<id>/sections/sync/ ارسال می‌کند.
 */

const SectionManager = {
    orderId: null,
    syncUrl: null,
    createOrderUrl: null,
    csrfToken: null,
    sectionCounter: 0,
    tempIdCounter: 0,
    _sortable: null,

    TAILWIND_COLORS: [
        { value: 'slate', label: 'اسلیت' }, { value: 'gray', label: 'خاکستری' },
        { value: 'zinc', label: 'زینک' }, { value: 'neutral', label: 'خنثی' },
        { value: 'stone', label: 'سنگی' }, { value: 'red', label: 'قرمز' },
        { value: 'orange', label: 'نارنجی' }, { value: 'amber', label: 'کهربایی' },
        { value: 'yellow', label: 'زرد' }, { value: 'lime', label: 'لیمویی' },
        { value: 'green', label: 'سبز' }, { value: 'emerald', label: 'زمردی' },
        { value: 'teal', label: 'فیروزه‌ای' }, { value: 'cyan', label: 'آبی‌فیروزه‌ای' },
        { value: 'sky', label: 'آبی آسمانی' }, { value: 'blue', label: 'آبی' },
        { value: 'indigo', label: 'نیلی' }, { value: 'violet', label: 'بنفش' },
        { value: 'purple', label: 'ارغوانی' }, { value: 'fuchsia', label: 'فوشیا' },
        { value: 'pink', label: 'صورتی' }, { value: 'rose', label: 'گلی' },
        { value: 'magenta', label: 'سرخابی' }, { value: 'olive', label: 'زیتونی' },
    ],

    // ══════════════════════════════════════════════════════
    //  INIT
    // ══════════════════════════════════════════════════════

    init(config = {}) {
        this.orderId       = config.orderId || null;
        this.syncUrl       = config.syncUrl || null;
        this.createOrderUrl = config.createOrderUrl || null;
        this.csrfToken     = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        this.sectionCounter = document.querySelectorAll('.section-item').length;

        SectionItemManager.init({ searchUrl: config.searchUrl });
        ConditionManager.init();

        this._attachListeners();
        this._initExistingSections();
        this._initSectionsSortable();

        // اگر قبلاً order ساخته شده، panel را فعال کن
        if (this.orderId) this._enableSectionPanel();

        console.log('✅ SectionManager initialized', { orderId: this.orderId, syncUrl: this.syncUrl });
    },

    _attachListeners() {
        // ─── دکمه ایجاد/بروزرسانی Order ───
        const orderForm = document.getElementById('orderForm');
        if (orderForm) {
            orderForm.addEventListener('submit', (e) => {
                if (!this.orderId) {
                    // حالت ایجاد → intercept و JSON ارسال کن
                    e.preventDefault();
                    this._submitOrderForm(orderForm);
                }
                // حالت ویرایش → فرم معمولی submit می‌شود
            });
        }

        // ─── دکمه افزودن Section ───
        document.getElementById('addSectionBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this._addSection();
        });
        // دکمه «افزودن اولین بخش» در empty state
        document.addEventListener('click', (e) => {
            if (e.target.closest('#addFirstSectionBtn')) {
                e.preventDefault();
                this._addSection();
            }
        });

        // ─── دکمه ذخیره یکجا ───
        document.getElementById('bulkSaveBtn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this._syncAll();
        });

        // ─── Event delegation ───
        document.addEventListener('click', (e) => {
            const deleteBtn = e.target.closest('.delete-section-btn');
            if (deleteBtn) {
                e.preventDefault(); e.stopPropagation();
                if (confirm('آیا از حذف این بخش اطمینان دارید؟')) {
                    deleteBtn.closest('.section-item')?.remove();
                    this._updateEmptyState();
                }
                return;
            }
            const editBtn = e.target.closest('.edit-section-btn');
            if (editBtn) {
                e.preventDefault(); e.stopPropagation();
                const sec = editBtn.closest('.section-item');
                this._storeOriginal(sec);
                this._setEditMode(sec, true);
                return;
            }
            const cancelBtn = e.target.closest('.cancel-edit-section-btn');
            if (cancelBtn) {
                e.preventDefault(); e.stopPropagation();
                const sec = cancelBtn.closest('.section-item');
                if (!sec.dataset.sectionId) {
                    if (confirm('این بخش هنوز ذخیره نشده. حذف شود؟')) {
                        sec.remove(); this._updateEmptyState();
                    }
                } else {
                    this._restoreOriginal(sec);
                    this._setEditMode(sec, false);
                }
                return;
            }
        });

        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('is-drug-section')) {
                this._toggleItemButtons(e.target.closest('.section-item'));
            }
        });
    },

    // ══════════════════════════════════════════════════════
    //  ORDER FORM — JSON submit (فقط در حالت ایجاد)
    // ══════════════════════════════════════════════════════

    async _submitOrderForm(form) {
        const btn = form.querySelector('[type=submit]');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin ml-2"></i>در حال ذخیره...';

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // تبدیل به payload مناسب
        const payload = {
            name: data.name,
            imp: data.imp,
            condition: data.condition,
            diet: data.diet,
            action: data.action,
            position: data.position,
            notes: data.notes || '',
            category_id: parseInt(data.category),
            color: data.color || '',
        };

        // validation
        const required = ['name', 'imp', 'condition', 'diet', 'action', 'position'];
        const missing = required.filter(f => !payload[f]?.trim());
        if (missing.length || !payload.category_id) {
            this._notify('لطفاً همه فیلدهای اجباری را پر کنید', 'error');
            btn.disabled = false;
            btn.innerHTML = originalText;
            return;
        }

        try {
            const res = await fetch(this.createOrderUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: JSON.stringify(payload),
            });
            const result = await res.json();

            if (res.ok && result.success) {
                this.orderId = result.order_id;
                this.syncUrl = this.syncUrl.replace('__ORDER_ID__', result.order_id);

                this._notify('اوردر با موفقیت ایجاد شد. اکنون می‌توانید بخش‌ها را اضافه کنید.', 'success');

                // بروزرسانی URL بدون reload
                history.replaceState(null, '', result.edit_url);

                // فعال کردن panel
                this._enableSectionPanel();

                // اطلاع‌رسانی به سایر Manager ها (Emergency, DynamicField, Media)
                if (typeof window.onOrderCreated === 'function') {
                    window.onOrderCreated(result.order_id);
                }

                // تغییر عنوان دکمه فرم
                btn.innerHTML = '<i class="fas fa-save ml-2"></i>بروزرسانی اوردر';
                btn.disabled = false;

                // تبدیل فرم به UPDATE mode
                form.setAttribute('action', result.edit_url);
                form.querySelector('[name=_method]')?.remove();
                // اضافه کردن فیلد مخفی برای method override اگر نیاز بود
                this._updateFormToEditMode(form, result.order_id);
            } else {
                this._notify(result.message || 'خطا در ایجاد اوردر', 'error');
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        } catch {
            this._notify('خطا در ارتباط با سرور', 'error');
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    },

    _updateFormToEditMode(form, orderId) {
        // فرم را به حالت submit معمولی برگردان تا ویرایش‌های بعدی normal POST باشد
        form.removeEventListener('submit', this._submitOrderFormBound);
        // اکنون submit معمولی کار می‌کند چون this.orderId مقدار دارد
        // (در attachListeners چک می‌شود if (!this.orderId) intercept کن)
    },

    // ══════════════════════════════════════════════════════
    //  SECTION PANEL
    // ══════════════════════════════════════════════════════

    _enableSectionPanel() {
        const panel = document.getElementById('sectionsPanel');
        if (!panel) return;
        panel.classList.remove('section-disabled');

        // دکمه‌ها را نمایش بده
        document.getElementById('addSectionBtn')?.classList.remove('hidden');
        document.getElementById('bulkSaveBtn')?.classList.remove('hidden');

        // placeholder را حذف کن
        panel.querySelector('.sections-locked-msg')?.remove();

        // اگر container خالی بود، container را نمایش بده
        let container = document.getElementById('sectionsContainer');
        if (!container) {
            panel.insertAdjacentHTML('beforeend', `
                <div id="sectionsContainer" class="space-y-4">
                    <div class="text-center py-12 text-gray-400" id="sectionsEmptyState">
                        <i class="fas fa-layer-group text-4xl mb-3 opacity-40"></i>
                        <p class="text-sm">هنوز بخشی اضافه نشده. اولین بخش را اضافه کنید.</p>
                    </div>
                </div>`);
            this._initSectionsSortable();
        }

        // به اسکرول برو
        setTimeout(() => panel.scrollIntoView({ behavior: 'smooth', block: 'start' }), 300);
    },

    // ══════════════════════════════════════════════════════
    //  ADD SECTION
    // ══════════════════════════════════════════════════════

    _addSection() {
        if (!this.orderId) {
            this._notify('ابتدا اوردر را ذخیره کنید', 'warning');
            document.getElementById('orderForm')?.querySelector('[name=name]')?.focus();
            return;
        }

        this.sectionCounter++;
        const tempId = this._tempId();
        const color = this._randomColor();
        const colorOpts = this.TAILWIND_COLORS.map(c =>
            `<option value="${c.value}" ${c.value === color ? 'selected' : ''}>${c.label}</option>`
        ).join('');

        const html = `
            <div class="section-item bg-white border-2 border-blue-300 rounded-xl p-5 shadow-sm"
                 data-section-id="" data-temp-id="${tempId}">

                <!-- Header -->
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <div class="drag-handle-section text-gray-400 hover:text-blue-500 cursor-grab">
                            <i class="fas fa-grip-vertical text-lg"></i>
                        </div>
                        <span class="text-sm font-semibold text-blue-700">بخش جدید #${this.sectionCounter}</span>
                    </div>
                    <div class="flex items-center gap-1">
                        <button type="button" class="edit-section-btn hidden text-xs px-2 py-1 text-blue-600 hover:bg-blue-50 rounded transition">
                            <i class="fas fa-edit ml-1"></i>ویرایش
                        </button>
                        <button type="button" class="cancel-edit-section-btn text-xs px-2 py-1 text-gray-600 hover:bg-gray-100 rounded transition">
                            <i class="fas fa-times ml-1"></i>انصراف
                        </button>
                        <button type="button" class="delete-section-btn text-xs px-2 py-1 text-red-600 hover:bg-red-50 rounded transition">
                            <i class="fas fa-trash ml-1"></i>حذف
                        </button>
                    </div>
                </div>

                <!-- Fields -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">عنوان بخش <span class="text-red-500">*</span></label>
                        <input type="text" dir="ltr" placeholder="مثال: Drugs، Monitoring..."
                               class="section-title w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 transition">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-600 mb-1">رنگ</label>
                        <select dir="ltr" class="section-color w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 transition">
                            ${colorOpts}
                        </select>
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-xs font-medium text-gray-600 mb-1">توضیحات</label>
                        <textarea dir="rtl" rows="2" placeholder="توضیحات این بخش..."
                                  class="section-notes w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 transition resize-none"></textarea>
                    </div>
                    <div class="flex items-center gap-2">
                        <input type="checkbox" class="is-drug-section w-4 h-4 text-green-600 rounded">
                        <label class="text-sm text-gray-700 cursor-pointer">بخش دارویی</label>
                    </div>
                </div>

                <!-- Items -->
                <div class="items-container border-t border-gray-100 pt-4">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-medium text-gray-600 flex items-center">
                            <i class="fas fa-list ml-1 text-gray-400"></i>آیتم‌ها
                        </span>
                        <div class="flex gap-1">
                            <button type="button" class="add-text-item-btn text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition font-medium">
                                <i class="fas fa-align-right ml-1"></i>متن
                            </button>
                            <button type="button" class="add-drug-item-btn text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition font-medium hidden">
                                <i class="fas fa-pills ml-1"></i>دارو
                            </button>
                        </div>
                    </div>
                    <div class="items-list space-y-2 min-h-[2rem]">
                        <div class="empty-items-state text-center text-gray-400 text-xs py-3">آیتمی اضافه نشده</div>
                    </div>
                </div>

                <!-- Conditions -->
                <div class="conditions-container border-t border-gray-100 pt-4 mt-4">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-medium text-gray-600 flex items-center">
                            <i class="fas fa-code-branch ml-1 text-purple-500"></i>شرایط (Conditions)
                        </span>
                        <button type="button" class="add-condition-btn text-xs px-2 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 transition font-medium">
                            <i class="fas fa-plus ml-1"></i>افزودن شرط
                        </button>
                    </div>
                    <div class="conditions-list space-y-2 min-h-[1rem]">
                        <div class="empty-conditions-state text-center text-gray-400 text-xs py-2">شرطی تعریف نشده</div>
                    </div>
                </div>
            </div>`;

        const container = document.getElementById('sectionsContainer');
        document.getElementById('sectionsEmptyState')?.remove();
        container.insertAdjacentHTML('beforeend', html);

        const newSec = container.lastElementChild;
        this._setEditMode(newSec, true);
        SectionItemManager.initItemsSortable(newSec);
        setTimeout(() => newSec.querySelector('.section-title')?.focus(), 100);
        newSec.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    },

    // ══════════════════════════════════════════════════════
    //  BULK SYNC
    // ══════════════════════════════════════════════════════

    async _syncAll() {
        if (!this.syncUrl || !this.orderId) {
            this._notify('URL sync یافت نشد', 'error');
            return;
        }

        const sections = this._collectSections();
        if (!sections) return;  // validation failed

        const btn = document.getElementById('bulkSaveBtn');
        const origText = btn?.innerHTML;
        if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin ml-2"></i>در حال ذخیره...'; }

        try {
            const res = await fetch(this.syncUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
                body: JSON.stringify({ sections }),
            });
            const result = await res.json();

            if (res.ok && result.success) {
                this._notify('همه تغییرات ذخیره شد', 'success');
                setTimeout(() => location.reload(), 1200);
            } else {
                this._notify(result.message || 'خطا در ذخیره‌سازی', 'error');
                if (btn) { btn.disabled = false; btn.innerHTML = origText; }
            }
        } catch {
            this._notify('خطا در ارتباط با سرور', 'error');
            if (btn) { btn.disabled = false; btn.innerHTML = origText; }
        }
    },

    _collectSections() {
        const sections = [];
        let valid = true;

        document.querySelectorAll('#sectionsContainer .section-item').forEach((el, i) => {
            const title = el.querySelector('.section-title')?.value?.trim();
            if (!title) {
                this._notify(`عنوان بخش #${i + 1} اجباری است`, 'error');
                el.querySelector('.section-title')?.focus();
                valid = false;
                return;
            }

            // items
            const items = [];
            el.querySelectorAll('.items-list > .item-row').forEach((itemEl, j) => {
                const type = itemEl.dataset.itemType;
                if (type === 'text') {
                    items.push({
                        id: itemEl.dataset.itemId ? parseInt(itemEl.dataset.itemId) : null,
                        temp_id: itemEl.dataset.tempId || null,
                        text: itemEl.querySelector('.item-text')?.value?.trim() || '',
                        notes: itemEl.querySelector('.item-notes')?.value?.trim() || '',
                        order_index: j,
                    });
                }
            });

            // drug_items
            const drugItems = [];
            el.querySelectorAll('.items-list > .item-row[data-item-type="drug"]').forEach((itemEl, j) => {
                const drugId = itemEl.querySelector('.drug-id')?.value;
                if (!drugId) return;
                drugItems.push({
                    id: itemEl.dataset.itemId ? parseInt(itemEl.dataset.itemId) : null,
                    temp_id: itemEl.dataset.tempId || null,
                    drug_id: parseInt(drugId),
                    notes: itemEl.querySelector('.drug-notes')?.value?.trim() || '',
                    order_index: j,
                });
            });

            // conditions
            const conditions = ConditionManager.extractConditionsForSection(el);

            const secData = {
                title,
                notes: el.querySelector('.section-notes')?.value?.trim() || '',
                color: el.querySelector('.section-color')?.value || '',
                is_drug_section: el.querySelector('.is-drug-section')?.checked || false,
                order_index: i,
                items,
                drug_items: drugItems,
                conditions,
            };
            if (el.dataset.sectionId) secData.id = parseInt(el.dataset.sectionId);
            else if (el.dataset.tempId) secData.temp_id = el.dataset.tempId;

            sections.push(secData);
        });

        return valid ? sections : null;
    },

    // ══════════════════════════════════════════════════════
    //  HELPERS
    // ══════════════════════════════════════════════════════

    _initExistingSections() {
        document.querySelectorAll('.section-item').forEach(sec => {
            if (!sec.dataset.sectionId && !sec.dataset.tempId) sec.dataset.tempId = this._tempId();
            this._setEditMode(sec, false);
            this._toggleItemButtons(sec);
            SectionItemManager.initItemsSortable(sec);
            SectionItemManager.initializeExistingItems(sec);
        });
    },

    _initSectionsSortable() {
        const container = document.getElementById('sectionsContainer');
        if (!container || typeof Sortable === 'undefined') return;
        if (this._sortable) this._sortable.destroy();
        this._sortable = Sortable.create(container, {
            animation: 150,
            handle: '.drag-handle-section',
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
        });
    },

    _setEditMode(sec, editing) {
        const fields = [
            sec.querySelector('.section-title'),
            sec.querySelector('.section-notes'),
        ];
        const colorSel = sec.querySelector('.section-color');
        const drugCb = sec.querySelector('.is-drug-section');
        const editBtn = sec.querySelector('.edit-section-btn');
        const cancelBtn = sec.querySelector('.cancel-edit-section-btn');

        if (editing) {
            fields.forEach(f => { f?.removeAttribute('readonly'); f?.classList.remove('bg-gray-50', 'cursor-not-allowed'); });
            colorSel?.removeAttribute('disabled');
            drugCb?.removeAttribute('disabled');
            editBtn?.classList.add('hidden');
            cancelBtn?.classList.remove('hidden');
        } else {
            fields.forEach(f => { f?.setAttribute('readonly', ''); f?.classList.add('bg-gray-50', 'cursor-not-allowed'); });
            colorSel?.setAttribute('disabled', '');
            drugCb?.setAttribute('disabled', '');
            editBtn?.classList.remove('hidden');
            cancelBtn?.classList.add('hidden');
        }
    },

    _storeOriginal(sec) {
        sec.dataset._title = sec.querySelector('.section-title')?.value || '';
        sec.dataset._notes = sec.querySelector('.section-notes')?.value || '';
        sec.dataset._color = sec.querySelector('.section-color')?.value || '';
        sec.dataset._drug = sec.querySelector('.is-drug-section')?.checked ? '1' : '0';
    },

    _restoreOriginal(sec) {
        const t = sec.querySelector('.section-title'); if (t) t.value = sec.dataset._title || '';
        const n = sec.querySelector('.section-notes'); if (n) n.value = sec.dataset._notes || '';
        const c = sec.querySelector('.section-color'); if (c) c.value = sec.dataset._color || 'slate';
        const d = sec.querySelector('.is-drug-section'); if (d) d.checked = sec.dataset._drug === '1';
        this._toggleItemButtons(sec);
    },

    _toggleItemButtons(sec) {
        const isDrug = sec.querySelector('.is-drug-section')?.checked;
        sec.querySelector('.add-text-item-btn')?.classList.toggle('hidden', !!isDrug);
        sec.querySelector('.add-drug-item-btn')?.classList.toggle('hidden', !isDrug);
    },

    _updateEmptyState() {
        const container = document.getElementById('sectionsContainer');
        if (!container) return;
        if (!container.querySelector('.section-item')) {
            if (!document.getElementById('sectionsEmptyState')) {
                container.innerHTML = `
                    <div id="sectionsEmptyState" class="text-center py-12 text-gray-400">
                        <i class="fas fa-layer-group text-4xl mb-3 opacity-40"></i>
                        <p class="text-sm">هنوز بخشی اضافه نشده</p>
                    </div>`;
            }
        }
    },

    _randomColor() {
        const used = [...document.querySelectorAll('.section-color')].map(s => s.value);
        const avail = this.TAILWIND_COLORS.filter(c => !used.includes(c.value));
        const pool = avail.length ? avail : this.TAILWIND_COLORS;
        return pool[Math.floor(Math.random() * pool.length)].value;
    },

    _tempId() {
        return `temp_sec_${Date.now()}_${++this.tempIdCounter}`;
    },

    _notify(message, type = 'info') {
        if (window.showNotification) { window.showNotification(message, type); return; }
        const colors = { success: 'bg-green-600', error: 'bg-red-600', warning: 'bg-yellow-600', info: 'bg-blue-600' };
        const el = document.createElement('div');
        el.className = `fixed top-4 left-4 z-50 ${colors[type] || colors.info} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 transition-opacity`;
        el.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()" class="text-white hover:text-gray-200"><i class="fas fa-times"></i></button>`;
        document.body.appendChild(el);
        setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 4000);
    },
};

window.SectionManager = SectionManager;