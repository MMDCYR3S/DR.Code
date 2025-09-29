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
        lastLoadTime: null, // اضافه کن
        totalCount: 0,      // اضافه کن
        nextPage: null,     // اضافه کن
        previousPage: null, // اضافه کن
        
        
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
            
            // Initialize Fuse.js for search
            this.initializeSearch();
        },
        
        async loadPrescriptions(page = 1) {
            try {
                this.loading = true;
                
                // درخواست به API با پارامترهای صفحه‌بندی
                let url = `${API.BASE_URL}api/v1/prescriptions/`;
                const params = new URLSearchParams();
                
                if (page > 1) {
                    params.append('page', page);
                }
                
                if (params.toString()) {
                    url += '?' + params.toString();
                }
                
                const response = await axios.get(url);
                
                // ذخیره نتایج
                this.prescriptions = response.data.results;
                this.filteredPrescriptions = [...this.prescriptions];
                
                // برای صفحه اول، دسته‌بندی‌ها رو هم بگیر
                if (page === 1 && response.data.filters) {
                    this.categories = response.data.filters.categories;
                }
                
                // ذخیره اطلاعات پیجینیشن
                this.totalCount = response.data.count;
                this.nextPage = response.data.next;
                this.previousPage = response.data.previous;
                
                // محاسبه مجدد تعداد صفحات
                // بر اساس page_size واقعی که API برمی‌گردونه
                if (response.data.results.length > 0 && page === 1) {
                    // تخمین page_size از طول نتایج صفحه اول
                    this.itemsPerPage = response.data.results.length;
                }
                
                // Load detailed data برای جستجو
                await this.loadDetailedData();
                
            } catch (error) {
                console.error('Error loading prescriptions:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'خطا',
                    text: 'خطا در بارگیری نسخه‌ها',
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#0077b6'
                });
            } finally {
                this.loading = false;
            }
        },
        
        
        async loadDetailedData() {
            // Load detailed prescription data for better search
            const detailPromises = this.prescriptions.map(async (prescription) => {
                try {
                    const response = await axios.get(`${API.BASE_URL}api/v1/prescriptions/${prescription.slug}/`);
                    
                    // Create comprehensive searchable content
                    const drugs = response.data.prescription_drugs
                        .map(pd => {
                            // جمع‌آوری همه اطلاعات دارویی
                            return `
                                ${pd.drug.title} 
                                ${pd.drug.code} 
                                ${pd.drug.generic_code || ''} 
                                ${pd.drug.description || ''}
                                ${pd.description || ''}
                                ${pd.usage || ''}
                                ${pd.dosage || ''}
                            `;
                        })
                        .join(' ');
                    
                    // ساخت محتوای جستجو از همه فیلدها
                    prescription.searchContent = `
                        ${prescription.title}
                        ${prescription.all_names.join(' ')}
                        ${prescription.primary_name}
                        ${prescription.category.title}
                        ${drugs}
                        ${response.data.description || ''}
                        ${response.data.contraindications || ''}
                        ${response.data.clinical_tips || ''}
                        ${response.data.patient_education || ''}
                        ${response.data.follow_up || ''}
                    `.toLowerCase();
                    
                    prescription.detailedData = response.data;
                } catch (error) {
                    console.error(`Error loading details for ${prescription.slug}:`, error);
                    prescription.searchContent = `
                        ${prescription.title}
                        ${prescription.all_names.join(' ')}
                        ${prescription.primary_name}
                        ${prescription.category.title}
                    `.toLowerCase();
                }
            });
            
            await Promise.all(detailPromises);
            
            // Re-initialize Fuse after loading detailed data
            this.initializeSearch();
        }
        
        ,
        
        initializeSearch() {
            // Configure Fuse.js with better options
            const options = {
                keys: [
                    { name: 'title', weight: 3 },
                    { name: 'all_names', weight: 2.5 },
                    { name: 'primary_name', weight: 2 },
                    { name: 'category.title', weight: 1.5 },
                    { name: 'searchContent', weight: 1 },
                    // اضافه کردن فیلدهای جزئیات
                    { name: 'detailedData.description', weight: 1.2 },
                    { name: 'detailedData.prescription_drugs.drug.title', weight: 2 },
                    { name: 'detailedData.prescription_drugs.drug.description', weight: 1 },
                    { name: 'detailedData.prescription_drugs.description', weight: 1 },
                    { name: 'detailedData.prescription_drugs.usage', weight: 1 }
                ],
                threshold: 0.3, // کاهش threshold برای جستجوی دقیق‌تر
                includeScore: true,
                shouldSort: true,
                minMatchCharLength: 2,
                ignoreLocation: true,
                useExtendedSearch: true,
                findAllMatches: true
            };
            
            this.fuse = new Fuse(this.prescriptions, options);
        }
        
        ,
        
        performSearch() {
            if (this.searchQuery.trim() === '') {
                this.applyFilters();
                return;
            }
            
            this.searchLoading = true;
            
            // Debounce search
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                const results = this.fuse.search(this.searchQuery);
                const searchResults = results.map(result => result.item);
                
                // Apply category filter to search results
                if (this.selectedCategories.length > 0) {
                    this.filteredPrescriptions = searchResults.filter(p => 
                        this.selectedCategories.includes(p.category.id)
                    );
                } else {
                    this.filteredPrescriptions = searchResults;
                }
                
                this.currentPage = 1;
                this.searchLoading = false;
            }, 300);
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
            let filtered = [...this.prescriptions];
            
            // Apply category filter
            if (this.selectedCategories.length > 0) {
                filtered = filtered.filter(p => 
                    this.selectedCategories.includes(p.category.id)
                );
            }
            
            // Apply search if exists
            if (this.searchQuery.trim() !== '') {
                const results = this.fuse.search(this.searchQuery);
                const searchIds = results.map(r => r.item.id);
                filtered = filtered.filter(p => searchIds.includes(p.id));
            }
            
            this.filteredPrescriptions = filtered;
            this.currentPage = 1;
        },
        
        goToPage(page) {
            if (page >= 1 && page <= this.totalPages) {
                this.currentPage = page;
                this.loadPrescriptions(page); // بارگذاری صفحه جدید از API
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
