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

      // 🆕 اضافه کن
      getAuthHeaders() {
        const token = StorageManager.getAccessToken();
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        };
    },
    
     // 🆕 اضافه کن
     handleError(error) {
        console.error('🔴 API Error:', error);
        
        let message = 'خطای ناشناخته رخ داد';
        
        if (error.response) {
            // خطای از سمت سرور
            message = error.response.data?.message || error.response.data?.detail || 'خطا در ارتباط با سرور';
        } else if (error.request) {
            // درخواست ارسال شد ولی پاسخی نیومد
            message = 'خطا در ارتباط با سرور. لطفاً اتصال اینترنت خود را بررسی کنید';
        } else {
            // خطای دیگر
            message = error.message || 'خطای ناشناخته';
        }

        return {
            success: false,
            message: message,
            error: error
        };
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
    },
        // Notifications API
        notifications: {
            // دریافت لیست نوتیفیکیشن‌ها
            async getNotifications(url = null) {
                try {
                    const endpoint = url || `${API.BASE_URL}api/v1/notifications/user/`;
                    
                    console.log('📡 GET:', endpoint);
    
                    const response = await axios.get(endpoint, {
                        headers: API.getAuthHeaders()
                    });
    
                    console.log('✅ Notifications response:', response.data);
    
                    return {
                        success: true,
                        data: response.data
                    };
    
                } catch (error) {
                    console.error('❌ Notifications error:', error);
                    return API.handleError(error);
                }
            },
    
            // علامت زدن به عنوان خوانده شده
            async markAsRead(notificationId) {
                try {
                    const url = `${API.BASE_URL}api/v1/notifications/user/${notificationId}/`;
                    
                    console.log('📡 POST:', url);
    
                    const response = await axios.post(url, {}, {
                        headers: API.getAuthHeaders()
                    });
    
                    console.log('✅ Mark as read response:', response.data);
    
                    return {
                        success: true,
                        data: response.data
                    };
    
                } catch (error) {
                    console.error('❌ Mark as read error:', error);
                    return API.handleError(error);
                }
            }
        },
    
            // Plans API
    plans: {
        // دریافت لیست پلن‌ها
        async getPlans() {
            try {
                const url = `${API.BASE_URL}api/v1/subscriptions/plan/`;
                
                console.log('📡 GET:', url);

                const response = await axios.get(url);

                console.log('✅ Plans response:', response.data);

                return {
                    success: true,
                    data: response.data
                };

            } catch (error) {
                console.error('❌ Plans error:', error);
                return API.handleError(error);
            }
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

    // // Get prescription detail
    // async getDetail(slug) {
    //     try {
    //         const response = await axios.get(`${API.BASE_URL}api/v1/prescriptions/${slug}/`);
    //         return response.data;
    //     } catch (error) {
    //         console.error('Error fetching prescription detail:', error);
    //         throw error;
    //     }
    // },
    // Get prescription detail by slug
    async getDetail(slug) {
        try {
            const response = await axios.get(
                `${API.BASE_URL}api/v1/prescriptions/${slug}/`,
                {
                    headers: API.getHeaders(true) // با توکن احراز هویت
                }
            );
            console.log(response.data.description);
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
                `${API.BASE_URL}api/v1/prescriptions/${slug}`,
                {
                    headers: API.getHeaders(true)
                }
            );
            console.log(response.data.description);
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
// Plans APIs
API.plans = {
    // دریافت لیست پلن‌های اشتراک
    async getPlans() {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/subscriptions/plan/`, {
                method: 'GET',
                headers: API.getHeaders(false) // بدون نیاز به توکن
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در دریافت پلن‌ها');
            }

            return {
                success: true,
                data: data
            };
        } catch (error) {
            console.error('Plans API error:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }
};

// Orders APIs
API.orders = {
    // دریافت جزئیات پلن برای checkout
    async getPlanDetails(planId) {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/order/purchase/${planId}/`, {
                method: 'GET',
                headers: API.getHeaders(true) // نیاز به توکن
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در دریافت اطلاعات پلن');
            }

            return {
                success: true,
                data: data.data,
                message: data.message
            };
        } catch (error) {
            console.error('Get plan details error:', error);
            return {
                success: false,
                message: error.message
            };
        }
    },

    // اعمال کد تخفیف/معرف
    async applyDiscountCode(planId, codes) {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/order/purchase/${planId}/`, {
                method: 'POST',
                headers: API.getHeaders(true),
                body: JSON.stringify(codes)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در اعمال کد');
            }

            return {
                success: true,
                data: data.data,
                message: data.message
            };
        } catch (error) {
            console.error('Apply discount error:', error);
            return {
                success: false,
                message: error.message
            };
        }
    },

    // ایجاد سفارش و انتقال به درگاه
    async createOrder(planId, codes) {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/order/purchase/${planId}/`, {
                method: 'POST',
                headers: API.getHeaders(true),
                body: JSON.stringify(codes)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در ثبت سفارش');
            }

            return {
                success: true,
                data: data.data,
                message: data.message
            };
        } catch (error) {
            console.error('Create order error:', error);
            return {
                success: false,
                message: error.message
            };
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

    const testSlug = 'tst-tst'; // از JSON شما


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
// testPrescriptionDetailAPI();

// Authentication API
API.authentication = {
    // Submit authentication request
    async submit(formData) {
        try {
            const token = StorageManager.getAccessToken();
            
            const response = await fetch(`${API.BASE_URL}api/v1/accounts/authentication/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || data.detail || 'خطا در ارسال درخواست احراز هویت');
            }

            return data;
        } catch (error) {
            console.error('Authentication submit error:', error);
            throw error;
        }
    }
};


// Tutorial APIs
API.tutorials = {
    // Get all tutorials
    async getAll() {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/home/tutorials/`, {
                method: 'GET',
                headers: API.getHeaders(false) // بدون نیاز به Authentication
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در دریافت آموزش‌ها');
            }

            return data;
        } catch (error) {
            console.error('Tutorials API error:', error);
            throw error;
        }
    }
    
};

// Test function (برای Console)
async function testTutorialsAPI() {
    console.log('🧪 Testing Tutorials API...\n');
    
    try {
        const response = await API.tutorials.getAll();
        console.log('✅ Success! Response:', response);
        console.log('📊 Total Count:', response.count);
        console.log('📹 Videos:', response.data);
        
        if (response.data.length > 0) {
            console.log('\n🎥 First video:');
            console.log('  - Title:', response.data[0].title);
            console.log('  - ID:', response.data[0].id);
            console.log('  - Created:', response.data[0].created_at);
        }
    } catch (error) {
        console.error('❌ Test Failed:', error.message);
    }
}

// برای تست در Console:
// testTutorialsAPI();


// Payment APIs
API.payment = {
    // ایجاد پرداخت با زرین‌پال
    async createZarinpalPayment(paymentData) {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/payment/zarinpal/create/`, {
                method: 'POST',
                headers: API.getHeaders(true),
                body: JSON.stringify(paymentData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در ایجاد درخواست پرداخت');
            }

            return {
                success: data.success || true,
                payment_id: data.payment_id,
                payment_url: data.payment_url,
                message: data.message
            };
        } catch (error) {
            console.error('ZarinPal payment error:', error);
            return {
                success: false,
                message: error.message
            };
        }
    },

    // ایجاد پرداخت با پارس پال
    async createParspalPayment(paymentData) {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/payment/parspal/request/`, {
                method: 'POST',
                headers: API.getHeaders(true),
                body: JSON.stringify(paymentData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در ایجاد درخواست پرداخت');
            }

            return {
                success: data.success || true,
                payment_id: data.payment_id,
                payment_url: data.payment_url,
                message: data.message
            };
        } catch (error) {
            console.error('ParsPal payment error:', error);
            return {
                success: false,
                message: error.message
            };
        }
    },

    // تایید پرداخت زرین‌پال (برای صفحه callback)
    async verifyZarinpalPayment(authority) {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/payment/zarinpal/verify/`, {
                method: 'POST',
                headers: API.getHeaders(true),
                body: JSON.stringify({ authority })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در تایید پرداخت');
            }

            return {
                success: true,
                data: data
            };
        } catch (error) {
            console.error('ZarinPal verify error:', error);
            return {
                success: false,
                message: error.message
            };
        }
    },

    // تایید پرداخت پارس پال (برای صفحه callback)
    async verifyParspalPayment(token) {
        try {
            const response = await fetch(`${API.BASE_URL}api/v1/payment/parspal/verify/`, {
                method: 'POST',
                headers: API.getHeaders(true),
                body: JSON.stringify({ token })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'خطا در تایید پرداخت');
            }

            return {
                success: true,
                data: data
            };
        } catch (error) {
            console.error('ParsPal verify error:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }
};
