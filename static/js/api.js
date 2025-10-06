// log and reg

// مدیریت ارتباط با API
const API = {
    BASE_URL: '/', // آدرس API خودتون

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

    // Refresh Token
    async refreshToken() {
        try {
            const refreshToken = StorageManager.getRefreshToken();
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }

            const response = await fetch(`${this.BASE_URL}api/v1/accounts/token/refresh/`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    refresh: refreshToken
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در تمدید نشست');
            }

            // ذخیره توکن‌های جدید
            StorageManager.saveTokens({
                access: data.access,
                refresh: data.refresh || refreshToken // اگر refresh جدید نداد، همون قدیمی رو نگه دار
            });

            return data;
        } catch (error) {
            console.error('Refresh token error:', error);
            // اگر refresh token هم منقضی شده، کاربر رو لاگ‌اوت کن
            StorageManager.clearAll();
            throw error;
        }
    },

    // ثبت‌نام کاربر جدید
    async register(userData) {
        try {
            const response = await fetch(`${this.BASE_URL}api/v1/accounts/register/`, {
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
            const response = await fetch(`${this.BASE_URL}api/v1/accounts/login/`, {
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

    // خروج کاربر
    async logout() {
        try {
            const tokens = StorageManager.getTokens();

            if (tokens?.access_token) {
                const response = await fetch(`${this.BASE_URL}api/v1/accounts/logout/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${tokens.access_token}`
                    }
                });

                // حتی اگر API ارور داد، باز هم localStorage رو پاک کن
                if (!response.ok) {
                    console.warn('Logout API returned error, but clearing local data anyway');
                }
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // در هر صورت localStorage رو پاک کن
            StorageManager.clearAll();
        }
    }
};

// Prescription APIs
API.prescriptions = {
    // Get all prescriptions
    async getAll(params = {}) {
        try {
            const queryString = new URLSearchParams(params).toString();
            const url = `${API.BASE_URL}api/v1/prescriptions/${queryString ? '?' + queryString : ''}`;

            const response = await axios.get(url);
            return response.data;
        } catch (error) {
            console.error('Error fetching prescriptions:', error);
            throw error;
        }
    },

    // Get prescription detail
    async getDetail(slug) {
        try {
            const response = await axios.get(`${API.BASE_URL}api/v1/prescriptions/${slug}/`);
            return response.data;
        } catch (error) {
            console.error('Error fetching prescription detail:', error);
            throw error;
        }
    }
};


// !!!!!!!!!!!!! profile api

// اضافه کردن به انتهای فایل api.js

// Profile APIs
API.profile = {
    // دریافت اطلاعات پروفایل
    async getProfile() {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/accounts/profile/`, {
                method: 'GET',
                headers: API.getHeaders(true)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در دریافت اطلاعات پروفایل');
            }

            return data;
        } catch (error) {
            console.error('Profile API error:', error);
            throw error;
        }
    },

    // دریافت اطلاعات کامل برای ویرایش
    async getProfileUpdate() {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/accounts/profile/update/`, {
                method: 'GET',
                headers: API.getHeaders(true)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در دریافت اطلاعات ویرایش');
            }

            return data;
        } catch (error) {
            console.error('Profile Update API error:', error);
            throw error;
        }
    },

    // به‌روزرسانی اطلاعات پروفایل
    async updateProfile(profileData) {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/accounts/profile/update/`, {
                method: 'PATCH',
                headers: API.getHeaders(true),
                body: JSON.stringify(profileData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در به‌روزرسانی اطلاعات');
            }

            return data;
        } catch (error) {
            console.error('Profile Update API error:', error);
            throw error;
        }
    }
};
