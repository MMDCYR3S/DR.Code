/**
 * SectionItemManager
 * مدیریت آیتم‌های متنی و دارویی با Drag & Drop و temp_id
 */

const SectionItemManager = {
    itemCounter: 0,
    itemsSortables: new Map(),
    drugSearchCache: new Map(),
    drugSearchUrl: '/dashboard/admin/drugs/search/',

    init(config = {}) {
        if (config.searchUrl) this.drugSearchUrl = config.searchUrl;
        this.attachEventListeners();
        this.initializeAllSections();
        console.log('✅ SectionItemManager initialized');
    },

    initializeAllSections() {
        document.querySelectorAll('.section-item').forEach(section => {
            this.initializeExistingItems(section);
            this.initItemsSortable(section);
        });
    },

    initializeExistingItems(sectionElement) {
        sectionElement.querySelectorAll('.items-list > .item-row').forEach(itemEl => {
            if (!itemEl.dataset.itemId && !itemEl.dataset.tempId) {
                itemEl.dataset.tempId = this.generateTempId();
            }
            this.setupFieldDirections(itemEl, itemEl.dataset.itemType);
        });
    },

    setupFieldDirections(itemEl, itemType) {
        if (itemType === 'text') {
            itemEl.querySelector('.item-text')?.setAttribute('dir', 'ltr');
            itemEl.querySelector('.item-notes')?.setAttribute('dir', 'rtl');
        } else if (itemType === 'drug') {
            itemEl.querySelector('.drug-search-input')?.setAttribute('dir', 'ltr');
            itemEl.querySelector('.drug-notes')?.setAttribute('dir', 'rtl');
        }
    },

    generateTempId() {
        return `temp_item_${Date.now()}_${++this.itemCounter}`;
    },

    initItemsSortable(sectionElement) {
        const itemsList = sectionElement.querySelector('.items-list');
        if (!itemsList || typeof Sortable === 'undefined') return;

        const existing = this.itemsSortables.get(sectionElement);
        if (existing) existing.destroy();

        const sortable = Sortable.create(itemsList, {
            animation: 150,
            handle: '.drag-handle-item',
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
        });
        this.itemsSortables.set(sectionElement, sortable);
    },

    attachEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.closest('.add-text-item-btn')) {
                e.preventDefault(); e.stopPropagation();
                this.addTextItemForm(e.target.closest('.section-item'));
            }
            if (e.target.closest('.add-drug-item-btn')) {
                e.preventDefault(); e.stopPropagation();
                this.addDrugItemForm(e.target.closest('.section-item'));
            }
            if (e.target.closest('.delete-item-btn')) {
                e.preventDefault(); e.stopPropagation();
                this.handleDeleteItem(e.target.closest('.delete-item-btn'));
            }
            if (e.target.closest('.drug-result-item')) {
                e.preventDefault(); e.stopPropagation();
                this.selectDrug(e.target.closest('.drug-result-item'));
            }
            if (!e.target.closest('.drug-search-container')) {
                this.closeAllDropdowns();
            }
        });

        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('drug-search-input')) {
                clearTimeout(e.target._searchTimeout);
                e.target._searchTimeout = setTimeout(() => this.searchDrugs(e.target), 300);
            }
        });

        document.addEventListener('focus', (e) => {
            if (e.target.classList.contains('drug-search-input') && e.target.value.trim().length >= 2) {
                this.searchDrugs(e.target);
            }
        }, true);
    },

    handleDeleteItem(btn) {
        const itemEl = btn.closest('.item-row');
        if (!itemEl) return;
        const label = itemEl.dataset.itemType === 'drug' ? 'دارویی' : 'متنی';
        if (confirm(`آیا از حذف این آیتم ${label} اطمینان دارید؟`)) {
            itemEl.remove();
        }
    },

    addTextItemForm(sectionElement) {
        const tempId = this.generateTempId();
        const html = `
            <div class="item-row bg-gray-50 border border-gray-200 rounded-lg p-3 mb-2 transition-all hover:shadow-sm"
                 data-item-id="" data-item-type="text" data-temp-id="${tempId}">
                <div class="flex items-start gap-2">
                    <div class="drag-handle-item cursor-move text-gray-400 hover:text-blue-500 mt-2">
                        <i class="fas fa-grip-vertical"></i>
                    </div>
                    <i class="fas fa-align-right text-blue-500 mt-3"></i>
                    <div class="flex-1 space-y-2">
                        <textarea rows="2" placeholder="متن آیتم..." dir="ltr"
                                  class="item-text w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 transition resize-none text-sm"></textarea>
                        <input type="text" placeholder="یادداشت (اختیاری)" dir="rtl"
                               class="item-notes w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 transition text-sm">
                    </div>
                    <button type="button" class="delete-item-btn text-red-500 hover:text-red-700 mt-2 p-1 rounded hover:bg-red-50 transition">
                        <i class="fas fa-trash text-sm"></i>
                    </button>
                </div>
            </div>`;

        const list = sectionElement.querySelector('.items-list');
        if (!list) return;
        this._removeEmptyState(list);
        list.insertAdjacentHTML('beforeend', html);
        setTimeout(() => list.lastElementChild.querySelector('.item-text')?.focus(), 50);
    },

    addDrugItemForm(sectionElement) {
        const tempId = this.generateTempId();
        const html = `
            <div class="item-row bg-green-50 border border-green-200 rounded-lg p-3 mb-2 transition-all hover:shadow-sm"
                 data-item-id="" data-item-type="drug" data-temp-id="${tempId}">
                <div class="flex items-start gap-2">
                    <div class="drag-handle-item cursor-move text-gray-400 hover:text-blue-500 mt-2">
                        <i class="fas fa-grip-vertical"></i>
                    </div>
                    <i class="fas fa-pills text-green-600 mt-3"></i>
                    <div class="flex-1 space-y-2">
                        <div class="drug-search-container relative">
                            <input type="text" placeholder="جستجوی دارو..." dir="ltr" autocomplete="off"
                                   class="drug-search-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 transition text-sm">
                            <input type="hidden" class="drug-id">
                            <div class="drug-dropdown hidden absolute z-20 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-48 overflow-y-auto"></div>
                        </div>
                        <input type="text" placeholder="یادداشت (اختیاری)" dir="rtl"
                               class="drug-notes w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 transition text-sm">
                    </div>
                    <button type="button" class="delete-item-btn text-red-500 hover:text-red-700 mt-2 p-1 rounded hover:bg-red-50 transition">
                        <i class="fas fa-trash text-sm"></i>
                    </button>
                </div>
            </div>`;

        const list = sectionElement.querySelector('.items-list');
        if (!list) return;
        this._removeEmptyState(list);
        list.insertAdjacentHTML('beforeend', html);
        setTimeout(() => list.lastElementChild.querySelector('.drug-search-input')?.focus(), 50);
    },

    _removeEmptyState(list) {
        list.querySelector('.empty-items-state')?.remove();
    },

    async searchDrugs(inputElement) {
        const query = inputElement.value.trim();
        const container = inputElement.closest('.drug-search-container');
        const dropdown = container?.querySelector('.drug-dropdown');
        if (!dropdown) return;

        if (query.length < 2) { dropdown.classList.add('hidden'); return; }

        if (this.drugSearchCache.has(query)) {
            this.renderDrugResults(dropdown, this.drugSearchCache.get(query));
            dropdown.classList.remove('hidden');
            return;
        }

        dropdown.innerHTML = `<div class="p-3 text-center text-gray-500 text-sm"><i class="fas fa-spinner fa-spin ml-1"></i>در حال جستجو...</div>`;
        dropdown.classList.remove('hidden');

        try {
            const res = await fetch(`${this.drugSearchUrl}?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            if (data.success && data.drugs) {
                this.drugSearchCache.set(query, data.drugs);
                this.renderDrugResults(dropdown, data.drugs);
            } else {
                dropdown.innerHTML = `<div class="p-3 text-center text-gray-500 text-sm">دارویی یافت نشد</div>`;
            }
        } catch {
            dropdown.innerHTML = `<div class="p-3 text-center text-red-500 text-sm">خطا در جستجو</div>`;
        }
    },

    renderDrugResults(dropdown, drugs) {
        if (!drugs?.length) {
            dropdown.innerHTML = `<div class="p-3 text-center text-gray-500 text-sm">دارویی یافت نشد</div>`;
            return;
        }
        dropdown.innerHTML = drugs.map(d => `
            <div class="drug-result-item p-3 hover:bg-green-50 cursor-pointer border-b border-gray-100 last:border-0 transition-colors"
                 data-drug-id="${d.id}" data-drug-title="${this.escapeHtml(d.title)}" data-drug-code="${this.escapeHtml(d.code || '')}">
                <div class="font-medium text-sm text-gray-800" dir="ltr">${this.escapeHtml(d.title)}</div>
                ${d.code ? `<div class="text-xs text-gray-500 mt-0.5" dir="ltr">کد: ${this.escapeHtml(d.code)}</div>` : ''}
            </div>`).join('');
    },

    selectDrug(drugItem) {
        const container = drugItem.closest('.drug-search-container');
        container.querySelector('.drug-search-input').value = drugItem.dataset.drugTitle;
        container.querySelector('.drug-id').value = drugItem.dataset.drugId;
        container.querySelector('.drug-dropdown').classList.add('hidden');
    },

    closeAllDropdowns() {
        document.querySelectorAll('.drug-dropdown').forEach(d => d.classList.add('hidden'));
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};

window.SectionItemManager = SectionItemManager;