// بررسی دسترسی به صفحات محافظت شده
const ProtectedRoute = {
    // لیست صفحات محافظت شده
    protectedPages: ['/profile', '/premium', '/my-prescriptions'],
    
    // بررسی دسترسی
    checkAccess() {
        const currentPath = window.location.pathname;
        
        if (this.protectedPages.includes(currentPath) && !StorageManager.isLoggedIn()) {
            // ذخیره مسیر فعلی برای redirect بعد از لاگین
            sessionStorage.setItem('redirectAfterLogin', currentPath);
            
            // نمایش پیام و redirect به صفحه اصلی
            alert('برای دسترسی به این صفحه باید وارد شوید.');
            window.location.href = '/';
        }
    },
    
    // redirect بعد از لاگین موفق
    redirectAfterLogin() {
        const redirectPath = sessionStorage.getItem('redirectAfterLogin');
        if (redirectPath) {
            sessionStorage.removeItem('redirectAfterLogin');
            window.location.href = redirectPath;
        }
    }
};

// اجرا در بارگذاری صفحه
document.addEventListener('DOMContentLoaded', () => {
    ProtectedRoute.checkAccess();
});
