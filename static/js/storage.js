// مدیریت لوکال استوریج برای لاگین و ثبت نام

// مدیریت ذخیره‌سازی توکن‌ها و اطلاعات کاربر
const StorageManager = {
    // کلیدهای ذخیره‌سازی
    KEYS: {
        ACCESS_TOKEN: 'drcode_access_token',
        REFRESH_TOKEN: 'drcode_refresh_token',
        USER_DATA: 'drcode_user_data',
        USER_PROFILE: 'drcode_user_profile'
    },

    // ذخیره توکن‌ها
    saveTokens(tokens) {
        if (tokens.access_token || tokens.access) {
            localStorage.setItem(this.KEYS.ACCESS_TOKEN, tokens.access_token || tokens.access);
        }
        if (tokens.refresh_token || tokens.refresh) {
            localStorage.setItem(this.KEYS.REFRESH_TOKEN, tokens.refresh_token || tokens.refresh);
        }
    },

    // ذخیره اطلاعات کاربر
    saveUserData(userData) {
        localStorage.setItem(this.KEYS.USER_DATA, JSON.stringify(userData));
    },

    // ذخیره پروفایل کاربر
    saveUserProfile(profile) {
        localStorage.setItem(this.KEYS.USER_PROFILE, JSON.stringify(profile));
    },

    // دریافت Access Token
    getAccessToken() {
        return localStorage.getItem(this.KEYS.ACCESS_TOKEN);
    },

    // دریافت Refresh Token
    getRefreshToken() {
        return localStorage.getItem(this.KEYS.REFRESH_TOKEN);
    },

    // دریافت همه توکن‌ها
    getTokens() {
        return {
            access_token: this.getAccessToken(),
            refresh_token: this.getRefreshToken()
        };
    },

    // دریافت اطلاعات کاربر
    getUserData() {
        const data = localStorage.getItem(this.KEYS.USER_DATA);
        return data ? JSON.parse(data) : null;
    },

    // دریافت پروفایل کاربر
    getUserProfile() {
        const profile = localStorage.getItem(this.KEYS.USER_PROFILE);
        return profile ? JSON.parse(profile) : null;
    },

    // بررسی وضعیت لاگین
    isLoggedIn() {
        return !!this.getAccessToken();
    },

    // پاک کردن همه داده‌ها (لاگ‌اوت)
    clearAll() {
        Object.values(this.KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
    }
};
