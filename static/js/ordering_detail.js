// =============================================================================
// Order Detail Page — Alpine.js Controller
// =============================================================================
// این فایل، نسخه اوردر از منطق صفحه prescription_detail.js است و همان قوانین
// (حفاظت محتوا، تم رنگی داینامیک، گیت پریمیوم برای سوالات) را رعایت می‌کند.
//
// ⚠️ پیش‌نیاز Backend Client:
// این فایل فرض می‌کند یک namespace به نام `API.ordering` در فایل مرکزی api.js
// شما تعریف شده (دقیقا هم‌خانواده با API.prescriptions). اگر هنوز اضافه نشده،
// این متدها را به api.js اضافه کنید:
//
//   API.ordering = {
//     getBase:          (slug) => API.get(`/ordering/${slug}/base/`),
//     getDisposition:   (slug) => API.get(`/ordering/${slug}/disposition/`),
//     getDynamicFields: (slug) => API.get(`/ordering/${slug}/dynamic-fields/`),
//     getMedia:         (slug) => API.get(`/ordering/${slug}/media/`),
//     getSections:      (slug) => API.get(`/ordering/${slug}/sections/`),
//     toggleSave:       (slug) => API.post(`/ordering/${slug}/toggle-save/`),
//     submitQuestion:   (slug, data) => API.post(`/ordering/${slug}/question/`, data),
//   };
//
// (دو متد آخر روی API های واقعی شما هنوز مشخص نشده — مسیر فرضی گذاشتم، اگر
// فرق داره فقط همینجا اصلاحش کن.)
// =============================================================================

// رنگ‌ها از بک‌اند بصورت کد هگز می‌آیند (مثلاً "#ec4899")، نه دیگر اسم
// تیلویندی. این تابع فقط معتبر بودن فرمت هگز را چک می‌کند؛ منطق روشن/تیره و
// شفافیت‌سازی با color-mix() در CSS (کلاس‌های dyn-* / dsec-*) انجام می‌شود.
const ORDER_DEFAULT_COLOR = "#64748b"; // slate-500 — فال‌بک وقتی رنگ نامعتبر/خالی باشد

function isValidHexColor(value) {
  return typeof value === "string" && /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(value.trim());
}

