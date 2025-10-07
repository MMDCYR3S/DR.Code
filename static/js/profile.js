// مدیریت صفحه پروفایل
console.log('👤 Profile.js loading...');

const profileApp = {
    profileData: null,
    profileUpdateData: null,
    loading: true,
    error: null,
    editMode: false,

    async init() {
        console.log('🟢 Profile app initializing...');
        
        // چک کن لاگین هست یا نه
        if (!StorageManager.isLoggedIn()) {
            console.log('❌ Not logged in, redirecting to home');
            window.location.href = '/';
            return;
        }

        console.log('✅ User is logged in, loading profile data...');
        await this.loadProfileData();
    },

    async loadProfileData() {
        try {
            this.loading = true;
            this.error = null;

            console.log('📡 Fetching profile data...');

            // دریافت اطلاعات پروفایل
            const profileResponse = await API.profile.getProfile();
            console.log('📦 Profile response:', profileResponse);

            if (profileResponse.success) {
                this.profileData = profileResponse.data;
            } else {
                throw new Error(profileResponse.message || 'خطا در دریافت اطلاعات');
            }

            // دریافت اطلاعات ویرایش
            const updateResponse = await API.profile.getProfileUpdate();
            console.log('📦 Update response:', updateResponse);

            if (updateResponse.success) {
                this.profileUpdateData = updateResponse.data;
            }

            console.log('✅ Profile loaded successfully');

        } catch (error) {
            console.error('❌ Profile load error:', error);
            this.error = error.message;

            // اگه خطای authentication بود
            if (error.message.includes('401') || error.message.includes('نشست')) {
                console.log('🔴 Session expired, logging out...');
                StorageManager.clearAll();
                window.location.href = '/';
                return;
            }

            // نمایش خطا
            Swal.fire({
                icon: 'error',
                title: 'خطا',
                text: error.message,
                confirmButtonText: 'باشه'
            });
        } finally {
            this.loading = false;
        }
    },

    enableEditMode() {
        this.editMode = true;
    },

    cancelEdit() {
        this.editMode = false;
    },

    async saveProfile() {
        try {
            const formData = {
                first_name: document.getElementById('edit-first-name').value,
                last_name: document.getElementById('edit-last-name').value,
                email: document.getElementById('edit-email').value
            };

            const response = await API.profile.updateProfile(formData);

            if (response.success) {
                await this.loadProfileData();
                this.editMode = false;

                Swal.fire({
                    icon: 'success',
                    title: 'موفق',
                    text: 'اطلاعات ذخیره شد'
                });
            }

        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'خطا',
                text: error.message
            });
        }
    }
};

// فقط اگه توی صفحه profile هستیم، init کن
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOM loaded');
    
    // چک کن که آیا این صفحه profile هست
    if (window.location.pathname.includes('/profile')) {
        console.log('✅ This is profile page, initializing...');
        
        window.profileApp = profileApp;
        
        // یکم صبر کن تا همه چیز لود بشه
        setTimeout(() => {
            profileApp.init();
        }, 200);
    } else {
        console.log('ℹ️ Not profile page, skipping profile init');
    }
});

console.log('✅ Profile.js loaded');
