// log and reg

// مدیریت ارتباط با API
const API = {
    BASE_URL: 'http://127.0.0.1:8000/', // آدرس API خودتون
    
    // تنظیمات پیش‌فرض برای درخواست‌ها
    getHeaders(includeAuth = false) {
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (includeAuth) {
            const token = StorageManager.getAccessToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }
        
        return headers;
    },

    // ثبت‌نام کاربر جدید
    async register(userData) {
        try {
            const response = await fetch(`${this.BASE_URL}/api/v1/accounts/register/`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(userData)
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'خطا در ثبت‌نام');
            }
            
            return data;
        } catch (error) {
            console.error('Register error:', error);
            throw error;
        }
    },

    // ورود کاربر
    async login(credentials) {
        try {
            const response = await fetch(`${this.BASE_URL}/api/v1/accounts/login/`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(credentials)
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'خطا در ورود');
            }
            
            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },

    // خروج کاربر (اگر API دارید)
    async logout() {
        // اگر API برای logout دارید، اینجا فراخوانی کنید
        // در غیر این صورت فقط localStorage رو پاک می‌کنیم
        StorageManager.clearAll();
    }
};
