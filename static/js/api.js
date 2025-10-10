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
            console.log('Login response data:', data);
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
                try {
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
                } catch (apiError) {
                    console.error('Logout API error:', apiError);
                    // در صورت خطا در تماس با API هم داده‌ها پاک شوند
                }
            }
        } catch (error) {
            console.error('General logout error:', error);
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
    },
    // Get prescription detail by slug
    async getDetail(slug) {
        try {
            const response = await axios.get(
                `${API.BASE_URL}api/v1/prescriptions/${slug}/`,
                {
                    headers: API.getHeaders(true) // با توکن احراز هویت
                }
            );
            return response.data;
        } catch (error) {
            console.error('Error fetching prescription detail:', error);
            throw error;
        }
    },

    // Get prescription description (HTML content)
    async getDescription(slug) {
        try {
            const response = await axios.get(
                `${API.BASE_URL}api/v1/prescriptions/${slug}/description/`,
                {
                    headers: API.getHeaders(true)
                }
            );
            return response.data;
        } catch (error) {
            console.error('Error fetching prescription description:', error);
            throw error;
        }
    },

    // Save/Unsave prescription to favorites
    async toggleSave(slug) {
        try {
            const response = await axios.post(
                `${API.BASE_URL}api/v1/accounts/profile/prescription/save/${slug}/`,
                {},
                {
                    headers: API.getHeaders(true)
                }
            );
            return response.data;
        } catch (error) {
            console.error('Error toggling save prescription:', error);
            throw error;
        }
    },

    // Submit question for premium users (برای آینده)
    async submitQuestion(slug, questionText) {
        try {
            const userData = StorageManager.getUserData();
            const response = await axios.post(
                `${API.BASE_URL}api/v1/prescriptions/${slug}/question/`, // URL فرضی
                {
                    question: questionText,
                    user_id: userData?.user_id,
                    prescription_slug: slug
                },
                {
                    headers: API.getHeaders(true)
                }
            );
            return response.data;
        } catch (error) {
            console.error('Error submitting question:', error);
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


// profile prescription saved
// Saved Prescriptions API
API.savedPrescriptions = {
    // Get saved prescriptions with pagination
    async getSaved(page = 1) {
        try {
            const token = StorageManager.getAccessToken();
            if (!token) {
                throw new Error('لطفاً ابتدا وارد حساب کاربری خود شوید');
            }

            const url = `${API.BASE_URL}api/v1/accounts/profile/saved/${page > 1 ? '?page=' + page : ''}`;
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در دریافت نسخه‌های ذخیره شده');
            }

            return data;
        } catch (error) {
            console.error('Error fetching saved prescriptions:', error);
            throw error;
        }
    }
};

// از اینجا به بعد چیزی تو کنس.ل اجرا نمیشه
// Test function for console
async function testSavedPrescriptionsAPI() {
    console.log('🧪 Testing Saved Prescriptions API...\n');
    
    try {
        // Test: Get first page
        console.log('📄 Test 1: Getting first page of saved prescriptions...');
        const page1 = await API.savedPrescriptions.getSaved(1);
        console.log('✅ Success! Response:', page1);
        console.log('📊 Total Count:', page1.count);
        console.log('📄 Total Pages:', page1.total_pages);
        console.log('📍 Current Page:', page1.current_page);
        console.log('📦 Page Size:', page1.page_size);
        console.log('📋 Results:', page1.results);
        
        if (page1.results.length > 0) {
            console.log('\n🔍 First prescription details:');
            console.log('  - Title:', page1.results[0].title);
            console.log('  - Category:', page1.results[0].category_title);
            console.log('  - Access Level:', page1.results[0].access_level);
            console.log('  - Detail URL:', page1.results[0].detail_url);
        }

        // Test: Get second page if exists
        if (page1.next) {
            console.log('\n📄 Test 2: Getting second page...');
            const page2 = await API.savedPrescriptions.getSaved(2);
            console.log('✅ Success! Page 2 Response:', page2);
        } else {
            console.log('\n📄 Test 2: No second page available (only one page of results)');
        }

    } catch (error) {
        console.error('❌ Test Failed:', error.message);
        console.error('Error details:', error);
    }
}

// Call test on page load (برای تست - بعداً حذف کن)
// test function
// testSavedPrescriptionsAPI();





// Test function for prescription detail APIs
async function testPrescriptionDetailAPI() {
    console.log('🧪 Testing Prescription Detail APIs...\n');

    const testSlug = 'khwb'; // از JSON شما

    try {
        // Test 1: Get Detail
        console.log('📝 Test 1: Get Prescription Detail');
        const detail = await API.prescriptions.getDetail(testSlug);
        console.log('✅ Detail Response:', detail);
        console.log('   - Title:', detail.title);
        console.log('   - Category:', detail.category.title);
        console.log('   - Access Level:', detail.access_level);
        console.log('   - Total Drugs:', detail.prescription_drugs.length);
        
        // بررسی گروه‌بندی داروها
        const combinationDrugs = detail.prescription_drugs.filter(d => d.is_combination);
        const substituteDrugs = detail.prescription_drugs.filter(d => d.is_substitute);
        console.log('   - Combination Drugs:', combinationDrugs.length);
        console.log('   - Substitute Drugs:', substituteDrugs.length);

        // Test 2: Get Description
        console.log('\n📝 Test 2: Get Prescription Description');
        const description = await API.prescriptions.getDescription(testSlug);
        console.log('✅ Description Response:', description);

        // Test 3: Toggle Save (نیاز به لاگین دارد)
        if (StorageManager.isLoggedIn()) {
            console.log('\n📝 Test 3: Toggle Save Prescription');
            const saveResult = await API.prescriptions.toggleSave(testSlug);
            console.log('✅ Save Result:', saveResult);
        } else {
            console.log('\n⚠️  Test 3 Skipped: User not logged in');
        }

        console.log('\n✅ All tests passed!');
    } catch (error) {
        console.error('❌ Test failed:', error);
        if (error.response) {
            console.error('   Response:', error.response.data);
        }
    }
}

// برای تست در کنسول
//  test function
testPrescriptionDetailAPI();
