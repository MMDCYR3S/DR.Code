/**
 * ╔════════════════════════════════════════════════════════════════╗
 * ║  📋 Prescription Detail Page - Alpine.js Component            ║
 * ║  دکتر کد - صفحه جزئیات نسخه                                  ║
 * ║  نسخه: 2.0 - بهینه‌سازی شده                                  ║
 * ╚════════════════════════════════════════════════════════════════╝
 */

function prescriptionDetailApp() {
    return {
        // ═══════════════════════════════════════════════════════════
        // 📊 STATE MANAGEMENT
        // ═══════════════════════════════════════════════════════════
        
        // Core Data
        prescription: null,
        loading: true,
        error: false,
        errorMessage: '',
        slug: '',

        // User & Access
        isPremiumUser: false,
        isBookmarked: false,

        // Modals & UI States
        descriptionModalOpen: false,
        descriptionLoading: false,
        detailedDescription: null,
        
        galleryOpen: false,
        currentImageIndex: 0,

        // Q&A Form
        questionText: '',
        questionSubmitting: false,

        // ═══════════════════════════════════════════════════════════
        // 🚀 LIFECYCLE & INITIALIZATION
        // ═══════════════════════════════════════════════════════════

        async init() {
            console.log('🎬 Initializing Prescription Detail App...');

            // Extract slug from URL
            this.slug = this.getSlugFromURL();

            if (!this.slug) {
                this.showError('نسخه مورد نظر یافت نشد');
                return;
            }

            // Check user premium status
            this.checkUserPremiumStatus();

            // Load prescription data
            await this.loadPrescription();

            // Check bookmark status
            this.checkBookmarkStatus();

            // Initialize AOS animations
            this.initAnimations();

            console.log('✅ App initialized successfully');
        },

        /**
         * Extract slug from current URL path
         * URL format: /prescriptions/{slug}/
         */
        getSlugFromURL() {
            const path = window.location.pathname;
            const parts = path.split('/').filter(p => p);
            
            if (parts.length >= 2 && parts[0] === 'prescriptions') {
                return parts[1];
            }
            
            console.warn('⚠️ Could not extract slug from URL:', path);
            return null;
        },

        /**
         * Check if current user has premium access
         */
        checkUserPremiumStatus() {
            const profile = StorageManager.getUserProfile();
            this.isPremiumUser = ['premium', 'doctor'].includes(profile?.role);
            
            console.log('👤 User Premium Status:', this.isPremiumUser);
        },

        /**
         * Initialize AOS animations if library is loaded
         */
        initAnimations() {
            if (typeof AOS !== 'undefined') {
                AOS.init({
                    duration: 600,
                    once: true,
                    offset: 100,
                    easing: 'ease-in-out'
                });
                console.log('✨ AOS animations initialized');
            }
        },

        // ═══════════════════════════════════════════════════════════
        // 📡 API & DATA LOADING
        // ═══════════════════════════════════════════════════════════

        /**
         * Load prescription data from API
         * Maps prescription_drugs to medications for consistency
         */
        async loadPrescription() {
            try {
                this.loading = true;
                this.error = false;

                console.log('📡 Fetching prescription:', this.slug);

                const response = await axios.get(
                    `${API.BASE_URL}api/v1/prescriptions/${this.slug}/`
                );

                this.prescription = response.data;

                // 🔥 Map prescription_drugs to medications
                this.prescription.medications = this.mapPrescriptionDrugs(
                    this.prescription.prescription_drugs
                );

                console.log('✅ Prescription loaded:', this.prescription);
                console.log('💊 Medications count:', this.prescription.medications?.length || 0);

                // Update page title
                this.updatePageTitle(this.prescription.title);

            } catch (error) {
                console.error('❌ Error loading prescription:', error);
                this.handleLoadError(error);

            } finally {
                this.loading = false;
            }
        },

        /**
         * Map prescription_drugs array to medications format
         * Ensures compatibility with frontend expectations
         */
        mapPrescriptionDrugs(prescriptionDrugs) {
            if (!prescriptionDrugs || !Array.isArray(prescriptionDrugs)) {
                console.warn('⚠️ No prescription_drugs found');
                return [];
            }

            return prescriptionDrugs.map((item, index) => ({
                // Core fields
                id: item.drug.code || `drug-${index}`,
                drug_name: item.drug.title || 'نامشخص',
                drug_code: item.drug.code || '-',
                
                // Dosage & instructions
                dosage: item.dosage || '-',
                frequency: item.instructions || '-',
                quantity: item.amount || 0,
                notes: item.instructions || '',
                
                // Flags
                is_combination: item.is_combination || false,
                order: item.order || index + 1,
                
                // Keep original data for debugging
                _raw: item
            }));
        },

        /**
         * Handle API errors gracefully
         */
        handleLoadError(error) {
            this.error = true;

            if (error.response) {
                const status = error.response.status;
                
                const errorMessages = {
                    404: 'نسخه مورد نظر یافت نشد',
                    403: 'شما به این نسخه دسترسی ندارید',
                    401: 'لطفاً وارد حساب کاربری خود شوید',
                    500: 'خطای سرور - لطفاً بعداً تلاش کنید',
                    default: 'خطا در بارگذاری اطلاعات نسخه'
                };

                this.errorMessage = errorMessages[status] || errorMessages.default;
            } else if (error.request) {
                this.errorMessage = 'خطا در ارتباط با سرور - اتصال اینترنت خود را بررسی کنید';
            } else {
                this.errorMessage = 'خطای نامشخص در بارگذاری داده‌ها';
            }
        },

        /**
         * Update document title
         */
        updatePageTitle(title) {
            document.title = `${title} - دکتر کد`;
        },

        /**
         * Show error state
         */
        showError(message) {
            this.error = true;
            this.errorMessage = message;
            this.loading = false;
        },

        // ═══════════════════════════════════════════════════════════
        // 📋 CLIPBOARD & COPY FUNCTIONALITY
        // ═══════════════════════════════════════════════════════════

        /**
         * Copy drug code to clipboard with visual feedback
         */
        async copyDrugCode(code) {
            if (!code || code === '-') {
                this.showToast('error', 'کد دارو موجود نیست');
                return;
            }

            try {
                await navigator.clipboard.writeText(code);
                
                this.showToast('success', 'کد دارو کپی شد', code);
                
                console.log('📋 Copied to clipboard:', code);

            } catch (error) {
                console.error('❌ Copy failed:', error);
                
                // Fallback for older browsers
                this.fallbackCopy(code);
            }
        },

        /**
         * Fallback copy method for browsers without clipboard API
         */
        fallbackCopy(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                document.execCommand('copy');
                this.showToast('success', 'کد دارو کپی شد', text);
            } catch (error) {
                this.showToast('error', 'خطا در کپی کردن');
            } finally {
                document.body.removeChild(textArea);
            }
        },

        // ═══════════════════════════════════════════════════════════
        // 📖 DESCRIPTION MODAL
        // ═══════════════════════════════════════════════════════════

        /**
         * Open detailed description modal
         * Loads content from API if not already loaded
         */
        async openDescriptionModal() {
            this.descriptionModalOpen = true;

            // Already loaded - skip API call
            if (this.detailedDescription) {
                return;
            }

            try {
                this.descriptionLoading = true;

                console.log('📡 Fetching detailed description...');

                const response = await axios.get(
                    `${API.BASE_URL}api/v1/prescriptions/${this.slug}/description/`
                );

                this.detailedDescription = response.data.detailed_description || 
                    '<p class="text-gray-500">توضیحات تکمیلی در دسترس نیست</p>';

                console.log('✅ Description loaded');

            } catch (error) {
                console.error('❌ Error loading description:', error);
                
                this.detailedDescription = 
                    '<p class="text-red-500">خطا در بارگذاری توضیحات - لطفاً دوباره تلاش کنید</p>';

            } finally {
                this.descriptionLoading = false;
            }
        },

        // ═══════════════════════════════════════════════════════════
        // 🖼️ IMAGE GALLERY
        // ═══════════════════════════════════════════════════════════

        /**
         * Open image gallery at specific index
         */
        openImageGallery(index) {
            if (!this.prescription?.images?.length) {
                console.warn('⚠️ No images available');
                return;
            }

            this.currentImageIndex = index;
            this.galleryOpen = true;
            
            // Prevent body scroll when gallery is open
            document.body.style.overflow = 'hidden';
            
            console.log('🖼️ Gallery opened at index:', index);
        },

        /**
         * Close image gallery
         */
        closeImageGallery() {
            this.galleryOpen = false;
            
            // Restore body scroll
            document.body.style.overflow = '';
            
            console.log('🖼️ Gallery closed');
        },

        /**
         * Navigate to next image
         */
        nextImage() {
            const totalImages = this.prescription.images.length;
            
            if (this.currentImageIndex < totalImages - 1) {
                this.currentImageIndex++;
            } else {
                this.currentImageIndex = 0; // Loop to first
            }
        },

        /**
         * Navigate to previous image
         */
        previousImage() {
            const totalImages = this.prescription.images.length;
            
            if (this.currentImageIndex > 0) {
                this.currentImageIndex--;
            } else {
                this.currentImageIndex = totalImages - 1; // Loop to last
            }
        },

        /**
         * Keyboard navigation for gallery
         */
        handleGalleryKeyboard(event) {
            if (!this.galleryOpen) return;

            switch(event.key) {
                case 'ArrowRight':
                    this.previousImage(); // RTL layout
                    break;
                case 'ArrowLeft':
                    this.nextImage(); // RTL layout
                    break;
                case 'Escape':
                    this.closeImageGallery();
                    break;
            }
        },

        // ═══════════════════════════════════════════════════════════
        // 🔖 BOOKMARK FUNCTIONALITY
        // ═══════════════════════════════════════════════════════════

        /**
         * Check if prescription is bookmarked
         * Currently uses localStorage - ready for API integration
         */
        checkBookmarkStatus() {
            try {
                const bookmarks = JSON.parse(
                    localStorage.getItem('bookmarkedPrescriptions') || '[]'
                );
                
                this.isBookmarked = bookmarks.includes(this.prescription?.id);
                
                console.log('🔖 Bookmark status:', this.isBookmarked);
            } catch (error) {
                console.error('❌ Error checking bookmark:', error);
                this.isBookmarked = false;
            }
        },

        /**
         * Toggle bookmark status
         * Shows login prompt if user not authenticated
         */
        async toggleBookmark() {
            const profile = StorageManager.getUserProfile();

            // Require authentication
            if (!profile) {
                this.promptLogin('ذخیره نسخه');
                return;
            }

            // Toggle state
            this.isBookmarked = !this.isBookmarked;

            // Update localStorage (temporary - replace with API)
            this.updateLocalBookmarks();

            // Show feedback
            this.showToast(
                'success',
                this.isBookmarked ? '🔖 نسخه ذخیره شد' : 'نسخه از ذخیره‌ها حذف شد'
            );

            // TODO: Replace with API call
            // await this.syncBookmarkWithAPI();
        },

        /**
         * Update bookmarks in localStorage
         */
        updateLocalBookmarks() {
            try {
                let bookmarks = JSON.parse(
                    localStorage.getItem('bookmarkedPrescriptions') || '[]'
                );

                if (this.isBookmarked) {
                    if (!bookmarks.includes(this.prescription.id)) {
                        bookmarks.push(this.prescription.id);
                    }
                } else {
                    bookmarks = bookmarks.filter(id => id !== this.prescription.id);
                }

                localStorage.setItem('bookmarkedPrescriptions', JSON.stringify(bookmarks));
                
                console.log('💾 Bookmarks updated:', bookmarks);
            } catch (error) {
                console.error('❌ Error updating bookmarks:', error);
            }
        },

        /**
         * 🔧 API Integration Point for Bookmarks
         * Uncomment and customize when backend is ready
         */
        async syncBookmarkWithAPI() {
            /*
            try {
                const token = StorageManager.getAccessToken();
                const url = `${API.BASE_URL}api/v1/users/bookmarks/`;

                if (this.isBookmarked) {
                    // Add bookmark
                    await axios.post(url, {
                        prescription_id: this.prescription.id
                    }, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                } else {
                    // Remove bookmark
                    await axios.delete(`${url}${this.prescription.id}/`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                }

                console.log('✅ Bookmark synced with server');

            } catch (error) {
                console.error('❌ Bookmark sync failed:', error);
                
                // Revert state on error
                this.isBookmarked = !this.isBookmarked;
                this.updateLocalBookmarks();
                
                this.showToast('error', 'خطا در همگام‌سازی - لطفاً دوباره تلاش کنید');
            }
            */
        },

        // ═══════════════════════════════════════════════════════════
        // ❓ Q&A FUNCTIONALITY
        // ═══════════════════════════════════════════════════════════

        /**
         * Submit user question
         * Requires premium access
         */
        async submitQuestion() {
            // Validation
            if (!this.questionText.trim()) {
                this.showToast('warning', 'لطفاً متن سوال را وارد کنید');
                return;
            }

            // Premium check
            if (!this.isPremiumUser) {
                Swal.fire({
                    icon: 'warning',
                    title: '⭐ دسترسی ویژه',
                    html: `
                        <p class="mb-4">این قابلیت فقط برای کاربران ویژه فعال است.</p>
                        <p class="text-sm text-gray-600">با ارتقا به پلن ویژه، از تمام امکانات دکتر کد استفاده کنید.</p>
                    `,
                    showCancelButton: true,
                    confirmButtonText: '🚀 مشاهده پلن‌ها',
                    cancelButtonText: 'انصراف',
                    confirmButtonColor: '#0077b6'
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = '/plan/';
                    }
                });
                return;
            }

            try {
                this.questionSubmitting = true;

                const token = StorageManager.getAccessToken();

                if (!token) {
                    throw new Error('لطفاً وارد حساب کاربری خود شوید');
                }

                console.log('📤 Submitting question...');

                // Submit question via API
                await axios.post(
                    `${API.BASE_URL}api/v1/prescriptions/${this.slug}/questions/`,
                    {
                        question: this.questionText.trim()
                    },
                    {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    }
                );

                // Success feedback
                Swal.fire({
                    icon: 'success',
                    title: '✅ سوال ارسال شد',
                    html: `
                        <p class="mb-2">سوال شما با موفقیت ثبت شد.</p>
                        <p class="text-sm text-gray-600">پاسخ در بخش پروفایل شما قابل مشاهده خواهد بود.</p>
                    `,
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#10b981'
                });

                // Clear form
                this.questionText = '';

                console.log('✅ Question submitted successfully');

            } catch (error) {
                console.error('❌ Error submitting question:', error);

                let errorMsg = 'خطا در ارسال سوال';
                
                if (error.response?.data?.message) {
                    errorMsg = error.response.data.message;
                } else if (error.message) {
                    errorMsg = error.message;
                }

                this.showToast('error', errorMsg);

            } finally {
                this.questionSubmitting = false;
            }
        },

        // ═══════════════════════════════════════════════════════════
        // 🛠️ UTILITY FUNCTIONS
        // ═══════════════════════════════════════════════════════════

        /**
         * Show toast notification
         */
        showToast(type, title, text = '') {
            const icons = {
                success: 'success',
                error: 'error',
                warning: 'warning',
                info: 'info'
            };

            Swal.fire({
                toast: true,
                position: 'top-end',
                icon: icons[type] || 'info',
                title: title,
                text: text,
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true,
                didOpen: (toast) => {
                    toast.addEventListener('mouseenter', Swal.stopTimer);
                    toast.addEventListener('mouseleave', Swal.resumeTimer);
                }
            });
        },

        /**
         * Prompt user to login
         */
        promptLogin(action = 'استفاده از این قابلیت') {
            Swal.fire({
                icon: 'warning',
                title: '🔐 ورود به حساب کاربری',
                html: `
                    <p class="mb-4">برای ${action} ابتدا وارد حساب کاربری خود شوید.</p>
                `,
                showCancelButton: true,
                confirmButtonText: 'ورود',
                cancelButtonText: 'انصراف',
                confirmButtonColor: '#0077b6'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Store return URL
                    sessionStorage.setItem('returnUrl', window.location.pathname);
                    window.location.href = '/login/';
                }
            });
        },

        /**
         * Retry loading prescription
         */
        async retryLoad() {
            console.log('🔄 Retrying load...');
            await this.loadPrescription();
        },

        /**
         * Check if prescription has any media
         */
        hasMedia() {
            return (this.prescription?.images?.length > 0) || 
                   (this.prescription?.videos?.length > 0);
        },

        /**
         * Format date to Persian
         */
        formatDate(dateString) {
            if (!dateString) return '-';
            
            try {
                const date = new Date(dateString);
                return new Intl.DateTimeFormat('fa-IR').format(date);
            } catch (error) {
                console.error('Date format error:', error);
                return dateString;
            }
        }
    };
}

// ═══════════════════════════════════════════════════════════════════
// 🌐 GLOBAL EVENT LISTENERS
// ═══════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 Prescription Detail Page Ready');
    
    // Add keyboard listener for gallery
    document.addEventListener('keydown', (e) => {
        const app = Alpine.$data(document.querySelector('[x-data="prescriptionDetailApp()"]'));
        if (app) {
            app.handleGalleryKeyboard(e);
        }
    });
});
