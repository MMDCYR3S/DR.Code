// Axios-like interceptor for native fetch
(function() {
    const originalFetch = window.fetch;
    
    window.fetch = function(...args) {
        let [url, config = {}] = args;
        
        // اضافه کردن توکن به همه درخواست‌های API
        if (url.includes('/api/') && StorageManager.isLoggedIn()) {
            config.headers = {
                ...config.headers,
                'Authorization': `Bearer ${StorageManager.getAccessToken()}`
            };
        }
        
        return originalFetch(url, config)
            .then(async response => {
                // Handle 401 errors
                if (response.status === 401) {
                    // توکن منقضی شده، کاربر رو لاگ‌اوت کن
                    StorageManager.clearAll();
                    Auth.updateUIForLoggedOutUser();
                    Auth.showAuthModal();
                    throw new Error('نشست شما منقضی شده است. لطفاً دوباره وارد شوید.');
                }
                
                return response;
            });
    };
})();
