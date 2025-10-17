// Alpine.js Component for Prescription Detail Page
function prescriptionDetailApp() {
    return {
        prescription: null,
        description: '',
        loading: true,
        descriptionLoading: true,
        isSaved: false,
        isPremiumUser: false,
        userProfile: null,
        
        questionText: '',
        questionSubmitting: false,
        
        showTutorialModal: false,
        showDescriptionModal: false,
        fullDescription: '',
        
        watermarkText: 'drcode-med.ir',

        

        async init() {
            const slug = this.getSlugFromURL();
            
            if (!slug) {
                window.location.href = '/prescriptions';
                return;
            }

            const userData = StorageManager.getUserData();
            // استفاده از متد جدید برای چک کردن Premium
            this.checkPremiumStatus();
            
            // تست دستی (میتونی بعدا کامنت کنی)
            console.log('🎯 Premium Status:', this.isPremiumUser);
            this.userProfile = userData;
            
            if (userData?.medical_code) {
                this.watermarkText = userData.medical_code;
            }

            await this.loadPrescription(slug);
            await this.loadDescription(slug);
            
            this.initSecurityMeasures();
            
        },

        getSlugFromURL() {
            const path = window.location.pathname;
            const match = path.match(/\/prescriptions\/([^\/]+)/);
            return match ? match[1] : null;
        },

        async loadPrescription(slug) {
            try {
                this.loading = true;
                const response = await API.prescriptions.getDetail(slug);
                
                this.prescription = response;
                this.isSaved = response.is_saved || false;
                
                const drugs = this.prescription.prescription_drugs || [];
                const description = this.prescription.description;
                this.prescription.normalDrugs = drugs.filter(
                    d => !d.is_combination && !d.is_substitute
                );
                
                this.prescription.combinationGroups = this.getCombinationGroups(drugs);
                
                this.prescription.substituteDrugs = drugs.filter(
                    d => d.is_substitute && !d.is_combination
                );

            } catch (error) {
                console.error('Error loading prescription:', error);
                
                Swal.fire({

                    icon: 'error',
                    title: 'خطا',
                    text: 'خطا در بارگذاری اطلاعات نسخه',
                    confirmButtonText: 'بازگشت',
                    confirmButtonColor: '#0077b6'
                }).then(() => {
                    window.location.href = '/prescriptions';
                });
            } finally {
                this.loading = false;
            }
            // Initialize gallery after data is loaded
this.initGallery();

        },

        // Initialize GLightbox for images
initGallery() {
    if (this.prescription.images && this.prescription.images.length > 0) {
        // Wait for DOM to update
        this.$nextTick(() => {
            const lightbox = GLightbox({
                selector: '.glightbox',
                touchNavigation: true,
                loop: true,
                autoplayVideos: false,
                closeButton: true,
                openEffect: 'zoom',
                closeEffect: 'fade',
                slideEffect: 'slide',
                moreLength: 0,
                skin: 'clean',
                cssEfects: {
                    fade: { in: 'fadeIn', out: 'fadeOut' },
                    zoom: { in: 'zoomIn', out: 'zoomOut' }
                }
            });
        });
    }
},

        async loadDescription(slug) {
            try {
                this.descriptionLoading = true;
                const response = await API.prescriptions.getDescription(slug);
                
                // بررسی دقیق محتوای description
                if (response && response.description) {
                    const cleanDesc = response.description.trim();
                    // اگر فقط تگ خالی بود، null قرار بده
                    this.description = (cleanDesc === '' || cleanDesc === '<p></p>' || cleanDesc === '<p><br></p>') 
                        ? null 
                        : cleanDesc;
                } else {
                    this.description = null;
                }
                
                console.log('Description loaded:', this.description); // برای debug
                
            } catch (error) {
                console.error('Error loading description:', error);
                this.description = null; // در صورت خطا null بذار تا باکس نمایش نشه
            } finally {
                this.descriptionLoading = false;
            }
        },
        

        getCombinationGroups(drugs) {
            const groups = {};
            
            drugs
                .filter(d => d.is_combination && d.group_number)
                .forEach(drug => {
                    if (!groups[drug.group_number]) {
                        groups[drug.group_number] = [];
                    }
                    groups[drug.group_number].push(drug);
                });

            return groups;
        },

        async toggleSave() {
            // چک لاگین
            if (!StorageManager.isLoggedIn()) {
                Auth.showAuthModal();
                return;
            }
        
            try {
                console.log('💾 Attempting to save prescription:', this.prescription.slug);
                
                // فراخوانی API با endpoint درست
                const response = await API.post(
                    `/accounts/profile/prescription/save/${this.prescription.slug}/`,
                    {} // بدنه خالی
                );
                alert(this.prescription.slug)
                console.log('✅ Save response:', response);
                
                // بررسی پاسخ
                if (response.is_saved !== undefined) {
                    this.isSaved = response.is_saved;
                    
                    const message = this.isSaved ? 'نسخه ذخیره شد ✅' : 'نسخه از لیست حذف شد ❌';
                    
                    Swal.fire({
                        icon: 'success',
                        title: message,
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false,
                        timer: 2000,
                        timerProgressBar: true
                    });
                } else {
                    throw new Error('Invalid response format');
                }
                
            } catch (error) {
                console.error('❌ Save error:', error);
                
                Swal.fire({
                    icon: 'error',
                    title: 'خطا در ذخیره‌سازی',
                    text: error.message || 'لطفاً دوباره تلاش کنید',
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#ef4444'
                });
            }
        }
        ,

        shareLink() {
            const url = window.location.href;
            
            navigator.clipboard.writeText(url).then(() => {
                Swal.fire({
                    icon: 'success',
                    title: 'لینک کپی شد',
                    text: 'لینک این نسخه در کلیپ‌بورد شما کپی شد',
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 2000,
                    timerProgressBar: true
                });
            }).catch(() => {
                Swal.fire({
                    icon: 'error',
                    title: 'خطا',
                    text: 'خطا در کپی لینک',
                    confirmButtonText: 'باشه'
                });
            });
        },

        scrollToQuestion() {
            const questionBox = document.getElementById('question-section');
            if (questionBox) {
                questionBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            alert('salam')
        },

        copyDrugCode(code) {
            navigator.clipboard.writeText(code).then(() => {
                Swal.fire({
                    icon: 'success',
                    title: 'کپی شد',
                    text: `کد ${code} کپی شد`,
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 1500
                });
            });
        },

        showFullDescription(description) {
            if (description && description.length > 100) {
                this.fullDescription = description;
                this.showDescriptionModal = true;
            }
        },

        truncateDescription(text, maxLength = 100) {
            if (!text) return '-';
            if (text.length <= maxLength) return text;
            return text.substring(0, maxLength) + '...';
        },

        async submitQuestion() {
            if (!this.isPremiumUser) {
                this.showUpgradeModal();
                return;
            }

            if (!this.questionText.trim()) {
                Swal.fire({
                    icon: 'warning',
                    title: 'هشدار',
                    text: 'لطفاً سوال خود را بنویسید',
                    confirmButtonText: 'باشه'
                });
                return;
            }

            try {
                this.questionSubmitting = true;
                
                const questionData = {
                    question: this.questionText,
                    prescription_slug: this.prescription.slug,
                    user_profile: this.userProfile
                };

                await API.prescriptions.submitQuestion(this.prescription.slug, questionData);
                
                Swal.fire({
                    icon: 'success',
                    title: 'سوال ارسال شد',
                    text: 'سوال شما با موفقیت ثبت شد و به زودی پاسخ داده می‌شود',
                    confirmButtonText: 'باشه',
                    confirmButtonColor: '#0077b6'
                });

                this.questionText = '';
                
            } catch (error) {
                Swal.fire({
                    icon: 'error',
                    title: 'خطا',
                    text: 'خطا در ارسال سوال. لطفاً دوباره تلاش کنید',
                    confirmButtonText: 'باشه'
                });
            } finally {
                this.questionSubmitting = false;
            }
        },

        showUpgradeModal() {
            Swal.fire({
                title: 'ویژه کاربران Premium',
                html: `
                    <div class="text-center">
                        <i class="fas fa-crown text-6xl text-amber-500 mb-4"></i>
                        <p class="mb-4">برای ارسال سوال نیاز به اشتراک ویژه دارید</p>
                        <p class="text-sm text-gray-600">با خرید اشتراک ویژه می‌توانید از متخصصین سوال بپرسید</p>
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: 'خرید اشتراک ویژه',
                cancelButtonText: 'بستن',
                confirmButtonColor: '#f59e0b',
                cancelButtonColor: '#6b7280'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = '/plans';
                }
            });
        },

        getTextColor(bgClass) {
            if (!bgClass) return '';
            return bgClass.replace('bg-', 'text-');
        },

        getBorderColor(bgClass) {
            if (!bgClass) return '';
            return bgClass.replace('bg-', 'border-');
        },

        getBgColorStyle(colorCode) {
            if (!colorCode) return '';
            const colorMap = {
                'bg-red-500': '#ef4444',
                'bg-blue-500': '#3b82f6',
                'bg-green-500': '#22c55e',
                'bg-yellow-500': '#eab308',
                'bg-purple-500': '#a855f7',
                'bg-pink-500': '#ec4899',
                'bg-indigo-500': '#6366f1',
                'bg-orange-500': '#f97316',
                'bg-teal-500': '#14b8a6',
                'bg-cyan-500': '#06b6d4'
            };
            return colorMap[colorCode] || '#3b82f6';
        },

        initSecurityMeasures() {
            document.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                return false;
            });

            document.addEventListener('keyup', (e) => {
                if (e.key === 'PrintScreen') {
                    navigator.clipboard.writeText('');
                    Swal.fire({
                        icon: 'warning',
                        title: 'غیرمجاز',
                        text: 'اسکرین‌شات از این صفحه مجاز نیست',
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false,
                        timer: 2000
                    });
                }
            });

            document.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
                    e.preventDefault();
                    Swal.fire({
                        icon: 'warning',
                        title: 'غیرمجاز',
                        text: 'چاپ این صفحه مجاز نیست',
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false,
                        timer: 2000
                    });
                    return false;
                }
            });

        },

        // در داخل return object، این متد رو اضافه کن یا جایگزین کن:

        // در فایل prescription_detail.js - اضافه کردن این متد به return object

groupDrugsByGroupNumber() {
    if (!this.prescription?.prescription_drugs) return {};
    
    const groups = {};
    const ungrouped = [];
    
    this.prescription.prescription_drugs.forEach(drug => {
        if (drug.group_number) {
            if (!groups[drug.group_number]) {
                groups[drug.group_number] = [];
            }
            groups[drug.group_number].push(drug);
        } else {
            ungrouped.push(drug);
        }
    });
    
    // اگر داروی بدون گروه وجود دارد، آن را به عنوان گروه 0 اضافه کن
    if (ungrouped.length > 0) {
        groups[0] = ungrouped;
    }
    
    return groups;
},

getGroupTitle(groupNumber) {
    if (groupNumber == 0) return 'داروهای بدون گروه';
    return `گروه ${groupNumber}`;
},

getBorderClasses(drug) {
    let classes = [];
    
    if (drug.is_combination) {
        classes.push('border-r-4 border-r-purple-600');
    }
    
    if (drug.is_substitute) {
        classes.push('border-l-4 border-l-lime-600');
    }
    
    return classes.join(' ');
}
,

checkPremiumStatus() {
    try {
        // خواندن از localStorage با کلید دقیق
        const userProfileString = localStorage.getItem('drcode_user_profile');
        
        console.log('🔍 Raw localStorage data:', userProfileString);
        
        if (!userProfileString) {
            console.warn('⚠️ No user profile found in localStorage');
            this.isPremiumUser = false;
            this.userProfile = null;
            return false;
        }

        const userProfile = JSON.parse(userProfileString);
        console.log('📦 Parsed user profile:', userProfile);
        
        // چک کردن role
        const isPremium = userProfile?.role === 'premium';
        console.log('👑 Is Premium User?', isPremium);
        console.log('🎭 User Role:', userProfile?.role);
        
        this.isPremiumUser = isPremium;
        this.userProfile = userProfile;
        
        // تست watermark
        if (userProfile?.medical_code) {
            this.watermarkText = userProfile.medical_code;
            console.log('🏷️ Watermark set to:', this.watermarkText);
        }
        
        return isPremium;
        
    } catch (error) {
        console.error('❌ Error checking premium status:', error);
        this.isPremiumUser = false;
        this.userProfile = null;
        return false;
    }
},

// تست کامل Premium Status
testPremiumStatus() {
    console.log('🧪 Starting Premium Status Test...');
    console.log('─────────────────────────────────');
    
    // تست 1: خواندن مستقیم از localStorage
    const rawData = localStorage.getItem('drcode_user_profile');
    console.log('Test 1 - Raw Data:', rawData);
    
    // تست 2: Parse کردن
    try {
        const parsed = JSON.parse(rawData);
        console.log('Test 2 - Parsed Data:', parsed);
        console.log('Test 2 - Role Field:', parsed?.role);
        console.log('Test 2 - Role Type:', typeof parsed?.role);
    } catch (e) {
        console.error('Test 2 - Parse Error:', e);
    }
    
    // تست 3: چک کردن شرط
    const result = this.checkPremiumStatus();
    console.log('Test 3 - Final Result:', result);
    console.log('Test 3 - isPremiumUser:', this.isPremiumUser);
    
    console.log('─────────────────────────────────');
    console.log('🧪 Test Completed!');
    
    // نمایش نتیجه در UI
    if (this.isPremiumUser) {
        console.log('✅ SUCCESS: Premium User Detected!');
        alert('✅ شما کاربر Premium هستید!');
    } else {
        console.log('❌ FAILED: Not a Premium User');
        alert('❌ شما کاربر Premium نیستید یا اطلاعات یافت نشد');
    }
},
async init() {
    const slug = this.getSlugFromURL();

    if (!slug) {
        window.location.href = '/prescriptions';
        return;
    }

    const userData = StorageManager.getUserData();
    
    // چک کردن وضعیت Premium
    this.checkPremiumStatus();
    
    this.userProfile = userData;

    if (userData?.medical_code) {
        this.watermarkText = userData.medical_code;
    }

    await this.loadPrescription(slug);
    await this.loadDescription(slug);

    this.initSecurityMeasures();
    this.initGallery();
},

// Check if user is Premium
checkPremiumStatus() {
    try {
        const userProfile = StorageManager.getUserProfile();
        
        if (!userProfile) {
            console.log('❌ No user profile found');
            this.isPremiumUser = false;
            return false;
        }

        const isPremium = userProfile.role === 'premium';
        console.log('👑 Premium Status:', isPremium);
        console.log('🎭 User Role:', userProfile.role);

        this.isPremiumUser = isPremium;
        this.userProfile = userProfile;

        return isPremium;

    } catch (error) {
        console.error('❌ Error checking premium status:', error);
        this.isPremiumUser = false;
        return false;
    }
},

// Scroll to Question Box
scrollToQuestion() {
    const questionBox = document.getElementById('question-section');
    if (questionBox && typeof scroll !== 'undefined') {
        scroll.animateScroll(questionBox);
    } else if (questionBox) {
        // Fallback اگر SmoothScroll لود نشده بود
        questionBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
},

// Submit Question (فعلاً فقط ساختار)
async submitQuestion() {
    if (!this.isPremiumUser) {
        Swal.fire({
            icon: 'warning',
            title: 'دسترسی محدود',
            text: 'این قابلیت فقط برای کاربران Premium است',
            confirmButtonText: 'باشه'
        });
        return;
    }

    if (!this.questionText.trim()) {
        Swal.fire({
            icon: 'warning',
            title: 'هشدار',
            text: 'لطفاً سوال خود را بنویسید',
            confirmButtonText: 'باشه'
        });
        return;
    }

    if (this.questionText.length > 500) {
        Swal.fire({
            icon: 'warning',
            title: 'هشدار',
            text: 'حداکثر طول سوال 500 کاراکتر است',
            confirmButtonText: 'باشه'
        });
        return;
    }

    try {
        this.questionSubmitting = true;

        // TODO: اینجا بعداً API متد اضافه می‌شه
        const questionData = {
            question: this.questionText,
            prescription_slug: this.prescription.slug,
            user_profile: this.userProfile
        };

        console.log('📤 Sending question:', questionData);

        // فعلاً فقط یک تاخیر شبیه‌سازی شده
        await new Promise(resolve => setTimeout(resolve, 2000));

        // موفقیت
        Swal.fire({
            icon: 'success',
            title: 'سوال ارسال شد',
            text: 'سوال شما با موفقیت ثبت شد و به زودی پاسخ داده می‌شود',
            confirmButtonText: 'باشه',
            confirmButtonColor: '#0077b6'
        });

        // پاک کردن فیلد
        this.questionText = '';

    } catch (error) {
        console.error('❌ Error submitting question:', error);
        
        Swal.fire({
            icon: 'error',
            title: 'خطا',
            text: 'خطا در ارسال سوال. لطفاً دوباره تلاش کنید',
            confirmButtonText: 'باشه'
        });
    } finally {
        this.questionSubmitting = false;
    }
},

    }


}
// نسخه بهبود یافته برای Alpine.js
function createProtectedWatermark() {
    let watermarkAdded = false;
    
    function addWatermark() {
        const targetSection = document.getElementById('prescription__section');
        
        // بررسی دقیق‌تر وضعیت نمایش سکشن
        if (!targetSection) {
            console.log('Section not found');
            return;
        }
        
        const style = getComputedStyle(targetSection);
        if (style.display === 'none' || style.visibility === 'hidden' || targetSection.offsetHeight === 0) {
            console.log('Section is hidden');
            return;
        }
        
        const existing = targetSection.querySelector('#protected-watermark');
        if (existing) {
            console.log('Watermark already exists');
            return;
        }
        
        console.log('Adding watermark...');
        
        const watermark = document.createElement('div');
        watermark.id = 'protected-watermark';
        watermark.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 10;
            overflow: hidden;
        `;
        
        // اطمینان از position: relative
        const computedStyle = getComputedStyle(targetSection);
        if (computedStyle.position === 'static') {
            targetSection.style.position = 'relative';
        }
        
        // محاسبه اندازه واقعی سکشن
        const sectionRect = targetSection.getBoundingClientRect();
        const isMobile = window.innerWidth < 768;
        
        // تعداد ثابت: 3 ردیف و 4 ستون
        const cols = 4;
        const rows = 3;
        
        // محاسبه فاصله بین هر واترمارک
        const colSpacing = sectionRect.width / (cols + 1);
        const rowSpacing = sectionRect.height / (rows + 1);
        
        const container = document.createElement('div');
        container.style.cssText = `
            position: relative;
            width: 100%;
            height: 100%;
            `;
            let medi = localStorage.getItem('drcode_user_profile')
            let mediObject = JSON.parse(medi);
            // alert(!!null)
        for (let row = 1; row <= rows; row++) {
            for (let col = 1; col <= cols; col++) {
                const text = document.createElement('div');
                text.textContent = medi?mediObject.medical_code:'drcode-med.ir';
                text.style.cssText = `
                    position: absolute;
                    top: ${row * rowSpacing}px;
                    left: ${col * colSpacing}px;
                    transform: translate(-50%, -50%) rotate(-45deg);
                    font-size: ${isMobile ? '34px' : '40px'};
                    font-weight: bold;
                    color: rgba(0, 0, 0, 0.15);
                    white-space: nowrap;
                    user-select: none;
                    font-family: Arial, sans-serif;
                `;
                container.appendChild(text);
            }
        }
        
        watermark.appendChild(container);
        targetSection.insertBefore(watermark, targetSection.firstChild);
        watermarkAdded = true;
        console.log('Watermark added successfully');
    }
    
    // تلاش مداوم برای اضافه کردن واترمارک
    function keepTrying() {
        const targetSection = document.getElementById('prescription__section');
        if (targetSection) {
            const style = getComputedStyle(targetSection);
            if (style.display !== 'none' && style.visibility !== 'hidden' && targetSection.offsetHeight > 0) {
                if (!targetSection.querySelector('#protected-watermark')) {
                    addWatermark();
                }
            }
        }
    }
    
    // تلاش‌های متعدد با فواصل زمانی مختلف
    setTimeout(keepTrying, 100);
    setTimeout(keepTrying, 300);
    setTimeout(keepTrying, 500);
    setTimeout(keepTrying, 800);
    setTimeout(keepTrying, 1000);
    setTimeout(keepTrying, 1500);
    setTimeout(keepTrying, 2000);
    
    // رصد تغییرات DOM برای تشخیص زمان لود شدن سکشن
    const bodyObserver = new MutationObserver(function(mutations) {
        keepTrying();
    });
    
    bodyObserver.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'x-show', 'class']
    });
    
    // محافظت در برابر حذف
    const sectionObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.removedNodes.forEach(function(node) {
                if (node.id === 'protected-watermark') {
                    console.log('Watermark removed, re-adding...');
                    setTimeout(addWatermark, 50);
                }
            });
        });
    });
    
    // شروع observer برای سکشن با تلاش مداوم
    let observerStarted = false;
    const startSectionObserver = setInterval(function() {
        const targetSection = document.getElementById('prescription__section');
        if (targetSection && !observerStarted) {
            sectionObserver.observe(targetSection, {
                childList: true,
                subtree: true
            });
            observerStarted = true;
            keepTrying();
            console.log('Section observer started');
        }
    }, 50);
    
    // توقف بعد از 5 ثانیه
    setTimeout(function() {
        clearInterval(startSectionObserver);
    }, 5000);
    
    // مدیریت resize
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            const targetSection = document.getElementById('prescription__section');
            if (!targetSection) return;
            
            const existing = targetSection.querySelector('#protected-watermark');
            if (existing) existing.remove();
            addWatermark();
        }, 300);
    });
    
    // بررسی دوره‌ای هر 2 ثانیه
    setInterval(function() {
        keepTrying();
    }, 2000);
    
    // رویداد Alpine.js (اگر در دسترس باشد)
    document.addEventListener('alpine:initialized', function() {
        console.log('Alpine initialized');
        setTimeout(keepTrying, 200);
        setTimeout(keepTrying, 500);
    });
    
    // رویداد scroll (گاهی Alpine با scroll فعال می‌شود)
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(keepTrying, 100);
    }, { passive: true });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createProtectedWatermark);
} else {
    createProtectedWatermark();
}
