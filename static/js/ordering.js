/**
 * ordering.js — Vanilla JS
 * استراتژی: همه داده‌ها یک‌بار از API لود می‌شن (همه صفحات)
 * سرچ + فیلتر دسته‌بندی + مرتب‌سازی + pagination کاملاً فرانتی
 */

const orderingApp = (() => {

    // ── State ──────────────────────────────────────────────────────────────
    const state = {
        allOrders:          [],   // تمام داده‌ها از API
        filteredOrders:     [],   // بعد از اعمال سرچ + فیلتر
        pagedOrders:        [],   // فقط صفحه جاری
        categories:         [],
        selectedCategories: [],
        searchQuery:        "",
        sortOrdering:       "",
        loading:            true,
        currentPage:        1,
        itemsPerPage:       12,
        searchTimeout:      null,
    };

    // ── DOM refs ───────────────────────────────────────────────────────────
    const $ = (id) => document.getElementById(id);

    const els = {
        skeletonGrid:    () => $("skeleton-grid"),
        cardsGrid:       () => $("cards-grid"),
        emptyState:      () => $("empty-state"),
        paginationWrap:  () => $("pagination-wrap"),
        pageNumbers:     () => $("page-numbers"),
        pageCurrent:     () => $("page-current"),
        pageTotal:       () => $("page-total"),
        prevBtn:         () => $("prev-btn"),
        nextBtn:         () => $("next-btn"),
        searchInput:     () => $("search-input"),
        searchSpinner:   () => $("search-spinner"),
        searchBtn:       () => $("search-btn"),
        resultsBadge:    () => $("results-badge"),
        resultsText:     () => $("results-count-text"),
        categoryPills:   () => $("category-pills"),
        btnAllCats:      () => $("btn-all-categories"),
        allActiveDot:    () => $("all-active-dot"),
        totalCountPill:  () => $("total-count-pill"),
        clearFiltersBtn: () => $("clear-filters-btn"),
        sortSelect:      () => $("sort-select"),
    };

    // ── Color map ──────────────────────────────────────────────────────────
    const COLOR_HEX = {
        slate:"#64748b", gray:"#6b7280", red:"#ef4444", orange:"#f97316",
        amber:"#f59e0b", yellow:"#eab308", lime:"#84cc16", green:"#22c55e",
        emerald:"#10b981", teal:"#14b8a6", cyan:"#06b6d4", sky:"#0ea5e9",
        blue:"#3b82f6", indigo:"#6366f1", violet:"#8b5cf6", purple:"#a855f7",
        fuchsia:"#d946ef", pink:"#ec4899", rose:"#f43f5e",
    };
    const colorHex = (c) => COLOR_HEX[c] || "#06b6d4";

    // ── API — بار همه‌ی صفحات ─────────────────────────────────────────────
    async function fetchAllOrders() {
        let url = `${API.BASE_URL}api/v1/ordering/`;
        let allResults = [];

        while (url) {
            const res  = await axios.get(url);
            const data = res.data;
            allResults = allResults.concat(data.results || []);
            // اگه next داشت برو صفحه بعد
            url = data.next || null;
        }
        return allResults;
    }

    async function init() {
        try {
            state.loading = true;
            showSkeleton(true);

            state.allOrders = await fetchAllOrders();

            // استخراج دسته‌بندی‌های یکتا
            const seen = new Map();
            state.allOrders.forEach((o) => {
                if (o.category && !seen.has(o.category.id)) {
                    seen.set(o.category.id, o.category);
                }
            });
            state.categories = Array.from(seen.values());

            // اولین رندر
            applyAll();
            renderCategories();

        } catch (err) {
            console.error("Error loading orders:", err);
            showSkeleton(false);

            const msg = (err.response?.status === 429)
                ? "لطفاً چند ثانیه صبر کنید و دوباره امتحان کنید"
                : "خطا در بارگیری اوردرها";
            const title = (err.response?.status === 429) ? "محدودیت درخواست" : "خطا";
            const icon  = (err.response?.status === 429) ? "warning" : "error";

            Swal.fire({ icon, title, text: msg, confirmButtonText: "باشه", confirmButtonColor: "#0077b6" });
        } finally {
            state.loading = false;
        }
    }

    // ── فرانتی: سرچ + فیلتر + مرتب‌سازی ─────────────────────────────────
    function applyAll() {
        let list = [...state.allOrders];

        // ۱. سرچ روی name + slug + category.title
        if (state.searchQuery.trim() !== "") {
            const q = state.searchQuery.trim().toLowerCase();
            list = list.filter((o) => {
                const name     = (o.name             || "").toLowerCase();
                const slug     = (o.slug             || "").toLowerCase();
                const catTitle = (o.category?.title  || "").toLowerCase();
                return name.includes(q) || slug.includes(q) || catTitle.includes(q);
            });
        }

        // ۲. فیلتر دسته‌بندی
        if (state.selectedCategories.length > 0) {
            list = list.filter((o) => state.selectedCategories.includes(o.category?.id));
        }

        // ۳. مرتب‌سازی
        if (state.sortOrdering) {
            const desc = state.sortOrdering.startsWith("-");
            const key  = state.sortOrdering.replace("-", "");
            list.sort((a, b) => {
                const va = (a[key] || "").toString().toLowerCase();
                const vb = (b[key] || "").toString().toLowerCase();
                if (va < vb) return desc ? 1 : -1;
                if (va > vb) return desc ? -1 : 1;
                return 0;
            });
        }

        state.filteredOrders = list;
        // به صفحه اول برگرد وقتی فیلتر عوض شد
        state.currentPage = 1;
        paginate();
    }

    function paginate() {
        const total = state.filteredOrders.length;
        const start = (state.currentPage - 1) * state.itemsPerPage;
        const end   = start + state.itemsPerPage;
        state.pagedOrders = state.filteredOrders.slice(start, end);

        renderCards();
        renderPagination();
        updateResultsBadge(total);
    }

    // ── Render ─────────────────────────────────────────────────────────────
    function showSkeleton(show) {
        els.skeletonGrid().classList.toggle("hidden", !show);
        if (show) {
            els.cardsGrid().classList.add("hidden");
            els.emptyState().classList.add("hidden");
            els.paginationWrap().classList.add("hidden");
        }
    }

    function renderCards() {
        showSkeleton(false);
        const grid = els.cardsGrid();
        grid.innerHTML = "";

        if (state.pagedOrders.length === 0) {
            els.emptyState().classList.remove("hidden");
            els.paginationWrap().classList.add("hidden");
            els.cardsGrid().classList.add("hidden");
            return;
        }

        els.emptyState().classList.add("hidden");
        els.cardsGrid().classList.remove("hidden");

        // انیمیشن fade
        grid.classList.remove("cards-fade");
        void grid.offsetWidth;
        grid.classList.add("cards-fade");

        state.pagedOrders.forEach((order) => {
            grid.insertAdjacentHTML("beforeend", buildCardHTML(order));
        });
    }

    function buildCardHTML(order) {
        const hex      = colorHex(order.color);
        const catTitle = order.category?.title     || "—";
        const catColor = order.category?.color_code || "bg-gray-400";

        // هایلایت متن جستجو در عنوان
        const rawName = order.name || "";
        const name    = state.searchQuery.trim()
            ? rawName.replace(
                new RegExp(`(${escapeRegex(state.searchQuery.trim())})`, "gi"),
                '<mark class="bg-yellow-200 text-yellow-900 rounded px-0.5">$1</mark>'
              )
            : rawName;

        return `
        <div class="group relative transform transition-all duration-500 hover:-translate-y-2 cursor-pointer"
             onclick="orderingApp.handleOrderClick('${order.slug}')">
            <div class="relative bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300">

                <!-- Hover gradient -->
                <div class="absolute inset-0 bg-gradient-to-br from-c5/5 via-transparent to-c4/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

                <!-- Top color bar -->
                <div class="h-1 group-hover:h-1.5 transition-all duration-300" style="background:${hex}"></div>

                <div class="relative p-5">
                    <!-- Header: category + color badge -->
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-1.5 px-2.5 py-1 bg-c5/20 rounded-full">
                            <span class="w-2 h-2 rounded-full ${catColor}"></span>
                            <span class="text-xs font-medium text-c1">${catTitle}</span>
                        </div>
                        <!-- <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-white text-xs font-medium"
                              style="background:${hex}">
                            <span class="w-1.5 h-1.5 rounded-full bg-white/60"></span>
                            ${order.color || "—"}
                        </span> -->
                    </div>

                    <!-- Title با هایلایت سرچ -->
                    <h3 class="text-lg font-bold text-gray-800 mb-3 line-clamp-2 group-hover:text-c1 transition-colors duration-300">
                        ${name}
                    </h3>

                    <!-- Footer -->
                    <div class="flex items-center justify-between pt-3 border-t border-gray-100">

                        <button class="w-9 h-9 bg-gradient-to-r from-c1 to-c2 rounded-xl flex items-center justify-center shadow-md transform group-hover:scale-105 group-hover:shadow-lg transition-all duration-300">
                            <i class="fas fa-arrow-left text-white text-xs transform group-hover:-translate-x-0.5 transition-transform duration-300"></i>
                        </button>
                    </div>
                </div>

                <!-- Corner accents -->
                <div class="absolute top-0 right-0 w-12 h-12 bg-gradient-to-br from-c1/8 to-transparent rounded-bl-full pointer-events-none"></div>
                <div class="absolute bottom-0 left-0 w-12 h-12 bg-gradient-to-tr from-c2/8 to-transparent rounded-tr-full pointer-events-none"></div>
            </div>
            <!-- Hover shadow -->
            <div class="absolute -bottom-4 left-4 right-4 h-8 bg-gray-900/10 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
        </div>`;
    }

    function renderCategories() {
        const container = els.categoryPills();
        container.querySelectorAll(".dynamic-cat-pill").forEach((el) => el.remove());

        els.totalCountPill().textContent = state.allOrders.length;

        state.categories.forEach((cat) => {
            const active = state.selectedCategories.includes(cat.id);
            const btn    = document.createElement("button");
            btn.className = `dynamic-cat-pill group px-5 py-3 rounded-xl font-medium transition-all duration-300 whitespace-nowrap flex items-center gap-2.5 hover:shadow-md transform hover:scale-105 ${
                active
                    ? "bg-gray-900 text-white shadow-lg scale-105"
                    : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
            }`;
            btn.innerHTML = `
                <div class="relative">
                    <span class="block w-4 h-4 rounded-full transition-transform duration-300 group-hover:scale-125 ${cat.color_code} ${active ? "ring-4 ring-white/30" : ""}"></span>
                </div>
                <span class="font-medium">${cat.title}</span>
                ${active ? '<i class="fas fa-check-circle text-xs"></i>' : ""}
            `;
            btn.addEventListener("click", () => toggleCategory(cat.id));
            container.appendChild(btn);
        });

        updateAllButton();
        els.clearFiltersBtn().classList.toggle("hidden", state.selectedCategories.length === 0);
    }

    function updateAllButton() {
        const allActive = state.selectedCategories.length === 0;
        els.btnAllCats().className = `group px-6 py-3 rounded-xl font-medium transition-all duration-300 whitespace-nowrap flex items-center gap-3 transform hover:scale-105 ${
            allActive
                ? "bg-gradient-to-r from-c1 to-c2 text-white shadow-lg"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
        }`;
        els.allActiveDot().classList.toggle("hidden", !allActive);
    }

    function renderPagination() {
        const totalPages = Math.ceil(state.filteredOrders.length / state.itemsPerPage);

        if (totalPages <= 1) {
            els.paginationWrap().classList.add("hidden");
            return;
        }
        els.paginationWrap().classList.remove("hidden");

        els.pageCurrent().textContent = state.currentPage;
        els.pageTotal().textContent   = totalPages;

        els.prevBtn().disabled = state.currentPage === 1;
        els.nextBtn().disabled = state.currentPage === totalPages;

        const pn = els.pageNumbers();
        pn.innerHTML = "";
        const maxVisible = 5;
        let start = Math.max(1, state.currentPage - Math.floor(maxVisible / 2));
        let end   = Math.min(totalPages, start + maxVisible - 1);
        if (end - start + 1 < maxVisible) start = Math.max(1, end - maxVisible + 1);

        for (let i = start; i <= end; i++) {
            const btn  = document.createElement("button");
            btn.textContent = i;
            btn.className = `w-12 h-12 rounded-xl border-2 font-bold transition-all duration-300 transform hover:scale-110 ${
                i === state.currentPage
                    ? "border-transparent bg-gradient-to-r from-c1 to-c2 text-white shadow-lg scale-110"
                    : "border-gray-200 bg-white text-gray-700 hover:text-c1 hover:border-c1"
            }`;
            const page = i;
            btn.addEventListener("click", () => goToPage(page));
            pn.appendChild(btn);
        }
    }

    function updateResultsBadge(total) {
        if (state.searchQuery.trim() !== "" || state.selectedCategories.length > 0) {
            els.resultsBadge().classList.remove("hidden");
            els.resultsText().textContent = `${total} نتیجه یافت شد`;
        } else {
            els.resultsBadge().classList.add("hidden");
        }
    }

    // ── Actions ────────────────────────────────────────────────────────────
    function performSearch() {
        const val = els.searchInput().value;
        state.searchQuery = val;

        // نشون بده spinner
        els.searchSpinner().classList.remove("hidden");
        clearTimeout(state.searchTimeout);

        state.searchTimeout = setTimeout(() => {
            applyAll();
            els.searchSpinner().classList.add("hidden");
        }, 300);
    }

    function toggleCategory(categoryId) {
        const idx = state.selectedCategories.indexOf(categoryId);
        if (idx > -1) state.selectedCategories.splice(idx, 1);
        else          state.selectedCategories.push(categoryId);
        renderCategories();
        applyAll();
    }

    function toggleAllCategories() {
        state.selectedCategories = [];
        renderCategories();
        applyAll();
    }

    function applyFilters() {
        state.sortOrdering = els.sortSelect().value;
        applyAll();
    }

    function clearFilters() {
        state.selectedCategories = [];
        els.sortSelect().value   = "";
        state.sortOrdering       = "";
        renderCategories();
        applyAll();
    }

    function goToPage(page) {
        const totalPages = Math.ceil(state.filteredOrders.length / state.itemsPerPage);
        if (page < 1 || page > totalPages) return;
        state.currentPage = page;
        paginate();
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function handleOrderClick(slug) {
        window.location.href = `/ordering/${slug}`;
    }

    function resetAll() {
        els.searchInput().value  = "";
        state.searchQuery        = "";
        state.selectedCategories = [];
        state.currentPage        = 1;
        els.sortSelect().value   = "";
        state.sortOrdering       = "";
        renderCategories();
        applyAll();
    }

    // ── Utils ──────────────────────────────────────────────────────────────
    function escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    // ── Bootstrap ──────────────────────────────────────────────────────────
    function boot() {
        els.searchInput().addEventListener("input",   performSearch);
        els.searchBtn().addEventListener("click",     performSearch);
        els.searchInput().addEventListener("keydown", (e) => { if (e.key === "Enter") performSearch(); });
        init();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }

    return {
        state,
        toggleAllCategories,
        toggleCategory,
        applyFilters,
        clearFilters,
        goToPage,
        handleOrderClick,
        resetAll,
    };
})();