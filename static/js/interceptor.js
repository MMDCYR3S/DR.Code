// Axios-like interceptor for native fetch
(function() {
    const originalFetch = window.fetch;
    let isRefreshing = false;
    let failedQueue = [];

    const processQueue = (error, token = null) => {
        failedQueue.forEach(prom => {
            if (error) {
                prom.reject(error);
            } else {
                prom.resolve(token);
            }
        });
        
        failedQueue = [];
    };

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
                if (response.status === 401 && url.includes('/api/') && !url.includes('/token/refresh/')) {
                    
                    if (isRefreshing) {
                        // اگر در حال refresh کردن هستیم، این درخواست رو به صف اضافه کن
                        return new Promise((resolve, reject) => {
                            failedQueue.push({ resolve, reject });
                        }).then(token => {
                            config.headers['Authorization'] = `Bearer ${token}`;
                            return originalFetch(url, config);
                        }).catch(err => {
                            return Promise.reject(err);
                        });
                    }

                    isRefreshing = true;

                    try {
                        // تلاش برای refresh کردن توکن
                        const refreshResult = await API.refreshToken();
                        const newToken = refreshResult.access;
                        
                        // به‌روزرسانی header با توکن جدید
                        config.headers['Authorization'] = `Bearer ${newToken}`;
                        
                        // پردازش صف درخواست‌های معلق
                        processQueue(null, newToken);
                        
                        // تکرار درخواست اصلی با توکن جدید
                        return originalFetch(url, config);
                        
                    } catch (refreshError) {
                        // اگر refresh هم ناموفق بود
                        processQueue(refreshError, null);
                        
                        // پاک کردن داده‌ها و هدایت به صفحه ورود
                        StorageManager.clearAll();
                        
                        if (typeof Auth !== 'undefined' && Auth.updateUIForLoggedOutUser) {
                            Auth.updateUIForLoggedOutUser();
                        }
                        
                        if (typeof Auth !== 'undefined' && Auth.showAuthModal) {
                            Auth.showAuthModal();
                        }
                        
                        throw new Error('نشست شما منقضی شده است. لطفاً دوباره وارد شوید.');
                    } finally {
                        isRefreshing = false;
                    }
                }

                return response;
            });
    };
})();
