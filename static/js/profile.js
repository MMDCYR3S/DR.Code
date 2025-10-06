// مدیریت صفحه پروفایل کاربر
const profileApp = {
    // State Management
    profileData: null,
    profileUpdateData: null,
    loading: true,
    error: null,
    editMode: false,

    // اولیه‌سازی
    async init() {
        console.log('Profile App Initialized');
        await this.loadProfileData();
    },

    // بارگذاری اطلاعات پروفایل
    async loadProfileData() {
        try {
            this.loading = true;
            this.error = null;

            console.log('Loading profile data...');

            // دریافت اطلاعات اصلی پروفایل
            const profileResponse = await API.profile.getProfile();
            console.log('Profile Data:', profileResponse);
            
            if (profileResponse.success) {
                this.profileData = profileResponse.data;
            }

            // دریافت اطلاعات کامل برای ویرایش
            const updateResponse = await API.profile.getProfileUpdate();
            console.log('Profile Update Data:', updateResponse);
            
            if (updateResponse.success) {
                this.profileUpdateData = updateResponse.data;
            }

        } catch (error) {
            console.error('Error loading profile:', error);
            this.error = error.message;
            
            // نمایش پیام خطا
            Swal.fire({
                icon: 'error',
                title: 'خطا در بارگذاری اطلاعات',
                text: error.message,
                confirmButtonText: 'تلاش مجدد',
                confirmButtonColor: '#0077b6'
            }).then((result) => {
                if (result.isConfirmed) {
                    this.loadProfileData();
                }
            });
        } finally {
            this.loading = false;
        }
    },

    // فعال‌سازی حالت ویرایش
    enableEditMode() {
        this.editMode = true;
        console.log('Edit mode enabled');
    },

    // لغو ویرایش
    cancelEdit() {
        this.editMode = false;
        console.log('Edit mode cancelled');
    },

    // ذخیره تغییرات
    async saveProfile() {
        try {
            console.log('Saving profile changes...');
            
            // دریافت داده‌های فرم
            const formData = {
                first_name: document.getElementById('edit-first-name').value,
                last_name: document.getElementById('edit-last-name').value,
                email: document.getElementById('edit-email').value
            };

            console.log('Form data to save:', formData);

            // ارسال به API
            const response = await API.profile.updateProfile(formData);
            console.log('Update response:', response);

            if (response.success) {
                // به‌روزرسانی داده‌های محلی
                await this.loadProfileData();
                this.editMode = false;

                // نمایش پیام موفقیت
                Swal.fire({
                    icon: 'success',
                    title: 'موفقیت',
                    text: 'اطلاعات با موفقیت به‌روزرسانی شد',
                    confirmButtonColor: '#0077b6'
                });
            }

        } catch (error) {
            console.error('Error saving profile:', error);
            
            Swal.fire({
                icon: 'error',
                title: 'خطا در ذخیره',
                text: error.message,
                confirmButtonColor: '#0077b6'
            });
        }
    },

    // محاسبه زمان باقی‌مانده اشتراک
    getSubscriptionTimeLeft() {
        if (!this.profileData?.subscription_end_date) {
            return null;
        }

        const endDate = new Date(this.profileData.subscription_end_date);
        const now = new Date();
        const diffTime = endDate - now;
        
        if (diffTime <= 0) {
            return 'منقضی شده';
        }

        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return `${diffDays} روز`;
    },

    // دریافت رنگ وضعیت احراز هویت
    getAuthStatusColor() {
        if (!this.profileData?.auth_status) return 'bg-gray-500';
        
        switch (this.profileData.auth_status) {
            case 'APPROVED':
                return 'bg-green-500';
            case 'PENDING':
                return 'bg-yellow-500';
            case 'REJECTED':
                return 'bg-red-500';
            default:
                return 'bg-gray-500';
        }
    },

    // دریافت آیکون وضعیت احراز هویت
    getAuthStatusIcon() {
        if (!this.profileData?.auth_status) return 'fas fa-question';
        
        switch (this.profileData.auth_status) {
            case 'APPROVED':
                return 'fas fa-check-circle';
            case 'PENDING':
                return 'fas fa-clock';
            case 'REJECTED':
                return 'fas fa-times-circle';
            default:
                return 'fas fa-question';
        }
    }
};

// اولیه‌سازی در بارگذاری صفحه
document.addEventListener('DOMContentLoaded', () => {
    // بررسی اینکه کاربر لاگین است یا نه
    if (!StorageManager.isLoggedIn()) {
        window.location.href = '/';
        return;
    }
    
    // اولیه‌سازی Alpine.js component
    window.profileApp = profileApp;
});





// کد تست برای کنسول - اضافه کردن به profile.js

// تابع تست برای بررسی API ها
async function testProfileAPIs() {
    console.log('=== شروع تست API های پروفایل ===');
    
    // بررسی وضعیت لاگین
    console.log('وضعیت لاگین:', StorageManager.isLoggedIn());
    console.log('Access Token:', StorageManager.getAccessToken());
    
    if (!StorageManager.isLoggedIn()) {
        console.error('کاربر لاگین نیست!');
        return;
    }

    try {
        // تست API اول
        console.log('\n--- تست API اطلاعات پروفایل ---');
        const profileData = await API.profile.getProfile();
        console.log('✅ Profile Data:', profileData);

        // تست API دوم  
        console.log('\n--- تست API اطلاعات ویرایش ---');
        const updateData = await API.profile.getProfileUpdate();
        console.log('✅ Profile Update Data:', updateData);

        console.log('\n=== همه تست‌ها موفق بودند ===');
        
    } catch (error) {
        console.error('❌ خطا در تست:', error);
    }
}

// اجرای تست در صورت نیاز
// testProfileAPIs();
