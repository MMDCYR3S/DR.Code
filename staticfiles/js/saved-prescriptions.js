// Alpine.js Component for Saved Prescriptions Page
function savedPrescriptionsApp() {
    return {
        // State
        prescriptions: [],
        loading: true,
        error: null,
        currentPage: 1,
        totalPages: 1,
        totalCount: 0,
        pageSize: 10,
        nextPage: null,
        previousPage: null,

        // Computed
        get hasResults() {
            return this.prescriptions.length > 0;
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
            console.log('🚀 Initializing Saved Prescriptions Page...');
            await this.loadSavedPrescriptions(1);
        },

        async loadSavedPrescriptions(page = 1) {
            try {
                this.loading = true;
                this.error = null;

                console.log(`📄 Loading page ${page}...`);
                
                const response = await API.savedPrescriptions.getSaved(page);
                
                console.log('✅ API Response:', response);
                console.log('📊 Pagination Info:', {
                    count: response.count,
                    total_pages: response.total_pages,
                    current_page: response.current_page,
                    page_size: response.page_size
                });
                console.log('📋 Results:', response.results);

                // Update state
                this.prescriptions = response.results || [];
                this.totalCount = response.count || 0;
                this.totalPages = response.total_pages || 1;
                this.currentPage = response.current_page || 1;
                this.pageSize = response.page_size || 10;
                this.nextPage = response.next;
                this.previousPage = response.previous;

                // Scroll to top
                window.scrollTo({ top: 0, behavior: 'smooth' });

            } catch (error) {
                console.error('❌ Error loading saved prescriptions:', error);
                this.error = error.message || 'خطا در بارگذاری نسخه‌های ذخیره شده';
                
                // Show SweetAlert
                Swal.fire({
                    icon: 'error',
                    title: 'خطا',
                    text: this.error,
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#0077b6'
                });
            } finally {
                this.loading = false;
            }
        },

        goToPage(page) {
            if (page >= 1 && page <= this.totalPages && page !== this.currentPage) {
                this.loadSavedPrescriptions(page);
            }
        },

        goToNextPage() {
            if (this.nextPage) {
                this.goToPage(this.currentPage + 1);
            }
        },

        goToPreviousPage() {
            if (this.previousPage) {
                this.goToPage(this.currentPage - 1);
            }
        },

        handlePrescriptionClick(prescription) {
            console.log('🔗 Navigating to prescription:', prescription.title);
            // Navigate to detail page using slug
            window.location.href = `/prescriptions/${prescription.slug}/`;
        },

        getAccessLevelBadge(accessLevel) {
            return accessLevel === 'PREMIUM' 
                ? { color: 'bg-gradient-to-r from-yellow-400 to-yellow-600', icon: 'fas fa-crown', text: 'ویژه' }
                : { color: 'bg-gradient-to-r from-green-400 to-green-600', icon: 'fas fa-check-circle', text: 'رایگان' };
        }
    };
}
