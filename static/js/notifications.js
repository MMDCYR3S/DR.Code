// مدیریت صفحه نوتیفیکیشن‌ها

function notificationsApp() {
    return {
        // State
        notifications: [],
        loading: true,
        pageLoading: false,
        totalCount: 0,
        unreadCount: 0,
        nextPage: null,
        previousPage: null,
        currentPage: 1,

        // Initialize
        async init() {

            // چک کردن لاگین
            if (!StorageManager.isLoggedIn()) {
                window.location.href = '/';
                return;
            }

            await this.loadNotifications();
        },

        async loadNotifications(url = null) {
            try {
                this.loading = !url;
                this.pageLoading = !!url;


                const response = await API.notifications.getNotifications(url);

                if (response.success) {
                    // اصلاح مسیر دریافت داده‌ها بر اساس ساختار جدید API
                    // قبلاً: response.data.results
                    // الان: response.data.notifications
                    this.notifications = response.data.notifications || response.data.results || [];
                    
                    this.totalCount = response.data.total_count || 0; // اصلاح نام فیلد
                    
                    // این فیلدها ممکن است در پاسخ جدید نباشند، اگر پیجینیشن ندارید null بگذارید
                    this.nextPage = response.data.next || null;
                    this.previousPage = response.data.previous || null;
                    
                    // اصلاح دریافت تعداد خوانده نشده (مستقیم از سرور)
                    // قبلاً: محاسبه دستی با filter
                    // الان: response.data.unread_count
                    this.unreadCount = response.data.unread_count || 0;

                    // محاسبه شماره صفحه
                    if (url) {
                        const urlParams = new URLSearchParams(url.split('?')[1]);
                        this.currentPage = parseInt(urlParams.get('page') || '1');
                    } else {
                        this.currentPage = 1;
                    }

                } else {
                    throw new Error(response.message);
                }

            } catch (error) {
                console.error('❌ Error loading notifications:', error);
                
                await Swal.fire({
                    icon: 'error',
                    title: 'خطا در بارگذاری',
                    text: error.message || 'لطفاً دوباره تلاش کنید',
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#0077b6'
                });

            } finally {
                this.loading = false;
                this.pageLoading = false;
            }
        },

        // Mark as Read
        async markAsRead(notification) {
            if (notification.is_read) {
                // اگه خوانده شده، فقط اسکرول به نسخه
                return;
            }

            try {

                const response = await API.notifications.markAsRead(notification.id);

                if (response.success) {
                    // به‌روزرسانی state
                    notification.is_read = true;
                    this.unreadCount = Math.max(0, this.unreadCount - 1);


                    // نمایش پیام موفقیت (اختیاری)
                    const Toast = Swal.mixin({
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false,
                        timer: 2000,
                        timerProgressBar: true
                    });

                    Toast.fire({
                        icon: 'success',
                        title: 'علامت به عنوان خوانده شده زده شد'
                    });

                } else {
                    throw new Error(response.message);
                }

            } catch (error) {
                console.error('❌ Error marking as read:', error);
                
                await Swal.fire({
                    icon: 'error',
                    title: 'خطا',
                    text: error.message || 'لطفاً دوباره تلاش کنید',
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#0077b6'
                });
            }
        },

        // Mark All as Read
        async markAllAsRead() {
            try {
                const result = await Swal.fire({
                    icon: 'question',
                    title: 'علامت همه به عنوان خوانده شده؟',
                    text: `${this.unreadCount} اعلان خوانده نشده دارید`,
                    showCancelButton: true,
                    confirmButtonText: 'بله',
                    cancelButtonText: 'خیر',
                    confirmButtonColor: '#0077b6',
                    cancelButtonColor: '#6b7280'
                });

                if (!result.isConfirmed) return;


                // فیلتر نوتیف‌های خوانده نشده
                const unreadNotifications = this.notifications.filter(n => !n.is_read);

                // ارسال درخواست برای همه
                const promises = unreadNotifications.map(notification => 
                    API.notifications.markAsRead(notification.id)
                );

                await Promise.all(promises);

                // به‌روزرسانی state
                this.notifications.forEach(n => n.is_read = true);
                this.unreadCount = 0;


                await Swal.fire({
                    icon: 'success',
                    title: 'انجام شد',
                    text: 'همه اعلان‌ها خوانده شدند',
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#0077b6',
                    timer: 2000
                });

            } catch (error) {
                console.error('❌ Error marking all as read:', error);
                
                await Swal.fire({
                    icon: 'error',
                    title: 'خطا',
                    text: 'لطفاً دوباره تلاش کنید',
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#0077b6'
                });
            }
        }
    };
}

// اجرای app وقتی صفحه لود شد
document.addEventListener('DOMContentLoaded', () => {
    
    if (window.location.pathname.includes('/notifications')) {
    }
});

