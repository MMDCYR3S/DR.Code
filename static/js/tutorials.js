// tutorials.js

// ✅ صبر می‌کنیم تا Alpine کاملاً لود بشه
document.addEventListener('alpine:init', () => {
    Alpine.data('tutorialsApp', () => ({
        // State
        tutorials: [],
        isLoading: true,
        error: null,

        // Initialize
        async init() {
            console.log('🎬 Tutorials App Initialized');
            await this.loadTutorials();
        },

        // Load tutorials from API
        async loadTutorials() {
            this.isLoading = true;
            this.error = null;

            try {
                const response = await API.tutorials.getAll();

                if (response.success) {
                    this.tutorials = response.data;
                    console.log('✅ Tutorials loaded:', this.tutorials.length);
                } else {
                    throw new Error('خطا در دریافت اطلاعات');
                }
            } catch (error) {
                console.error('❌ Error loading tutorials:', error);
                this.error = error.message;

                // نمایش پیام خطا
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'error',
                        title: 'خطا',
                        text: 'خطا در بارگذاری ویدیوها. لطفاً دوباره تلاش کنید.',
                        confirmButtonText: 'باشه'
                    });
                }
            } finally {
                this.isLoading = false;
            }
        },

        // Format date to Persian
        formatDate(dateString) {
            if (!dateString) return 'نامشخص';

            try {
                const date = new Date(dateString);
                const options = {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                };

                return new Intl.DateTimeFormat('fa-IR', options).format(date);
            } catch (error) {
                console.error('Date format error:', error);
                return 'نامشخص';
            }
        },

        // Scroll to FAQ section
        scrollToFAQ() {
            const faqSection = document.getElementById('faq-section');
            if (faqSection) {
                faqSection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
                console.log('📜 Scrolling to FAQ section');
            } else {
                console.warn('⚠️ FAQ section not found');
            }
        }
    }));

    console.log('✅ Alpine.js tutorialsApp component registered');
});

// ✅ بررسی اینکه Alpine لود شده یا نه
console.log('📦 tutorials.js loaded');
