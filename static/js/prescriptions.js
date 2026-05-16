// Alpine.js Component for Prescriptions Page
function prescriptionsApp() {
    return {
        // State
        prescriptions: [],
        filteredPrescriptions: [],
        categories: [],
        selectedCategories: [],
        searchQuery: '',
        loading: true,
        searchLoading: false,
        currentPage: 1,
        itemsPerPage: 10,
        isPremiumUser: false,
        fuse: null,
        searchCache: {},
        lastLoadTime: null,
        totalCount: 0,
        nextPage: null,
        previousPage: null,
        isSearchMode: false, // برای تشخیص حالت جستجو

        // Computed
        get totalPages() {
            return Math.ceil(this.totalCount / this.itemsPerPage);
        },

        get visiblePages() {
            const pages = [];
            const maxVisible = 5;
            let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
            let end = Math.min(this.totalPages, start + maxVisible - 1);

            if (end - start + 1 < maxVisible) {
                start = Math.max(1, end - maxVisible + 1);
            }

            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            return pages;
        },

        // Methods
        async init() {
            // Check if user is premium
            const profile = StorageManager.getUserProfile();
            this.isPremiumUser = profile?.role === 'premium';

            // Load prescriptions
            await this.loadPrescriptions();
        },

        async loadPrescriptions(page = 1, searchTerm = '') {
            try {
                this.loading = true;

                // ساخت URL با پارامترها
                let url = `${API.BASE_URL}api/v1/prescriptions/`;
                const params = new URLSearchParams();

                // اضافه کردن پارامتر صفحه
                if (page > 1) {
                    params.append('page', page);
                }

                // اضافه کردن پارامتر جستجو
                if (searchTerm) {
                    params.append('search', searchTerm);
                    this.isSearchMode = true;
                } else {
                    this.isSearchMode = false;
                }

                // اضافه کردن فیلتر دسته‌بندی
                if (this.selectedCategories.length > 0) {
                    this.selectedCategories.forEach(catId => {
                        params.append('category', catId);
                    });
                }

                if (params.toString()) {
                    url += '?' + params.toString();
                }

                const response = await axios.get(url);

                // ذخیره نتایج
                this.prescriptions = response.data.results;
                this.filteredPrescriptions = [...this.prescriptions];

                // دسته‌بندی‌ها فقط در صفحه اول و بدون جستجو
                if (page === 1 && !searchTerm && response.data.filters) {
                    this.categories = response.data.filters.categories;
                }

                // اطلاعات پیجینیشن
                this.totalCount = response.data.count || 0;
                this.nextPage = response.data.next;
                this.previousPage = response.data.previous;

                // تنظیم itemsPerPage بر اساس نتایج
                if (response.data.results.length > 0 && page === 1) {
                    this.itemsPerPage = response.data.results.length;
                }

            } catch (error) {
                console.error('Error loading prescriptions:', error);
                
                if (error.response && error.response.status === 429) {
                    Swal.fire({
                        icon: 'warning',
                        title: 'محدودیت درخواست',
                        text: 'لطفاً چند ثانیه صبر کنید و دوباره امتحان کنید',
                        confirmButtonText: 'باشه',
                        confirmButtonColor: '#0077b6'
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'خطا',
                        text: 'خطا در بارگیری نسخه‌ها',
                        confirmButtonText: 'باشه',
                        confirmButtonColor: '#0077b6'
                    });
                }
            } finally {
                this.loading = false;
            }
        },

        performSearch() {
            // اگر جستجو خالی شد
            if (this.searchQuery.trim() === '') {
                this.currentPage = 1;
                this.loadPrescriptions(1);
                return;
            }

            this.searchLoading = true;

            // Debounce search
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(async () => {
                this.currentPage = 1;
                await this.loadPrescriptions(1, this.searchQuery);
                this.searchLoading = false;
            }, 500); // تاخیر 500 میلی‌ثانیه برای جلوگیری از درخواست‌های زیاد
        },

        toggleCategory(categoryId) {
            const index = this.selectedCategories.indexOf(categoryId);
            if (index > -1) {
                this.selectedCategories.splice(index, 1);
            } else {
                this.selectedCategories.push(categoryId);
            }

            this.applyFilters();
        },

        toggleAllCategories() {
            this.selectedCategories = [];
            this.applyFilters();
        },

        applyFilters() {
            // بارگذاری مجدد با فیلترهای جدید
            this.currentPage = 1;
            this.loadPrescriptions(1, this.searchQuery);
        },

        goToPage(page) {
            if (page >= 1 && page <= this.totalPages) {
                this.currentPage = page;
                this.loadPrescriptions(page, this.searchQuery);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        },

        handlePrescriptionClick(prescription) {
            if (prescription.access_level === 'PREMIUM' && !this.isPremiumUser) {
                // Handled by overlay click
                return;
            }

            // Navigate to prescription detail
            window.location.href = `/prescriptions/${prescription.slug}`;
        },

        showPremiumModal() {
            Swal.fire({
                title: 'نسخه ویژه',
                html: `
                    <div class="text-center">
                        <i class="fas fa-crown text-6xl text-amber-500 mb-4"></i>
                        <p class="mb-4">این نسخه فقط برای کاربران ویژه در دسترس است</p>
                        <p class="text-sm text-gray-600">با خرید اشتراک ویژه به تمام نسخه‌ها دسترسی داشته باشید</p>
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: 'مشاهده پلن‌های ویژه',
                cancelButtonText: 'بستن',
                confirmButtonColor: '#f59e0b',
                cancelButtonColor: '#6b7280'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = '/plans';
                }
            });
        }
    };
}
