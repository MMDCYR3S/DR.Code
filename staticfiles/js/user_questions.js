/**
 * User Questions Alpine.js Component
 * نمایش سوالات و پاسخ‌های کاربر با pagination
 */

function userQuestionsApp() {
    return {
        // Data
        questions: [],
        selectedQuestion: null,
        loading: true,
        showModal: false,
        
        // Pagination
        currentPage: 1,
        totalPages: 1,
        totalCount: 0,
        nextUrl: null,
        prevUrl: null,

        /**
         * Initialize component
         */
        async init() {
            console.log('🚀 User Questions App Initialized');
            
            // بررسی لاگین بودن
            if (!StorageManager.isLoggedIn()) {
                Swal.fire({
                    icon: 'warning',
                    title: 'لطفاً وارد شوید',
                    text: 'برای مشاهده سوالات باید وارد حساب کاربری خود شوید',
                    confirmButtonText: 'ورود',
                    confirmButtonColor: '#0077b6'
                }).then(() => {
                    window.location.href = '/login';
                });
                return;
            }

            await this.loadQuestions(1);
        },

        /**
         * بارگذاری سوالات
         * @param {number} page - شماره صفحه
         */
        async loadQuestions(page = 1) {
            try {
                this.loading = true;
                
                const response = await API.userQuestions.getQuestions(page);
                
                this.questions = response.results || [];
                this.totalCount = response.count || 0;
                this.currentPage = page;
                this.nextUrl = response.next;
                this.prevUrl = response.previous;
                
                // محاسبه تعداد صفحات
                const pageSize = response.results?.length || 10;
                this.totalPages = Math.ceil(this.totalCount / pageSize);

                console.log('✅ Questions loaded:', {
                    total: this.totalCount,
                    page: this.currentPage,
                    pages: this.totalPages
                });

            } catch (error) {
                console.error('❌ Error loading questions:', error);
                
                Swal.fire({
                    icon: 'error',
                    title: 'خطا',
                    text: error.message || "اره",
                    confirmButtonText: 'تلاش مجدد',
                    backButtonText: "بازگشت",
                    confirmButtonColor: '#0077b6'
                }).then((result) => {
                    if (result.isConfirmed) {
                        this.loadQuestions(page);
                    }
                });
            } finally {
                this.loading = false;
            }
        },

        /**
         * بارگذاری صفحه خاص
         * @param {number} page - شماره صفحه
         */
        async loadPage(page) {
            if (page < 1 || page > this.totalPages) return;
            
            // اسکرول به بالا
            window.scrollTo({ top: 0, behavior: 'smooth' });
            
            await this.loadQuestions(page);
        },

        /**
         * باز کردن مودال جزئیات
         * @param {object} question - اطلاعات سوال
         */
        openModal(question) {
            this.selectedQuestion = question;
            this.showModal = true;
            
            // جلوگیری از اسکرول بدنه
            document.body.style.overflow = 'hidden';
            
            console.log('📖 Modal opened for question:', question.question_text);
        },

        /**
         * بستن مودال
         */
        closeModal() {
            this.showModal = false;
            this.selectedQuestion = null;
            
            // بازگشت اسکرول بدنه
            document.body.style.overflow = 'auto';
        },

        /**
         * کوتاه کردن متن
         * @param {string} text - متن اصلی
         * @param {number} maxLength - حداکثر طول
         * @returns {string}
         */
        truncateText(text, maxLength = 100) {
            if (!text) return '-';
            if (text.length <= maxLength) return text;
            return text.substring(0, maxLength) + '...';
        },

        /**
         * فرمت تاریخ کوتاه
         * @param {string} dateString - رشته تاریخ ISO
         * @returns {string}
         */
        formatDate(dateString) {
            if (!dateString) return '-';
            
            try {
                const date = new Date(dateString);
                const now = new Date();
                const diffTime = Math.abs(now - date);
                const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
                
                if (diffDays === 0) {
                    return 'امروز';
                } else if (diffDays === 1) {
                    return 'دیروز';
                } else if (diffDays < 7) {
                    return `${diffDays} روز پیش`;
                } else if (diffDays < 30) {
                    const weeks = Math.floor(diffDays / 7);
                    return `${weeks} هفته پیش`;
                } else if (diffDays < 365) {
                    const months = Math.floor(diffDays / 30);
                    return `${months} ماه پیش`;
                } else {
                    const years = Math.floor(diffDays / 365);
                    return `${years} سال پیش`;
                }
            } catch (error) {
                console.error('Error formatting date:', error);
                return '-';
            }
        },

        /**
         * فرمت تاریخ کامل
         * @param {string} dateString - رشته تاریخ ISO
         * @returns {string}
         */
        formatDateFull(dateString) {
            if (!dateString) return '-';
            
            try {
                const date = new Date(dateString);
                
                const options = {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                };
                
                return new Intl.DateTimeFormat('fa-IR', options).format(date);
            } catch (error) {
                console.error('Error formatting date:', error);
                return '-';
            }
        }
    };
}
