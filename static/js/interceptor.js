// Interceptor for handling token refresh

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

        // فقط برای API هایی که لاگین دارن، توکن اضافه کن
        if (url.includes('/api/') && typeof StorageManager !== 'undefined') {
            const token = StorageManager.getAccessToken();
            if (token) {
                config.headers = {
                    ...config.headers,
                    'Authorization': `Bearer ${token}`
                };
            }
        }

        return originalFetch(url, config)
            .then(async response => {
                // فقط اگه 401 بود و لاگین هستیم، رفرش کن
                if (response.status === 401 && 
                    url.includes('/api/') && 
                    !url.includes('/token/refresh/') &&
                    typeof StorageManager !== 'undefined' &&
                    StorageManager.isLoggedIn() &&
                    StorageManager.getRefreshToken()) {
                    

                    if (isRefreshing) {
                        return new Promise((resolve, reject) => {
                            failedQueue.push({ resolve, reject });
                        }).then(token => {
                            config.headers['Authorization'] = `Bearer ${token}`;
                            return originalFetch(url, config);
                        });
                    }

                    isRefreshing = true;

                    try {
                        const refreshResult = await API.refreshToken();
                        const newToken = refreshResult.access;

                        processQueue(null, newToken);

                        config.headers['Authorization'] = `Bearer ${newToken}`;
                        return originalFetch(url, config);

                    } catch (refreshError) {
                        console.error('❌ Refresh failed:', refreshError);
                        processQueue(refreshError, null);
                        
                        StorageManager.clearAll();
                        
                        // فقط هدایت کن، بدون reload
                        if (window.location.pathname !== '/') {
                            window.location.href = '/';
                        }
                        
                        return response;
                    } finally {
                        isRefreshing = false;
                    }
                }

                return response;
            })
            .catch(error => {
                console.error('🔴 Fetch error:', error);
                throw error;
            });
    };

})();
