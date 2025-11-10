// مدیریت لوکال استوریج
console.log('📦 Storage.js loading...');

const StorageManager = {
    KEYS: {
        ACCESS_TOKEN: 'drcode_access_token',
        REFRESH_TOKEN: 'drcode_refresh_token',
        USER_DATA: 'drcode_user_data',
        USER_PROFILE: 'drcode_user_profile',
        USER_JTI: 'drcode_user_jti',
    },

    saveTokens(tokens) {
        console.log('💾 Saving tokens');
        if (tokens.access_token || tokens.access) {
            localStorage.setItem(this.KEYS.ACCESS_TOKEN, tokens.access_token || tokens.access);
        }
        if (tokens.refresh_token || tokens.refresh) {
            localStorage.setItem(this.KEYS.REFRESH_TOKEN, tokens.refresh_token || tokens.refresh);
        }
        if (tokens.jti || tokens.active_jti) {
            localStorage.setItem(this.KEYS.USER_JTI, tokens.jti || tokens.active_jti);
        }
    },

    saveUserData(userData) {
        localStorage.setItem(this.KEYS.USER_DATA, JSON.stringify(userData));
    },

    saveUserProfile(profile) {
        localStorage.setItem(this.KEYS.USER_PROFILE, JSON.stringify(profile));
    },


    getAccessToken() {
        return localStorage.getItem(this.KEYS.ACCESS_TOKEN);
    },

    getRefreshToken() {
        return localStorage.getItem(this.KEYS.REFRESH_TOKEN);
    },

    getTokens() {
        return {
            access_token: this.getAccessToken(),
            refresh_token: this.getRefreshToken()
        };
    },

    getUserData() {
        const data = localStorage.getItem(this.KEYS.USER_DATA);
        return data ? JSON.parse(data) : null;
    },

// ✨ فقط این متد رو عوض کن
async getUserProfile() {
    try {
        const token = this.getAccessToken();
        
        if (!token) {
            console.log('❌ No token, reading from localStorage');
            const profile = localStorage.getItem(this.KEYS.USER_PROFILE);
            return profile ? JSON.parse(profile) : null;
        }

        console.log('🌐 Fetching profile from API...');
        
        const response = await fetch('http://127.0.0.1:8000/api/v1/accounts/profile/', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            console.error('❌ API Error:', response.status);
            const profile = localStorage.getItem(this.KEYS.USER_PROFILE);
            return profile ? JSON.parse(profile) : null;
        }

        const profileData = await response.json();
        console.log('✅ Profile from API:', profileData);

        // ذخیره در localStorage
        this.saveUserProfile(profileData);

        return profileData;

    } catch (error) {
        console.error('❌ Error:', error);
        const profile = localStorage.getItem(this.KEYS.USER_PROFILE);
        return profile ? JSON.parse(profile) : null;
    }
},


    isLoggedIn() {
        const hasToken = !!this.getAccessToken();
        console.log('🔐 isLoggedIn check:', hasToken);
        return hasToken;
    },

    clearAll() {
        console.log('🗑️ Clearing all storage');
        Object.values(this.KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
    }
};

console.log('✅ Storage.js loaded');
