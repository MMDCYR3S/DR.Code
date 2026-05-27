// محافظت از صفحات که نیاز به لاگین دارن
console.log('🛡️ Protected.js loading...');

const ProtectedPage = {
    init() {
        // هیچ کاری نکن!
        // این فایل فقط برای صفحاتی هست که میخوای manually چک کنی
        console.log('🛡️ ProtectedPage initialized');
    },

    checkAuth() {
        const isLoggedIn = StorageManager.isLoggedIn();
        console.log('🔒 Checking auth for protected page:', isLoggedIn);
        
        if (!isLoggedIn) {
            console.log('❌ Not logged in, redirecting...');
            window.location.href = '/';
            return false;
        }
        
        return true;
    }
};

console.log('✅ Protected.js loaded');
