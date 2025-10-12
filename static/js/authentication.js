// Alpine.js Component for Authentication Form
function authenticationForm() {
    return {
        // Form Data
        formData: {
            medical_code: '',
            auth_link: '',
            referral_code: ''
        },
        
        // Files
        files: [],
        dragOver: false,
        
        // State
        isSubmitting: false,
        maxTotalSize: 5 * 1024 * 1024, // 5MB in bytes
        
        // Computed: Total Size
        get totalSize() {
            return this.files.reduce((sum, file) => sum + file.size, 0);
        },
        
        // Initialize
        init() {
            this.checkAuthStatus();
        },
        
        // Check if user is logged in and authenticated
        async checkAuthStatus() {
            // Check if user is logged in
            if (!StorageManager.isLoggedIn()) {
                await Swal.fire({
                    icon: 'warning',
                    title: 'لطفاً ابتدا وارد شوید',
                    text: 'برای احراز هویت باید ابتدا در سایت ثبت‌نام کنید',
                    confirmButtonText: 'ورود / ثبت‌نام',
                    confirmButtonColor: '#0077b6'
                });
                window.location.href = '/';
                return;
            }
            
            // Check if already authenticated
            try {
                const profile = StorageManager.getUserProfile();
                if (profile && profile.is_authenticated === true) {
                    await Swal.fire({
                        icon: 'success',
                        title: 'شما قبلاً احراز هویت شده‌اید',
                        text: 'حساب کاربری شما تایید شده است',
                        confirmButtonText: 'بازگشت به صفحه اصلی',
                        confirmButtonColor: '#0077b6'
                    });
                    window.location.href = '/';
                }
            } catch (error) {
                console.log('Could not check authentication status:', error);
            }
        },
        
        // Handle File Select
        handleFileSelect(event) {
            const selectedFiles = Array.from(event.target.files);
            this.addFiles(selectedFiles);
            event.target.value = ''; // Reset input
        },
        
        // Handle Drag & Drop
        handleDrop(event) {
            this.dragOver = false;
            const droppedFiles = Array.from(event.dataTransfer.files);
            this.addFiles(droppedFiles);
        },
        
        // Add Files
        addFiles(newFiles) {
            // Filter valid files
            const validFiles = newFiles.filter(file => {
                const isValidType = file.type === 'image/jpeg' || 
                                  file.type === 'image/png' || 
                                  file.type === 'application/pdf';
                
                if (!isValidType) {
                    Swal.fire({
                        icon: 'error',
                        title: 'فرمت نامعتبر',
                        text: `فایل "${file.name}" فرمت مجاز نیست. فقط JPG، PNG و PDF قابل قبول است.`,
                        confirmButtonColor: '#0077b6'
                    });
                    return false;
                }
                
                return true;
            });
            
            // Add to files array
            this.files = [...this.files, ...validFiles];
            
            // Check total size
            if (this.totalSize > this.maxTotalSize) {
                Swal.fire({
                    icon: 'warning',
                    title: 'حجم فایل زیاد است',
                    text: 'مجموع حجم فایل‌ها نباید بیش از 5 مگابایت باشد',
                    confirmButtonColor: '#0077b6'
                });
            }
        },
        
        // Remove File
        removeFile(index) {
            this.files.splice(index, 1);
        },
        
        // Format File Size
        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        },
        
        // Submit Form
        async submitForm() {
            // Validation
            if (this.files.length === 0) {
                await Swal.fire({
                    icon: 'error',
                    title: 'فایلی انتخاب نشده',
                    text: 'لطفاً حداقل یک فایل (کارت نظام پزشکی یا دانشجویی) را بارگذاری کنید',
                    confirmButtonColor: '#0077b6'
                });
                return;
            }
            
            if (this.totalSize > this.maxTotalSize) {
                await Swal.fire({
                    icon: 'error',
                    title: 'حجم فایل زیاد است',
                    text: 'مجموع حجم فایل‌ها نباید بیش از 5 مگابایت باشد',
                    confirmButtonColor: '#0077b6'
                });
                return;
            }
            
            // Prepare FormData
            const formData = new FormData();
            
            // Add text fields (only if not empty)
            if (this.formData.medical_code.trim()) {
                formData.append('medical_code', this.formData.medical_code.trim());
            }
            
            if (this.formData.auth_link.trim()) {
                formData.append('auth_link', this.formData.auth_link.trim());
            }
            
            if (this.formData.referral_code.trim()) {
                formData.append('referral_code', this.formData.referral_code.trim());
            }
            
            // Add files
            this.files.forEach((file, index) => {
                formData.append('documents', file);
            });
            
            // Submit
            this.isSubmitting = true;
            
            try {
                const response = await API.authentication.submit(formData);
                
                // Success
                await Swal.fire({
                    icon: 'success',
                    title: 'درخواست با موفقیت ارسال شد',
                    html: `
                        <p class="text-gray-700 mb-3">درخواست احراز هویت شما ثبت شد</p>
                        <div class="bg-blue-50 rounded-lg p-4 text-sm text-gray-700">
                            <i class="fas fa-info-circle text-blue-500 ml-2"></i>
                            نتیجه بررسی از طریق ایمیل به شما اطلاع‌رسانی خواهد شد
                        </div>
                    `,
                    confirmButtonText: 'بازگشت به صفحه اصلی',
                    confirmButtonColor: '#0077b6',
                    allowOutsideClick: false
                });
                
                // Redirect to home
                window.location.href = '/';
                
            } catch (error) {
                await Swal.fire({
                    icon: 'error',
                    title: 'خطا در ارسال درخواست',
                    text: error.message || 'لطفاً دوباره تلاش کنید',
                    confirmButtonColor: '#0077b6'
                });
            } finally {
                this.isSubmitting = false;
            }
        }
    }
}

// Auto-check on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Authentication page loaded');
});
