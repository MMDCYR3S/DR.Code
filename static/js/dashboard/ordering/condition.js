/**
 * ConditionManager
 * مدیریت شرایط با temp_id و inline form
 */

const ConditionManager = {
    conditionCounter: 0,

    init() {
        this.attachEventListeners();
        this._initExisting();
        console.log('✅ ConditionManager initialized');
    },

    _initExisting() {
        document.querySelectorAll('.condition-item').forEach(el => {
            if (!el.dataset.conditionId && !el.dataset.tempId) {
                el.dataset.tempId = this.generateTempId();
            }
        });
    },

    generateTempId() {
        return `temp_cond_${Date.now()}_${++this.conditionCounter}`;
    },

    attachEventListeners() {
        document.addEventListener('click', (e) => {
            // افزودن
            const addBtn = e.target.closest('.add-condition-btn');
            if (addBtn) {
                e.preventDefault(); e.stopPropagation();
                this.showAddForm(addBtn.closest('.section-item'));
                return;
            }
            // ویرایش
            const editBtn = e.target.closest('.edit-condition-btn');
            if (editBtn) {
                e.preventDefault(); e.stopPropagation();
                this.showEditForm(
                    editBtn.closest('.condition-item'),
                    editBtn.closest('.section-item')
                );
                return;
            }
            // حذف
            const delBtn = e.target.closest('.delete-condition-btn');
            if (delBtn) {
                e.preventDefault(); e.stopPropagation();
                if (confirm('آیا از حذف این شرط اطمینان دارید؟')) {
                    delBtn.closest('.condition-item')?.remove();
                }
            }
        });
    },

    // ─── فرم افزودن ────────────────────────────────────────────────
    showAddForm(sectionEl) {
        const list = this._getConditionsList(sectionEl);

        // حذف فرم باز قبلی
        list.parentElement.querySelector('.condition-form-wrapper')?.remove();

        const html = `
            <div class="condition-form-wrapper bg-purple-50 border-2 border-purple-300 rounded-lg p-4 mb-3">
                <h6 class="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                    <i class="fas fa-plus-circle ml-2 text-purple-600"></i>افزودن شرط جدید
                </h6>
                <div class="mb-3">
                    <label class="block text-xs font-medium text-gray-600 mb-1">متن شرط <span class="text-red-500">*</span></label>
                    <textarea rows="2" dir="ltr" placeholder="Enter condition text..."
                              class="condition-text w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 transition resize-none"></textarea>
                </div>
                <div class="mb-3">
                    <label class="block text-xs font-medium text-gray-600 mb-1">آیتم‌های مرتبط <span class="text-xs text-gray-400">(اختیاری)</span></label>
                    <div class="related-items-selector border border-gray-200 rounded-lg p-2 bg-white max-h-48 overflow-y-auto space-y-1">
                        ${this._itemCheckboxes(sectionEl)}
                    </div>
                </div>
                <div class="flex gap-2">
                    <button type="button" class="confirm-add-condition-btn px-4 py-1.5 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition font-medium">
                        <i class="fas fa-check ml-1"></i>ذخیره
                    </button>
                    <button type="button" class="cancel-condition-form-btn px-4 py-1.5 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300 transition font-medium">
                        <i class="fas fa-times ml-1"></i>انصراف
                    </button>
                </div>
            </div>`;

        list.insertAdjacentHTML('beforebegin', html);
        const wrapper = list.previousElementSibling;
        setTimeout(() => wrapper.querySelector('.condition-text')?.focus(), 50);

        wrapper.querySelector('.confirm-add-condition-btn').addEventListener('click', () => {
            this._submitAdd(wrapper, sectionEl, list);
        });
        wrapper.querySelector('.cancel-condition-form-btn').addEventListener('click', () => {
            wrapper.remove();
        });
    },

    _submitAdd(wrapper, sectionEl, list) {
        const text = wrapper.querySelector('.condition-text').value.trim();
        if (!text) {
            wrapper.querySelector('.condition-text').focus();
            return;
        }
        const selected = this._getSelectedItems(wrapper);
        const tempId = this.generateTempId();

        this._appendConditionDOM(list, {
            conditionId: '',
            tempId,
            text,
            itemTempIds: selected.textItems,
            drugItemTempIds: selected.drugItems,
        }, sectionEl);

        wrapper.remove();
    },

    // ─── فرم ویرایش ─────────────────────────────────────────────────
    showEditForm(condEl, sectionEl) {
        const currentText = condEl.querySelector('.condition-text-display')?.textContent.trim() || '';
        const itemTempIds = (condEl.dataset.itemTempIds || '').split(',').filter(Boolean);
        const drugItemTempIds = (condEl.dataset.drugItemTempIds || '').split(',').filter(Boolean);

        const html = `
            <div class="condition-edit-form bg-yellow-50 border-2 border-yellow-300 rounded-lg p-4 mb-3">
                <h6 class="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                    <i class="fas fa-edit ml-2 text-yellow-600"></i>ویرایش شرط
                </h6>
                <div class="mb-3">
                    <label class="block text-xs font-medium text-gray-600 mb-1">متن شرط <span class="text-red-500">*</span></label>
                    <textarea rows="2" dir="ltr"
                              class="condition-text w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-yellow-500 transition resize-none">${this.escapeHtml(currentText)}</textarea>
                </div>
                <div class="mb-3">
                    <label class="block text-xs font-medium text-gray-600 mb-1">آیتم‌های مرتبط</label>
                    <div class="related-items-selector border border-gray-200 rounded-lg p-2 bg-white max-h-48 overflow-y-auto space-y-1">
                        ${this._itemCheckboxes(sectionEl, { textItems: itemTempIds, drugItems: drugItemTempIds })}
                    </div>
                </div>
                <div class="flex gap-2">
                    <button type="button" class="confirm-edit-condition-btn px-4 py-1.5 bg-yellow-600 text-white rounded-lg text-sm hover:bg-yellow-700 transition font-medium">
                        <i class="fas fa-check ml-1"></i>بروزرسانی
                    </button>
                    <button type="button" class="cancel-edit-condition-btn px-4 py-1.5 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300 transition font-medium">
                        <i class="fas fa-times ml-1"></i>انصراف
                    </button>
                </div>
            </div>`;

        condEl.style.display = 'none';
        condEl.insertAdjacentHTML('afterend', html);
        const editWrapper = condEl.nextElementSibling;
        setTimeout(() => editWrapper.querySelector('.condition-text')?.focus(), 50);

        editWrapper.querySelector('.confirm-edit-condition-btn').addEventListener('click', () => {
            const newText = editWrapper.querySelector('.condition-text').value.trim();
            if (!newText) { editWrapper.querySelector('.condition-text').focus(); return; }
            const selected = this._getSelectedItems(editWrapper);

            condEl.querySelector('.condition-text-display').textContent = newText;
            condEl.dataset.itemTempIds = selected.textItems.join(',');
            condEl.dataset.drugItemTempIds = selected.drugItems.join(',');
            this._updateBadges(condEl, sectionEl, selected);

            editWrapper.remove();
            condEl.style.display = '';
        });
        editWrapper.querySelector('.cancel-edit-condition-btn').addEventListener('click', () => {
            editWrapper.remove();
            condEl.style.display = '';
        });
    },

    // ─── helpers ────────────────────────────────────────────────────
    _getConditionsList(sectionEl) {
        let list = sectionEl.querySelector('.conditions-list');
        if (!list) {
            sectionEl.querySelector('.items-container')?.insertAdjacentHTML('afterend', `
                <div class="conditions-container mt-4 pt-4 border-t border-gray-200">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm font-medium text-gray-700 flex items-center">
                            <i class="fas fa-code-branch ml-2 text-purple-600"></i>شرایط
                        </span>
                        <button type="button" class="add-condition-btn text-xs px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-semibold">
                            <i class="fas fa-plus ml-1"></i>افزودن شرط
                        </button>
                    </div>
                    <div class="conditions-list space-y-2"></div>
                </div>`);
            list = sectionEl.querySelector('.conditions-list');
        }
        return list;
    },

    _itemCheckboxes(sectionEl, selected = null) {
        const items = sectionEl.querySelectorAll('.items-list > .item-row');
        if (!items.length) return `<p class="text-xs text-gray-400 text-center py-2">هیچ آیتمی وجود ندارد</p>`;

        return [...items].map(item => {
            const id = item.dataset.tempId || item.dataset.itemId;
            if (!id) return '';
            const type = item.dataset.itemType;
            const text = type === 'drug'
                ? (item.querySelector('.drug-search-input')?.value || 'دارو')
                : (item.querySelector('.item-text')?.value || 'آیتم');
            const checked = selected && (
                selected.textItems?.includes(id) || selected.drugItems?.includes(id)
            );
            const icon = type === 'drug' ? 'fa-pills text-green-600' : 'fa-align-right text-blue-500';
            return `
                <label class="flex items-center gap-2 p-1.5 hover:bg-gray-50 rounded cursor-pointer text-sm">
                    <input type="checkbox" class="item-checkbox w-4 h-4 text-purple-600 rounded"
                           value="${id}" data-item-type="${type}" ${checked ? 'checked' : ''}>
                    <i class="fas ${icon} text-xs"></i>
                    <span dir="ltr" class="truncate max-w-xs">${this.escapeHtml(text.substring(0, 60))}</span>
                </label>`;
        }).join('');
    },

    _getSelectedItems(container) {
        const textItems = [], drugItems = [];
        container.querySelectorAll('.item-checkbox:checked').forEach(cb => {
            if (cb.dataset.itemType === 'drug') drugItems.push(cb.value);
            else textItems.push(cb.value);
        });
        return { textItems, drugItems };
    },

    _appendConditionDOM(list, { conditionId, tempId, text, itemTempIds, drugItemTempIds }, sectionEl) {
        const badges = this._buildBadges(sectionEl, itemTempIds, drugItemTempIds);
        const html = `
            <div class="condition-item bg-purple-50 border border-purple-200 rounded-lg p-3"
                 data-condition-id="${conditionId}"
                 data-temp-id="${tempId}"
                 data-item-temp-ids="${itemTempIds.join(',')}"
                 data-drug-item-temp-ids="${drugItemTempIds.join(',')}">
                <div class="flex justify-between items-start gap-2">
                    <div class="flex-1">
                        <div class="condition-text-display text-sm text-gray-800 leading-relaxed" dir="ltr">${this.escapeHtml(text)}</div>
                        <div class="related-badges flex flex-wrap gap-1 mt-2">${badges}</div>
                    </div>
                    <div class="flex gap-1 shrink-0">
                        <button type="button" class="edit-condition-btn text-yellow-600 hover:bg-yellow-100 p-1.5 rounded transition" title="ویرایش">
                            <i class="fas fa-pencil text-xs"></i>
                        </button>
                        <button type="button" class="delete-condition-btn text-red-600 hover:bg-red-100 p-1.5 rounded transition" title="حذف">
                            <i class="fas fa-trash text-xs"></i>
                        </button>
                    </div>
                </div>
            </div>`;

        // حذف empty state
        list.querySelector('.empty-conditions-state')?.remove();
        list.insertAdjacentHTML('beforeend', html);
    },

    _buildBadges(sectionEl, itemTempIds, drugItemTempIds) {
        let html = '';
        [...itemTempIds, ...drugItemTempIds].forEach(id => {
            const el = sectionEl.querySelector(`.item-row[data-temp-id="${id}"], .item-row[data-item-id="${id}"]`);
            if (!el) return;
            const type = el.dataset.itemType;
            const text = type === 'drug'
                ? (el.querySelector('.drug-search-input')?.value || 'دارو')
                : (el.querySelector('.item-text')?.value || 'آیتم');
            const cls = type === 'drug' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700';
            const icon = type === 'drug' ? 'fa-pills' : 'fa-align-right';
            html += `<span class="text-xs px-2 py-0.5 ${cls} rounded flex items-center gap-1" dir="ltr">
                        <i class="fas ${icon} text-xs"></i>${this.escapeHtml(text.substring(0, 30))}
                     </span>`;
        });
        return html || '<span class="text-xs text-gray-400 italic">بدون آیتم مرتبط</span>';
    },

    _updateBadges(condEl, sectionEl, selected) {
        const badgesEl = condEl.querySelector('.related-badges');
        if (badgesEl) {
            badgesEl.innerHTML = this._buildBadges(
                sectionEl,
                selected.textItems,
                selected.drugItems
            );
        }
    },

    /** استخراج برای bulk save */
    extractConditionsForSection(sectionEl) {
        return [...sectionEl.querySelectorAll('.condition-item')].map((el, i) => ({
            id: el.dataset.conditionId ? parseInt(el.dataset.conditionId) : null,
            temp_id: el.dataset.tempId || null,
            text: el.querySelector('.condition-text-display')?.textContent.trim() || '',
            order_index: i,
            item_temp_ids: (el.dataset.itemTempIds || '').split(',').filter(Boolean),
            drug_item_temp_ids: (el.dataset.drugItemTempIds || '').split(',').filter(Boolean),
        })).filter(c => c.text);
    },

    escapeHtml(text) {
        if (!text) return '';
        const d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    },
};

window.ConditionManager = ConditionManager;