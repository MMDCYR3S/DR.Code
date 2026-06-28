// =============================================================================
// Order Detail Page — Alpine.js Controller
// =============================================================================
// تغییرات:
// ① Dynamic Fields → نام «پیش‌بالینی» و جابجایی قبل از اوردر (در HTML)
// ② Item numbering → item_number روی هر آیتم نمایش داده می‌شود
// ③ ساختار API: sections[].relationship_groups[].text_items / drug_items
// ④ groupItemsByCondition روی text_items و drug_items داخل هر relationship_group
// =============================================================================

const ORDER_DEFAULT_COLOR = "#64748b";

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

    fieldModal: { open: false, title: "", subtitle: "", content: "", isHtml: false },

    watermarkText: "drcode-med.ir",

    disposition: null,
    dynamicFields: null,
    media: null,
    sections: null,

    activePopover: null,
    popoverData: { title: "", content: "" },
    popoverStyle: "",
    popoverTheme: { style: "", iconTextStyle: "" },

    showBackToTop: false,

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
      this.initScrollListener();

      await this.loadDisposition(slug);
      await this.loadDynamicFields(slug);
      await this.loadSections(slug);
    },

    getSlugFromURL() {
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

    async loadDisposition(slug) {
      try {
        this.disposition = await API.ordering.getDisposition(slug);
        this.autoExpandDisposition();
      } catch (e) {
        console.error("Error loading disposition tree:", e);
      }
    },

    async loadDynamicFields(slug) {
      try {
        this.dynamicFields = await API.ordering.getDynamicFields(slug);
        this.autoExpandDynamicFields();
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

    // auto-expand اولین node از disposition
    autoExpandDisposition() {
      try {
        if (!this.disposition?.emergency_disposition?.nodes) return;
        const nodes = this.disposition.emergency_disposition.nodes;
        if (nodes.length > 0) {
          const firstWithChildren = nodes.find(n => n.children && n.children.length > 0);
          if (firstWithChildren) {
            firstWithChildren._open = true;
          } else {
            nodes[0]._open = true;
          }
        }
      } catch (e) {
        console.warn("autoExpandDisposition failed:", e);
      }
    },

    // auto-expand اولین node از هر group در dynamic fields
    autoExpandDynamicFields() {
      try {
        if (!this.dynamicFields?.dynamic_field_groups) return;
        this.dynamicFields.dynamic_field_groups.forEach(group => {
          if (!group.nodes || group.nodes.length === 0) return;
          const firstMeaningful = group.nodes.find(n =>
            (n.content && n.content.trim()) || (n.children && n.children.length > 0)
          );
          if (firstMeaningful) {
            firstMeaningful._open = true;
          } else {
            group.nodes[0]._open = true;
          }
        });
      } catch (e) {
        console.warn("autoExpandDynamicFields failed:", e);
      }
    },

    // ----- Popover Management -----
    togglePopover(event, id) {
      event.stopPropagation();
      event.preventDefault();

      if (this.activePopover === id) {
        this.closePopover();
        return;
      }

      const data = this.findPopoverContent(id);
      if (!data) return;

      const rect = event.currentTarget.getBoundingClientRect();
      const popoverWidth = 360;
      const popoverEstHeight = 200;
      const margin = 8;

      let left = rect.right - popoverWidth;
      if (left < margin) left = margin;
      if (left + popoverWidth > window.innerWidth - margin) {
        left = window.innerWidth - popoverWidth - margin;
      }

      let top = rect.bottom + margin;
      if (top + popoverEstHeight > window.innerHeight - margin) {
        top = rect.top - popoverEstHeight - margin;
        if (top < margin) top = margin;
      }

      this.popoverStyle = `top: ${top}px; left: ${left}px;`;
      this.popoverData = data;
      this.popoverTheme = data.theme || { style: "", iconTextStyle: "" };
      this.activePopover = id;
    },

    closePopover() {
      this.activePopover = null;
      this.popoverData = { title: "", content: "" };
      this.popoverStyle = "";
    },

    // یافتن محتوای popover بر اساس ID
    // ساختار جدید: sections[].relationship_groups[].text_items / drug_items
    findPopoverContent(id) {
      // field-{key}
      if (id.startsWith("field-")) {
        const key = id.replace("field-", "");
        const field = this.infoFields().find(f => f.key === key);
        if (field) {
          return {
            title: "توضیحات: " + field.labelFa,
            content: field.notes || "",
            theme: {
              style: `--theme-c: ${this.theme().color};`,
              iconTextStyle: `color: ${this.theme().color};`,
            },
          };
        }
      }

      // section-{id}
      if (id.startsWith("section-") && this.sections?.sections) {
        const secId = parseInt(id.replace("section-", ""));
        const section = this.sections.sections.find(s => s.id === secId);
        if (section) {
          const color = isValidHexColor(section.color) ? section.color : ORDER_DEFAULT_COLOR;
          return {
            title: "توضیحات بخش: " + section.title,
            content: section.notes || "",
            theme: {
              style: `--section-c: ${color}; background: color-mix(in srgb, ${color} 6%, white);`,
              iconTextStyle: `color: color-mix(in srgb, ${color} 72%, black);`,
            },
          };
        }
      }

      // item-{id} — جستجو در relationship_groups[].text_items
      if (id.startsWith("item-") && this.sections?.sections) {
        const itemId = parseInt(id.replace("item-", ""));
        for (const section of this.sections.sections) {
          if (!section.relationship_groups) continue;
          for (const rg of section.relationship_groups) {
            if (!rg.text_items) continue;
            const item = rg.text_items.find(i => i.id === itemId);
            if (item) {
              const color = isValidHexColor(section.color) ? section.color : ORDER_DEFAULT_COLOR;
              return {
                title: "توضیحات آیتم" + (item.item_number ? " #" + item.item_number : ""),
                content: item.notes || "",
                theme: {
                  style: `--section-c: ${color}; background: color-mix(in srgb, ${color} 6%, white);`,
                  iconTextStyle: `color: color-mix(in srgb, ${color} 72%, black);`,
                },
              };
            }
          }
        }
      }

      // drug-{id} — جستجو در relationship_groups[].drug_items
      if (id.startsWith("drug-") && this.sections?.sections) {
        const drugId = parseInt(id.replace("drug-", ""));
        for (const section of this.sections.sections) {
          if (!section.relationship_groups) continue;
          for (const rg of section.relationship_groups) {
            if (!rg.drug_items) continue;
            const drug = rg.drug_items.find(d => d.id === drugId);
            if (drug) {
              const color = isValidHexColor(section.color) ? section.color : ORDER_DEFAULT_COLOR;
              return {
                title: "توضیحات دارو: " + (drug.drug?.title || ""),
                content: drug.notes || "",
                theme: {
                  style: `--section-c: ${color}; background: color-mix(in srgb, ${color} 6%, white);`,
                  iconTextStyle: `color: color-mix(in srgb, ${color} 72%, black);`,
                },
              };
            }
          }
        }
      }

      // disp-{id}
      if (id.startsWith("disp-") && this.disposition?.emergency_disposition) {
        const disp = this.disposition.emergency_disposition;
        const color = isValidHexColor(disp.color) ? disp.color : ORDER_DEFAULT_COLOR;
        return {
          title: "توضیحات: " + (disp.title || ""),
          content: disp.notes || "",
          theme: {
            style: `--df-c: ${color}; background: color-mix(in srgb, ${color} 6%, white);`,
            iconTextStyle: `color: color-mix(in srgb, ${color} 72%, black);`,
          },
        };
      }

      return null;
    },

    // back-to-top
    initScrollListener() {
      const handleScroll = () => {
        this.showBackToTop = window.scrollY > 400;
      };
      window.addEventListener("scroll", handleScroll, { passive: true });
      handleScroll();
    },

    scrollToTop() {
      window.scrollTo({ top: 0, behavior: "smooth" });
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

    dfTheme(color) {
      const c = isValidHexColor(color) ? color.trim() : ORDER_DEFAULT_COLOR;
      return {
        style: `--df-c: ${c};`,
        gradient: "ddf-gradient",
        softBg: "ddf-soft-bg",
        softBorder: "ddf-soft-border",
        iconBg: "ddf-icon-bg",
        iconText: "ddf-icon-text",
        chip: "ddf-chip",
        headerBorder: "ddf-header-border",
        nodeBg: "ddf-node-bg",
        nodeBorder: "ddf-node-border",
        childBorder: "ddf-child-border",
      };
    },

    // ─────────────────────────────────────────────────────────────────────────
    // groupItemsByCondition
    // ورودی: آرایه‌ای از text_items یا drug_items (داخل یک relationship_group)
    // خروجی: گروه‌بندی براساس condition
    // ─────────────────────────────────────────────────────────────────────────
    groupItemsByCondition(items) {
      if (!items || items.length === 0) return [];

      const groups = [];
      const conditionMap = new Map();

      items.forEach((item) => {
        if (!item.conditions || item.conditions.length === 0) {
          let nullGroup = groups.find((g) => g.condition === null);
          if (!nullGroup) {
            nullGroup = { condition: null, items: [] };
            groups.push(nullGroup);
          }
          nullGroup.items.push(item);
        } else {
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
      this.fieldModal.isHtml = false;
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
        Swal.fire({ icon: "warning", title: "هشدار", text: "سوال شما باید حداقل ۱۰ کاراکتر باشد.", confirmButtonText: "باشه" });
        return;
      }
      if (trimmed.length > 1000) {
        Swal.fire({ icon: "warning", title: "هشدار", text: "حداکثر طول سوال ۱۰۰۰ کاراکتر است.", confirmButtonText: "باشه" });
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

        if (e.key === "Escape" && this.activePopover) {
          this.closePopover();
        }
      });
    },
  };
}

// =============================================================================
// Watermark Protection
// =============================================================================
function createOrderProtectedWatermark() {
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
      pointer-events: none; z-index: 1; overflow: hidden;
    `;

    const computedStyle = getComputedStyle(targetSection);
    if (computedStyle.position === "static") {
      targetSection.style.position = "relative";
    }

    const sectionRect = targetSection.getBoundingClientRect();
    const isMobile = window.innerWidth < 768;
    const cols = 5;
    const rows = 8;
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

    const text = (medi && mediObject?.medical_code) ? mediObject.medical_code : "drcode-med.ir";

    for (let row = 1; row <= rows; row++) {
      for (let col = 1; col <= cols; col++) {
        const textEl = document.createElement("div");
        textEl.textContent = text;
        textEl.style.cssText = `
          position: absolute;
          top: ${row * rowSpacing}px;
          left: ${col * colSpacing}px;
          transform: translate(-50%, -50%) rotate(-45deg);
          font-size: ${isMobile ? "22px" : "28px"};
          font-weight: 700;
          color: rgba(15, 23, 42, 0.06);
          white-space: nowrap;
          user-select: none;
          font-family: Arial, sans-serif;
        `;
        container.appendChild(textEl);
      }
    }

    watermark.appendChild(container);
    targetSection.insertBefore(watermark, targetSection.firstChild);
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