function orderDetailApp() {
  return {
    // ----- State -----
    order: null,
    loading: true,
    isSaved: false,
    isPremiumUser: false,
    userProfile: null,

    questionText: "",
    questionSubmitting: false,

    fieldModal: { open: false, title: "", subtitle: "", content: "" },

    watermarkText: "drcode-med.ir",

    // فاز بعدی — فقط نگه‌دارنده state، هنوز fetch/render نمی‌شوند
    disposition: null,
    dynamicFields: null,
    media: null,
    sections: null,

    // ----- Init -----
    async init() {
      const slug = this.getSlugFromURL();

      if (!slug) {
        window.location.href = "/orders";
        return;
      }

      let userData = null;
      try {
        userData = JSON.parse(localStorage.getItem("drcode_user_profile"))?.data;
      } catch (e) {
        userData = null;
      }

      this.checkPremiumStatus();
      this.userProfile = userData;
      this.watermarkText = userData?.medical_code || "DrCode-med.ir";

      await this.loadOrderBase(slug);
      this.initSecurityMeasures();

      // فاز بعدی (وقتی اسکیمای پاسخ این 3 تا رو دادی فعالشون می‌کنم):
      // await this.loadDisposition(slug);
      // await this.loadDynamicFields(slug);
      // await this.loadMedia(slug);

      // ✅ فعال — sections API آماده است
      await this.loadSections(slug);
    },

    getSlugFromURL() {
      // به جای فرض‌کردن پیشوند مسیر (/orders/ یا /ordering/)، آخرین تکه‌ی
      // غیرخالی از مسیر رو به‌عنوان slug برمی‌داریم — مستقل از روتینگ شما.
      const path = window.location.pathname;
      const segments = path.split("/").filter(Boolean);
      return segments.length ? segments[segments.length - 1] : null;
    },

    // ----- Data Loading -----
    async loadOrderBase(slug) {
      try {
        this.loading = true;
        const response = await API.ordering.getBase(slug);
        this.order = response;
        this.isSaved = response.is_saved || false;
      } catch (error) {
        console.error("Error loading order:", error);
        const errorMessage =
          (error.response && error.response.data && error.response.data.detail) ||
          "خطا در بارگذاری اطلاعات اوردر. آدرس ممکن است اشتباه باشد.";

        Swal.fire({
          icon: "error",
          title: "خطا",
          text: errorMessage,
          confirmButtonText: "بازگشت",
          confirmButtonColor: "#0077b6",
        }).then(() => {
          setTimeout(() => {
            // window.location.href = "/orders";
          }, 3000);
        });
      } finally {
        this.loading = false;
      }
    },

    // فاز بعدی — استاب آماده، صرفا منتظر اسکیمای پاسخ
    async loadDisposition(slug) {
      try {
        this.disposition = await API.ordering.getDisposition(slug);
      } catch (e) {
        console.error("Error loading disposition tree:", e);
      }
    },
    async loadDynamicFields(slug) {
      try {
        this.dynamicFields = await API.ordering.getDynamicFields(slug);
      } catch (e) {
        console.error("Error loading dynamic fields:", e);
      }
    },
    async loadMedia(slug) {
      try {
        this.media = await API.ordering.getMedia(slug);
      } catch (e) {
        console.error("Error loading media:", e);
      }
    },
    async loadSections(slug) {
      try {
        this.sections = await API.ordering.getSections(slug);
      } catch (e) {
        console.error("Error loading sections:", e);
      }
    },

    // ----- Derived / Display Helpers -----
    infoFields() {
      if (!this.order) return [];
      return [
        {
          key: "imp",
          icon: "fa-stethoscope",
          labelEn: "Impression",
          labelFa: "تشخیص اصلی",
          value: this.order.imp,
          notes: this.order.imp_notes,
        },
        {
          key: "condition",
          icon: "fa-diagram-project",
          labelEn: "Condition",
          labelFa: "وضعیت بیمار",
          value: this.order.condition,
          notes: this.order.condition_notes,
        },
        {
          key: "diet",
          icon: "fa-utensils",
          labelEn: "Diet",
          labelFa: "رژیم غذایی",
          value: this.order.diet,
          notes: this.order.diet_notes,
        },
        {
          key: "action",
          icon: "fa-hand-holding-medical",
          labelEn: "Action",
          labelFa: "اقدام",
          value: this.order.action,
          notes: this.order.action_notes,
        },
        {
          key: "position",
          icon: "fa-bed",
          labelEn: "Position",
          labelFa: "وضعیت قرارگیری",
          value: this.order.position,
          notes: this.order.position_notes,
        },
      ];
    },

    // تم رنگی داینامیک بر اساس order.color (کد هگز) — مجزا از رنگ دسته‌بندی (category.color_code)
    // رنگ واقعی با :style روی --theme-c ست می‌شه و کلاس‌های dyn-* (تعریف‌شده در
    // <style> صفحه) با color-mix() روشنی/شفافیت مناسب رو از همون رنگ می‌سازن.
    theme() {
      const c = isValidHexColor(this.order?.color) ? this.order.color.trim() : ORDER_DEFAULT_COLOR;
      return {
        name: c,
        color: c,
        style: `--theme-c: ${c};`,
        dot: "dyn-dot",
        gradient: "dyn-gradient",
        gradientText: "dyn-gradient-text",
        softBg: "dyn-soft-bg",
        softBorder: "dyn-soft-border",
        iconBg: "dyn-icon-bg",
        iconText: "dyn-icon-text",
        ring: "dyn-ring",
        chip: "dyn-chip",
        hoverBorder: "dyn-hover-border",
        hoverText: "dyn-hover-text",
        headerAccent: "dyn-header-accent",
        primaryBtn: "dyn-primary-btn",
        glow: "dyn-glow",
      };
    },

    // ----- Section / Item Helpers -----

    // تم رنگی داینامیک بر اساس رنگ هر section (کد هگز، مستقل از تم کلی اوردر)
    // رنگ واقعی با :style روی --section-c همون wrapper section ست می‌شه و
    // کلاس‌های dsec-* با color-mix() نسخه‌های روشن/تیره/شفاف می‌سازن.
    sectionTheme(color) {
      const c = isValidHexColor(color) ? color.trim() : ORDER_DEFAULT_COLOR;
      return {
        name: c,
        color: c,
        style: `--section-c: ${c};`,
        gradient: "dsec-gradient",
        softBg: "dsec-soft-bg",
        softBorder: "dsec-soft-border",
        iconBg: "dsec-icon-bg",
        iconText: "dsec-icon-text",
        headerBorder: "dsec-header-border",
        chip: "dsec-chip",
        conditionBg: "dsec-condition-bg",
        conditionBorder: "dsec-condition-border",
        conditionText: "dsec-condition-text",
        drugBg: "dsec-drug-bg",
        drugBorder: "dsec-drug-border",
        drugCodeText: "dsec-drug-code-text",
      };
    },

    // آیتم‌هایی که شرط دارند را گروه‌بندی می‌کند:
    // خروجی: آرایه‌ای از { condition: obj|null, items: [...] }
    groupItemsByCondition(items) {
      if (!items || items.length === 0) return [];

      const groups = [];
      const conditionMap = new Map(); // conditionId → group index

      items.forEach((item) => {
        if (!item.conditions || item.conditions.length === 0) {
          // آیتم بدون شرط → گروه null
          let nullGroup = groups.find((g) => g.condition === null);
          if (!nullGroup) {
            nullGroup = { condition: null, items: [] };
            groups.push(nullGroup);
          }
          nullGroup.items.push(item);
        } else {
          // هر شرط جداگانه نمایش داده می‌شود (یک آیتم می‌تواند زیر چند شرط باشد)
          item.conditions.forEach((cond) => {
            if (!conditionMap.has(cond.id)) {
              conditionMap.set(cond.id, groups.length);
              groups.push({ condition: cond, items: [] });
            }
            groups[conditionMap.get(cond.id)].items.push(item);
          });
        }
      });

      return groups;
    },

    isLong(text, max = 130) {
      return !!text && text.length > max;
    },

    showFieldModal(field) {
      this.fieldModal = {
        open: true,
        title: field.labelFa,
        subtitle: field.labelEn,
        content: field.value || "",
      };
    },

    showNotesModal() {
      this.fieldModal = {
        open: true,
        title: "یادداشت تکمیلی اوردر",
        subtitle: "",
        content: this.order?.notes || "",
      };
    },

    closeFieldModal() {
      this.fieldModal.open = false;
    },

    // ----- Actions -----
    async toggleSave() {
      if (!StorageManager.isLoggedIn()) {
        Auth.showAuthModal();
        return;
      }

      try {
        const response = await API.ordering.toggleSave(this.order.slug);

        if (response.is_saved !== undefined) {
          this.isSaved = response.is_saved;
          Swal.fire({
            icon: "success",
            title: this.isSaved ? "اوردر ذخیره شد ✅" : "اوردر از لیست حذف شد ❌",
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
        console.error("Save error:", error);
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
            text: "لینک این اوردر در کلیپ‌بورد شما کپی شد",
            toast: true,
            position: "top-end",
            showConfirmButton: false,
            timer: 2000,
            timerProgressBar: true,
          });
        })
        .catch(() => {
          Swal.fire({ icon: "error", title: "خطا", text: "خطا در کپی لینک", confirmButtonText: "باشه" });
        });
    },

    copySlug() {
      if (!this.order?.slug) return;
      navigator.clipboard.writeText(this.order.slug).then(() => {
        Swal.fire({
          icon: "success",
          title: "کپی شد",
          text: `شناسه ${this.order.slug} کپی شد`,
          toast: true,
          position: "top-end",
          showConfirmButton: false,
          timer: 1500,
        });
      });
    },

    scrollToQuestion() {
      const questionBox = document.getElementById("order-question-section");
      if (questionBox) {
        questionBox.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    },

    checkPremiumStatus() {
      try {
        const userProfile = JSON.parse(localStorage.getItem("drcode_user_profile"))?.data;

        if (!userProfile) {
          this.isPremiumUser = false;
          return false;
        }

        const isPremium = userProfile.role === "premium" || userProfile.role === "admin";
        this.isPremiumUser = isPremium;
        this.userProfile = userProfile;
        return isPremium;
      } catch (error) {
        console.error("Error checking premium status:", error);
        this.isPremiumUser = false;
        return false;
      }
    },

    async submitQuestion() {
      if (!this.isPremiumUser) {
        this.showUpgradeModal();
        return;
      }

      const trimmed = this.questionText.trim();

      if (!trimmed) {
        Swal.fire({ icon: "warning", title: "هشدار", text: "لطفاً سوال خود را بنویسید", confirmButtonText: "باشه" });
        return;
      }
      if (trimmed.length < 10) {
        Swal.fire({
          icon: "warning",
          title: "هشدار",
          text: "سوال شما باید حداقل ۱۰ کاراکتر باشد.",
          confirmButtonText: "باشه",
        });
        return;
      }
      if (trimmed.length > 1000) {
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

        const responseData = await API.ordering.submitQuestion(this.order.id, this.questionText);

        Swal.fire({
          icon: "success",
          title: "سوال شما ارسال شد",
          text: responseData?.message || "سوال شما با موفقیت ثبت شد و به زودی پاسخ داده می‌شود.",
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
          } else if (errorData.question) {
            errorMessage = errorData.question[0];
          } else if (typeof errorData === "object") {
            const firstKey = Object.keys(errorData)[0];
            errorMessage = `${firstKey}: ${errorData[firstKey][0]}`;
          }
        }

        Swal.fire({ icon: "error", title: "خطا", text: errorMessage, confirmButtonText: "باشه" });
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
  };
}

// =============================================================================
// Watermark Protection — همان مکانیزم prescription_detail.js، روی #order__section
// =============================================================================
function createOrderProtectedWatermark() {
  let watermarkAdded = false;

  function addWatermark() {
    const targetSection = document.getElementById("order__section");
    if (!targetSection) return;

    const style = getComputedStyle(targetSection);
    if (style.display === "none" || style.visibility === "hidden" || targetSection.offsetHeight === 0) return;

    if (targetSection.querySelector("#order-protected-watermark")) return;

    const watermark = document.createElement("div");
    watermark.id = "order-protected-watermark";
    watermark.style.cssText = `
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      pointer-events: none; z-index: 10; overflow: hidden;
    `;

    const computedStyle = getComputedStyle(targetSection);
    if (computedStyle.position === "static") {
      targetSection.style.position = "relative";
    }

    const sectionRect = targetSection.getBoundingClientRect();
    const isMobile = window.innerWidth < 768;
    const cols = 4;
    const rows = 3;
    const colSpacing = sectionRect.width / (cols + 1);
    const rowSpacing = sectionRect.height / (rows + 1);

    const container = document.createElement("div");
    container.style.cssText = `position: relative; width: 100%; height: 100%;`;

    let medi, mediObject;
    try {
      medi = localStorage.getItem("drcode_user_profile");
      mediObject = JSON.parse(medi)?.data;
    } catch (e) {
      medi = null;
    }

    for (let row = 1; row <= rows; row++) {
      for (let col = 1; col <= cols; col++) {
        const text = document.createElement("div");
        text.textContent = medi && mediObject?.medical_code ? mediObject.medical_code : "drcode-med.ir";
        text.style.cssText = `
          position: absolute;
          top: ${row * rowSpacing}px;
          left: ${col * colSpacing}px;
          transform: translate(-50%, -50%) rotate(-45deg);
          font-size: ${isMobile ? "34px" : "40px"};
          font-weight: bold;
          color: rgba(0, 0, 0, 0.1);
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
  }

  function keepTrying() {
    const targetSection = document.getElementById("order__section");
    if (!targetSection) return;
    const style = getComputedStyle(targetSection);
    if (style.display !== "none" && style.visibility !== "hidden" && targetSection.offsetHeight > 0) {
      if (!targetSection.querySelector("#order-protected-watermark")) addWatermark();
    }
  }

  [100, 300, 500, 800, 1000, 1500, 2000].forEach((t) => setTimeout(keepTrying, t));

  const bodyObserver = new MutationObserver(() => keepTrying());
  bodyObserver.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["style", "x-show", "class"],
  });

  const sectionObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.removedNodes.forEach((node) => {
        if (node.id === "order-protected-watermark") setTimeout(addWatermark, 50);
      });
    });
  });

  let observerStarted = false;
  const startSectionObserver = setInterval(() => {
    const targetSection = document.getElementById("order__section");
    if (targetSection && !observerStarted) {
      sectionObserver.observe(targetSection, { childList: true, subtree: true });
      observerStarted = true;
      keepTrying();
    }
  }, 50);
  setTimeout(() => clearInterval(startSectionObserver), 5000);

  let resizeTimeout;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      const targetSection = document.getElementById("order__section");
      if (!targetSection) return;
      const existing = targetSection.querySelector("#order-protected-watermark");
      if (existing) existing.remove();
      addWatermark();
    }, 300);
  });

  setInterval(keepTrying, 2000);

  document.addEventListener("alpine:initialized", () => {
    setTimeout(keepTrying, 200);
    setTimeout(keepTrying, 500);
  });

  let scrollTimeout;
  window.addEventListener(
    "scroll",
    () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(keepTrying, 100);
    },
    { passive: true }
  );
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", createOrderProtectedWatermark);
} else {
  createOrderProtectedWatermark();
}