// Alpine.js Component for Prescription Detail Page
function prescriptionDetailApp() {
  return {
    prescription: null,
    description: "",
    loading: true,
    descriptionLoading: true,
    isSaved: false,
    isPremiumUser: false,
    userProfile: null,

    // Tutorial state (spotlight)
    showCopyTutorial: false,
    copyTutorialDismissed: false,
    copyTutorialRect: null,
    copyTutorialTooltip: { top: 0, left: 0, width: 320, position: "below", arrowLeft: 20 },
    copyTutorialTarget: null,
    _copyTutorialObserver: null,
    _copyTutorialShown: false,
    _copyTutorialScrollHandler: null,
    _copyTutorialTableScroller: null,

    questionText: "",
    questionSubmitting: false,

    showTutorialModal: false,
    showDescriptionModal: false,
    fullDescription: "",

    watermarkText: "drcode-med.ir",

    async init() {
      const slug = this.getSlugFromURL();

      if (!slug) {
        window.location.href = "/prescriptions";
        return;
      }

      const userData =  JSON.parse(localStorage.getItem("drcode_user_profile")).data

      // استفاده از متد جدید برای چک کردن Premium
      this.checkPremiumStatus();

      // تست دستی (میتونی بعدا کامنت کنی)
      console.log("🎯 Premium Status:", this.isPremiumUser);
      this.userProfile = userData;

      if (userData?.medical_code) {
        this.watermarkText = userData.medical_code;
      }

      await this.loadPrescription(slug);
      await this.loadDescription(slug);

      this.initSecurityMeasures();
      this.initCopyTutorial();
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
          (d) => !d.is_combination && !d.is_substitute
        );

        this.prescription.combinationGroups = this.getCombinationGroups(drugs);

        this.prescription.substituteDrugs = drugs.filter(
          (d) => d.is_substitute && !d.is_combination
        );
      } catch (error) {
        console.error("Error loading prescription:", error);
        const errorMessage =
          (error.response &&
            error.response.data &&
            error.response.data.detail) ||
          "خطا در بارگذاری اطلاعات نسخه. آدرس ممکن است اشتباه باشد.";

        Swal.fire({
          icon: "error",
          title: "خطا",
          text: errorMessage,
          confirmButtonText: "بازگشت",
          confirmButtonColor: "#0077b6",
        }).then(() => {
          setTimeout(() => {
            console.log("Redirecting to /prescriptions after 5 seconds...");
            window.location.href = "/prescriptions";
          }, 3000);
        });
      } finally {
        this.loading = false;
      }
      // Initialize gallery after data is loaded
      this.initGallery();
    },

    initGallery() {
    // handled by inline script
    },

    async loadDescription(slug) {
      try {
        this.descriptionLoading = true;
        const response = await API.prescriptions.getDescription(slug);

        // بررسی دقیق محتوای description
        if (response && response.description) {
          const cleanDesc = response.description.trim();
          // اگر فقط تگ خالی بود، null قرار بده
          this.description =
            cleanDesc === "" ||
            cleanDesc === "<p></p>" ||
            cleanDesc === "<p><br></p>"
              ? null
              : cleanDesc;
        } else {
          this.description = null;
        }

        console.log("Description loaded:", this.description); // برای debug
      } catch (error) {
        console.error("Error loading description:", error);
        this.description = null; // در صورت خطا null بذار تا باکس نمایش نشه
      } finally {
        this.descriptionLoading = false;
      }
    },

    getCombinationGroups(drugs) {
      const groups = {};

      drugs
        .filter((d) => d.is_combination && d.group_number)
        .forEach((drug) => {
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
        console.log(
          "💾 Attempting to save prescription:",
          this.prescription.slug
        );

        // >>> این خط را اصلاح کنید <<<
        // به جای API.post از متد صحیح استفاده کنید
        const response = await API.prescriptions.toggleSave(
          this.prescription.slug
        );

        console.log("✅ Save response:", response);

        // بررسی پاسخ
        if (response.is_saved !== undefined) {
          this.isSaved = response.is_saved;

          const message = this.isSaved
            ? "نسخه ذخیره شد ✅"
            : "نسخه از لیست حذف شد ❌";

          Swal.fire({
            icon: "success",
            title: message,
            toast: true,
            position: "top-end",
            showConfirmButton: false,
            timer: 2000,
            timerProgressBar: true,
          });
        } else {
          throw new Error("Invalid response format");
        }
      } catch (error) {
        console.error("❌ Save error:", error);

        Swal.fire({
          icon: "error",
          title: "خطا در ذخیره‌سازی",
          text: error.detail || "لطفاً دوباره تلاش کنید",
          confirmButtonText: "باشه",
          confirmButtonColor: "#ef4444",
        });
      }
    },

    shareLink() {
      const url = window.location.href;

      navigator.clipboard
        .writeText(url)
        .then(() => {
          Swal.fire({
            icon: "success",
            title: "لینک کپی شد",
            text: "لینک این نسخه در کلیپ‌بورد شما کپی شد",
            toast: true,
            position: "top-end",
            showConfirmButton: false,
            timer: 2000,
            timerProgressBar: true,
          });
        })
        .catch(() => {
          Swal.fire({
            icon: "error",
            title: "خطا",
            text: "خطا در کپی لینک",
            confirmButtonText: "باشه",
          });
        });
    },

    scrollToQuestion() {
      const questionBox = document.getElementById("question-section");
      if (questionBox) {
        questionBox.scrollIntoView({ behavior: "smooth", block: "start" });
      }

    },

    copyDrugCode(code) {
      navigator.clipboard.writeText(code).then(() => {
        Swal.fire({
          icon: "success",
          title: "کپی شد",
          text: `کد ${code} کپی شد`,
          toast: true,
          position: "top-end",
          showConfirmButton: false,
          timer: 1500,
        });
      });
    },

    showFullDescription(description) {
      if (description && description.length > 30) {
        this.fullDescription = description;
        this.showDescriptionModal = true;
      }
    },

    truncateDescription(text, maxLength = 100) {
      if (!text) return "-";
      if (text.length <= maxLength) return text;
      return text.substring(0, maxLength) + "...";
    },

    async submitQuestion() {
      if (!this.isPremiumUser) {
        this.showUpgradeModal();
        return;
      }

      if (!this.questionText.trim()) {
        Swal.fire({
          icon: "warning",
          title: "هشدار",
          text: "لطفاً سوال خود را بنویسید",
          confirmButtonText: "باشه",
        });
        return;
      }

      try {
        this.questionSubmitting = true;

        const questionData = {
          question: this.questionText,
          prescription_slug: this.prescription.slug,
          user_profile: this.userProfile,
        };

        await API.prescriptions.submitQuestion(
          this.prescription.slug,
          questionData
        );

        Swal.fire({
          icon: "success",
          title: "سوال ارسال شد",
          text: "سوال شما با موفقیت ثبت شد و به زودی پاسخ داده می‌شود",
          confirmButtonText: "باشه",
          confirmButtonColor: "#0077b6",
        });

        this.questionText = "";
      } catch (error) {
        Swal.fire({
          icon: "error",
          title: "خطا",
          text: "خطا در ارسال سوال. لطفاً دوباره تلاش کنید",
          confirmButtonText: "باشه",
        });
      } finally {
        this.questionSubmitting = false;
      }
    },

    showUpgradeModal() {
      Swal.fire({
        title: "ویژه کاربران Premium",
        html: `
                    <div class="text-center">
                        <i class="fas fa-crown text-6xl text-amber-500 mb-4"></i>
                        <p class="mb-4">برای ارسال سوال نیاز به اشتراک ویژه دارید</p>
                        <p class="text-sm text-gray-600">با خرید اشتراک ویژه می‌توانید از متخصصین سوال بپرسید</p>
                    </div>
                `,
        showCancelButton: true,
        confirmButtonText: "خرید اشتراک ویژه",
        cancelButtonText: "بستن",
        confirmButtonColor: "#f59e0b",
        cancelButtonColor: "#6b7280",
      }).then((result) => {
        if (result.isConfirmed) {
          window.location.href = "/plan";
        }
      });
    },

    getTextColor(bgClass) {
      if (!bgClass) return "";
      return bgClass.replace("bg-", "text-");
    },

    getBorderColor(bgClass) {
      if (!bgClass) return "";
      return bgClass.replace("bg-", "border-");
    },

    getBgColorStyle(colorCode) {
      if (!colorCode) return "";
      const colorMap = {
        "bg-red-500": "#ef4444",
        "bg-blue-500": "#3b82f6",
        "bg-green-500": "#22c55e",
        "bg-yellow-500": "#eab308",
        "bg-purple-500": "#a855f7",
        "bg-pink-500": "#ec4899",
        "bg-indigo-500": "#6366f1",
        "bg-orange-500": "#f97316",
        "bg-teal-500": "#14b8a6",
        "bg-cyan-500": "#06b6d4",
      };
      return colorMap[colorCode] || "#3b82f6";
    },

    initSecurityMeasures() {
      document.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        return false;
      });

      document.addEventListener("keyup", (e) => {
        if (e.key === "PrintScreen") {
          navigator.clipboard.writeText("");
          Swal.fire({
            icon: "warning",
            title: "غیرمجاز",
            text: "اسکرین‌شات از این صفحه مجاز نیست",
            toast: true,
            position: "top-end",
            showConfirmButton: false,
            timer: 2000,
          });
        }
      });

      document.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "p") {
          e.preventDefault();
          Swal.fire({
            icon: "warning",
            title: "غیرمجاز",
            text: "چاپ این صفحه مجاز نیست",
            toast: true,
            position: "top-end",
            showConfirmButton: false,
            timer: 2000,
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

      this.prescription.prescription_drugs.forEach((drug) => {
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
      if (groupNumber == 0) return "داروهای بدون گروه";
      return `گروه ${groupNumber}`;
    },

    getBorderClasses(drug) {
      let classes = [];

      if (drug.is_combination) {
        classes.push("border-r-4 border-r-purple-600");
      }

      if (drug.is_substitute) {
        classes.push("border-r-4 border-r-lime-600");
      }

      return classes.join(" ");
    },
    // ✨ این متد رو async کن
    async checkPremiumStatus() {
      try {
        const userProfile = await StorageManager.getUserProfile(); // حالا async شد

        if (!userProfile) {
          console.log("❌ No user profile found");
          this.isPremiumUser = false;
          return false;
        }

        const isPremium =
          userProfile.role === "premium" || userProfile.role === "admin";
        console.log("👑 Premium Status:", isPremium);
        console.log("🎭 User Role:", userProfile.role);

        this.isPremiumUser = isPremium;
        this.userProfile = userProfile;

        return isPremium;
      } catch (error) {
        console.error("❌ Error checking premium status:", error);
        this.isPremiumUser = false;
        return false;
      }
    },

    // تست کامل Premium Status
    testPremiumStatus() {
      console.log("🧪 Starting Premium Status Test...");
      console.log("─────────────────────────────────");

      // تست 1: خواندن مستقیم از localStorage
      const rawData = localStorage.getItem("drcode_user_profile");
      console.log("Test 1 - Raw Data:", rawData);

      // تست 2: Parse کردن
      try {
        const parsed = JSON.parse(rawData);
        console.log("Test 2 - Parsed Data:", parsed);
        console.log("Test 2 - Role Field:", parsed?.role);
        console.log("Test 2 - Role Type:", typeof parsed?.role);
      } catch (e) {
        console.error("Test 2 - Parse Error:", e);
      }

      // تست 3: چک کردن شرط
      const result = this.checkPremiumStatus();
      console.log("Test 3 - Final Result:", result);
      console.log("Test 3 - isPremiumUser:", this.isPremiumUser);

      console.log("─────────────────────────────────");
      console.log("🧪 Test Completed!");

      // نمایش نتیجه در UI
      if (this.isPremiumUser) {
        console.log("✅ SUCCESS: Premium User Detected!");
        alert("✅ شما کاربر Premium هستید!");
      } else {
        console.log("❌ FAILED: Not a Premium User");
        alert("❌ شما کاربر Premium نیستید یا اطلاعات یافت نشد");
      }
    },
    async init() {
      const slug = this.getSlugFromURL();

      if (!slug) {
        window.location.href = "/prescriptions";
        return;
      }
      
      let userData
      userData = StorageManager.getUserData();
      try {
        userData=JSON.parse(localStorage.getItem("drcode_user_profile")).data
      } catch (error) {
        
      }
      console.log(userData?.medical_code);
      
      // چک کردن وضعیت Premium
      this.checkPremiumStatus();

      this.userProfile = userData;

      if (userData?.medical_code) {
        this.watermarkText = userData.medical_code;
      } else {
        this.watermarkText = "DrCode-med.ir";
      }


      await this.loadPrescription(slug);
      await this.loadDescription(slug);

      this.initSecurityMeasures();
      this.initGallery();
      this.initCopyTutorial();
    },

    // Check if user is Premium
    checkPremiumStatus() {
      try {
        const userProfile =JSON.parse(localStorage.getItem("drcode_user_profile")).data
        console.log(userProfile);

        if (!userProfile) {
          console.log("❌ No user profile found");
          this.isPremiumUser = false;
          return false;
        }

        /*
{"success":true,"data":{"user_full_name":"mmmm rrrr","user_phone":"09911234567","role":"premium","medical_code":"DR-CODE","auth_status":"APPROVED","auth_status_display":"تایید شده","rejection_reason":null,"subscription_end_date":null,"created_at":"2025-11-10T14:00:16.108990Z","updated_at":"2025-11-10T15:22:54.731861Z","has_uploaded_document":false}}
*/

        const isPremium =
          userProfile.role === "premium" || userProfile.role === "admin";
        console.log("👑 Premium Status:", isPremium);
        console.log("🎭 User Role:", userProfile.role);

        this.isPremiumUser = isPremium;
        this.userProfile = userProfile;

        return isPremium;
      } catch (error) {
        console.error("❌ Error checking premium status:", error);
        this.isPremiumUser = false;
        return false;
      }
    },

    // Scroll to Question Box
    scrollToQuestion() {
      const questionBox = document.getElementById("question-section");
      if (questionBox && typeof scroll !== "undefined") {
        scroll.animateScroll(questionBox);
      } else if (questionBox) {
        // Fallback اگر SmoothScroll لود نشده بود
        questionBox.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    },

    // Submit Question
    async submitQuestion() {
      if (!this.isPremiumUser) {
        this.showUpgradeModal();
        return;
      }

      const trimmedQuestion = this.questionText.trim();

      if (!trimmedQuestion) {
        Swal.fire({
          icon: "warning",
          title: "هشدار",
          text: "لطفاً سوال خود را بنویسید",
          confirmButtonText: "باشه",
        });
        return;
      }

      if (trimmedQuestion.length < 10) {
        Swal.fire({
          icon: "warning",
          title: "هشدار",
          text: "سوال شما باید حداقل ۱۰ کاراکتر باشد.",
          confirmButtonText: "باشه",
        });
        return;
      }

      if (trimmedQuestion.length > 1000) {
        Swal.fire({
          icon: "warning",
          title: "هشدار",
          text: "حداکثر طول سوال ۱۰۰۰ کاراکتر است.",
          confirmButtonText: "باشه",
        });
        return;
      }
      try {
        this.questionSubmitting = true;

        const responseData = await API.prescriptions.submitQuestion(
          this.prescription.id,
          this.questionText
        );

        Swal.fire({
          icon: "success",
          title: "سوال شما ارسال شد",
          text:
            responseData.message ||
            "سوال شما با موفقیت ثبت شد و به زودی پاسخ داده می‌شود.",
          confirmButtonText: "باشه",
          confirmButtonColor: "#0077b6",
        });

        this.questionText = "";
      } catch (error) {
        let errorMessage = "خطا در ارسال سوال. لطفاً دوباره تلاش کنید.";

        if (error.response && error.response.data) {
          const errorData = error.response.data;
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (errorData.question_text) {
            errorMessage = errorData.question_text[0];
          } else if (typeof errorData === "object") {
            // تلاش برای یافتن اولین پیام خطا در آبجکت
            const firstErrorKey = Object.keys(errorData)[0];
            errorMessage = `${firstErrorKey}: ${errorData[firstErrorKey][0]}`;
          }
        }

        Swal.fire({
          icon: "error",
          title: "خطا",
          text: errorMessage,
          confirmButtonText: "باشه",
        });
      } finally {
        this.questionSubmitting = false;
      }
    },

    /* ============================================================
    🎓 Tutorial: Spotlight روی اولین کد دارو
    ============================================================ */
    initCopyTutorial() {
        try {
            this.copyTutorialDismissed =
                localStorage.getItem("drcode_copy_tutorial_dismissed") === "1";
        } catch (e) {
            this.copyTutorialDismissed = false;
        }

        if (this.copyTutorialDismissed) {
            console.log("🎓 Copy tutorial: user already dismissed it.");
            return;
        }

        this.$nextTick(() => {
            setTimeout(() => this._setupCopyTutorialObserver(), 800);
        });
    },

    _setupCopyTutorialObserver() {
        const target = document.getElementById("prescription__section");
        if (!target) {
            setTimeout(() => this._setupCopyTutorialObserver(), 500);
            return;
        }

        if (this._copyTutorialObserver) {
            this._copyTutorialObserver.disconnect();
        }

        this._copyTutorialObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (
                        entry.isIntersecting &&
                        entry.intersectionRatio >= 0.4 &&
                        !this._copyTutorialShown &&
                        !this.copyTutorialDismissed
                    ) {
                        this._copyTutorialShown = true;
                        setTimeout(() => this._openCopyTutorial(), 450);
                    }
                });
            },
            {
                threshold: [0.4, 0.5, 0.6],
                rootMargin: "-15% 0px -15% 0px",
            }
        );

        this._copyTutorialObserver.observe(target);
        console.log("🎓 Copy tutorial observer started.");
    },

    _openCopyTutorial() {
        if (this.copyTutorialDismissed || this.showCopyTutorial) return;

        const target = this._findFirstDrugCodeCell();
        if (!target) {
            console.warn("🎓 Copy tutorial: no drug code cell found (yet).");
            setTimeout(() => {
                const retry = this._findFirstDrugCodeCell();
                if (retry && !this.copyTutorialDismissed) {
                    this.copyTutorialTarget = retry;
                    this._scrollAndShowTutorial(retry);
                }
            }, 800);
            return;
        }

        this.copyTutorialTarget = target;
        this._scrollAndShowTutorial(target);
    },

    _scrollAndShowTutorial(target) {
        // ۱. اول جدول را افقی اسکرول کن
        const scrollResult = this._scrollTableToCodeCell(target);
        this._copyTutorialTableScroller = scrollResult?.scroller || null;

        // ۲. بعد از اسکرول، آموزش را نمایش بده
        // (اگر اسکرول لازم نبود، فوراً؛ وگرنه کمی صبر کن)
        const delay = scrollResult?.scrolled ? 700 : 50;

        setTimeout(() => {
            if (this.copyTutorialDismissed || this.showCopyTutorial) return;
            this._updateCopyTutorialPosition();
            this.showCopyTutorial = true;
            document.body.classList.add("modal-open");
            this._bindCopyTutorialListeners();
            console.log("🎓 Copy tutorial opened on code cell");
        }, delay);
    },

    _findFirstDrugCodeCell() {
        // جدول‌های داخل سکشن داروها را می‌گردیم
        const rows = document.querySelectorAll(
            "#prescription__section table tbody tr"
        );
        for (const row of rows) {
            const cells = row.querySelectorAll("td");
            if (cells.length < 3) continue;
            // ستون سوم (index 2) = کد دارو
            const codeCell = cells[2];
            // چک کن که واقعاً کد داره (نه «بدون کد»)
            const hasCode =
                codeCell.querySelector("span.font-mono") ||
                codeCell.querySelector("button[title*='کپی']");
            if (hasCode) return codeCell;
        }
        return null;
    },

    /* ============================================================
    📱 اسکرول افقی جدول تا سلول کد دارو در دید قرار بگیرد
    ============================================================ */
    _scrollTableToCodeCell(cell) {
        if (!cell) return null;

        // پیدا کردن نزدیک‌ترین اسکرولر افقی
        let scroller = cell.closest('.overflow-x-auto');
        if (!scroller) {
            let el = cell.parentElement;
            while (el && el !== document.body) {
                const style = getComputedStyle(el);
                if (
                    (style.overflowX === 'auto' || style.overflowX === 'scroll') &&
                    el.scrollWidth > el.clientWidth + 2
                ) {
                    scroller = el;
                    break;
                }
                el = el.parentElement;
            }
        }

        if (!scroller) {
            console.log("🎓 No horizontal scroller found for tutorial cell");
            return null;
        }

        // چک کن آیا سلول در دید افقی هست
        const cellRect = cell.getBoundingClientRect();
        const scrollerRect = scroller.getBoundingClientRect();
        const padding = 20;

        const isFullyVisible =
            cellRect.left >= scrollerRect.left + padding &&
            cellRect.right <= scrollerRect.right - padding;

        if (isFullyVisible) {
            console.log("🎓 Code cell already in horizontal view");
            return { scroller, scrolled: false };
        }

        // اسکرول افقی به مرکز
        // block: 'nearest' → اگر عمودی در دید است، اسکرول عمودی نمی‌کند
        // inline: 'center' → سلول در مرکز افقی scroller قرار می‌گیرد
        cell.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
            inline: 'center',
        });

        console.log("🎓 Scrolling table horizontally to show code cell");
        return { scroller, scrolled: true };
    },

    _updateCopyTutorialPosition() {
        if (!this.copyTutorialTarget) return;
        const rect = this.copyTutorialTarget.getBoundingClientRect();

        // اگر هدف از دید خارج شد، آموزش را ببند
        if (rect.bottom < 0 || rect.top > window.innerHeight) {
            this.showCopyTutorial = false;
            return;
        }

        // 🆕 چک افقی — اگر سلول کاملاً بیرون از viewport رفت
        const padding = 10;
        const isHorizontallyVisible =
            rect.right > padding && rect.left < window.innerWidth - padding;

        if (!isHorizontallyVisible) {
            this.showCopyTutorial = false;
            return;
        }

        const pad = 12;
        const gap = 16;
        const tooltipW = Math.min(320, window.innerWidth - 32);
        const tooltipH = 180; // تقریبی برای محاسبه فضا

        // تعیین موقعیت عمودی tooltip
        const spaceBelow = window.innerHeight - rect.bottom;
        const spaceAbove = rect.top;
        let position = "below";
        let tooltipTop;

        if (spaceBelow >= tooltipH + gap + pad) {
            position = "below";
            tooltipTop = rect.bottom + gap;
        } else if (spaceAbove >= tooltipH + gap + pad) {
            position = "above";
            tooltipTop = rect.top - tooltipH - gap;
        } else {
            position = "below";
            tooltipTop = Math.min(
                window.innerHeight - tooltipH - pad,
                rect.bottom + gap
            );
            tooltipTop = Math.max(pad, tooltipTop);
        }

        // موقعیت افقی tooltip
        let tooltipLeft = rect.left + rect.width / 2 - tooltipW / 2;
        tooltipLeft = Math.max(
            pad,
            Math.min(window.innerWidth - tooltipW - pad, tooltipLeft)
        );

        // موقعیت فلش نسبت به tooltip
        const targetCenterX = rect.left + rect.width / 2;
        let arrowLeft = targetCenterX - tooltipLeft - 7;
        arrowLeft = Math.max(20, Math.min(tooltipW - 34, arrowLeft));

        this.copyTutorialRect = {
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height,
        };

        this.copyTutorialTooltip = {
            top: tooltipTop,
            left: tooltipLeft,
            width: tooltipW,
            position: position,
            arrowLeft: arrowLeft,
        };
    },

    _bindCopyTutorialListeners() {
        // پاکسازی listenerهای قبلی
        this._unbindCopyTutorialListeners();

        this._copyTutorialScrollHandler = () => this._updateCopyTutorialPosition();

        // اسکرول عمودی صفحه
        window.addEventListener("scroll", this._copyTutorialScrollHandler, {
            passive: true,
        });

        // resize
        window.addEventListener("resize", this._copyTutorialScrollHandler, {
            passive: true,
        });

        // 🆕 اسکرول افقی جدول — تا اگر کاربر جدول رو خودش اسکرول کرد،
        // spotlight همراهش حرکت کنه
        if (this._copyTutorialTableScroller) {
            this._copyTutorialTableScroller.addEventListener(
                "scroll",
                this._copyTutorialScrollHandler,
                { passive: true }
            );
        }
    },

    _unbindCopyTutorialListeners() {
        if (!this._copyTutorialScrollHandler) return;

        window.removeEventListener("scroll", this._copyTutorialScrollHandler);
        window.removeEventListener("resize", this._copyTutorialScrollHandler);

        if (this._copyTutorialTableScroller) {
            this._copyTutorialTableScroller.removeEventListener(
                "scroll",
                this._copyTutorialScrollHandler
            );
            this._copyTutorialTableScroller = null;
        }

        this._copyTutorialScrollHandler = null;
    },

    closeCopyTutorial(dontShowAgain = false) {
        this.showCopyTutorial = false;
        this.copyTutorialTarget = null;
        document.body.classList.remove("modal-open");

        this._unbindCopyTutorialListeners();

        if (dontShowAgain) {
            this.copyTutorialDismissed = true;
            try {
                localStorage.setItem("drcode_copy_tutorial_dismissed", "1");
            } catch (e) {
                console.warn("localStorage write failed:", e);
            }
        }

        if (this._copyTutorialObserver) {
            this._copyTutorialObserver.disconnect();
            this._copyTutorialObserver = null;
        }
    },
  };
}
// نسخه بهبود یافته برای Alpine.js
function createProtectedWatermark() {
  let watermarkAdded = false;

  function addWatermark() {
    const targetSection = document.getElementById("prescription__section");

    // بررسی دقیق‌تر وضعیت نمایش سکشن
    if (!targetSection) {
      console.log("Section not found");
      return;
    }

    const style = getComputedStyle(targetSection);
    if (
      style.display === "none" ||
      style.visibility === "hidden" ||
      targetSection.offsetHeight === 0
    ) {
      console.log("Section is hidden");
      return;
    }

    const existing = targetSection.querySelector("#protected-watermark");
    if (existing) {
      console.log("Watermark already exists");
      return;
    }

    console.log("Adding watermark...");

    const watermark = document.createElement("div");
    watermark.id = "protected-watermark";
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
    if (computedStyle.position === "static") {
      targetSection.style.position = "relative";
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

    const container = document.createElement("div");
    container.style.cssText = `
            position: relative;
            width: 100%;
            height: 100%;
            `;
            let medi
            let mediObject
    try {
        medi = localStorage.getItem("drcode_user_profile")
        mediObject = JSON.parse(medi).data
        } catch (error) {
            
        }

    // alert(!!null)
    for (let row = 1; row <= rows; row++) {
      for (let col = 1; col <= cols; col++) {
        const text = document.createElement("div");
        if (medi){
            text.textContent = medi ? mediObject.medical_code : "drcode-med.ir";
        }else{
            text.textContent = "drcode-med.ir";
        }

        text.style.cssText = `
                    position: absolute;
                    top: ${row * rowSpacing}px;
                    left: ${col * colSpacing}px;
                    transform: translate(-50%, -50%) rotate(-45deg);
                    font-size: ${isMobile ? "34px" : "40px"};
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
    console.log("Watermark added successfully");
  }

  // تلاش مداوم برای اضافه کردن واترمارک
  function keepTrying() {
    const targetSection = document.getElementById("prescription__section");
    if (targetSection) {
      const style = getComputedStyle(targetSection);
      if (
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        targetSection.offsetHeight > 0
      ) {
        if (!targetSection.querySelector("#protected-watermark")) {
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
  const bodyObserver = new MutationObserver(function (mutations) {
    keepTrying();
  });

  bodyObserver.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["style", "x-show", "class"],
  });

  // محافظت در برابر حذف
  const sectionObserver = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.removedNodes.forEach(function (node) {
        if (node.id === "protected-watermark") {
          console.log("Watermark removed, re-adding...");
          setTimeout(addWatermark, 50);
        }
      });
    });
  });

  // شروع observer برای سکشن با تلاش مداوم
  let observerStarted = false;
  const startSectionObserver = setInterval(function () {
    const targetSection = document.getElementById("prescription__section");
    if (targetSection && !observerStarted) {
      sectionObserver.observe(targetSection, {
        childList: true,
        subtree: true,
      });
      observerStarted = true;
      keepTrying();
      console.log("Section observer started");
    }
  }, 50);

  // توقف بعد از 5 ثانیه
  setTimeout(function () {
    clearInterval(startSectionObserver);
  }, 5000);

  // مدیریت resize
  let resizeTimeout;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function () {
      const targetSection = document.getElementById("prescription__section");
      if (!targetSection) return;

      const existing = targetSection.querySelector("#protected-watermark");
      if (existing) existing.remove();
      addWatermark();
    }, 300);
  });

  // بررسی دوره‌ای هر 2 ثانیه
  setInterval(function () {
    keepTrying();
  }, 2000);

  // رویداد Alpine.js (اگر در دسترس باشد)
  document.addEventListener("alpine:initialized", function () {
    console.log("Alpine initialized");
    setTimeout(keepTrying, 200);
    setTimeout(keepTrying, 500);
  });

  // رویداد scroll (گاهی Alpine با scroll فعال می‌شود)
  let scrollTimeout;
  window.addEventListener(
    "scroll",
    function () {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(keepTrying, 100);
    },
    { passive: true }
  );
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", createProtectedWatermark);
} else {
  createProtectedWatermark();
}


