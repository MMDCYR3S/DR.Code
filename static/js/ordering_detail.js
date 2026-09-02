// =============================================================================
// Order Detail Page — Alpine.js Controller
// =============================================================================
// نسخه: ۲.۰ — بازنویسی کامل فرانت
//
// تغییرات کلیدی:
// ① تمامی API ها: base / disposition / dynamic-fields / sections
// ② فیکس باگ رندر ungrouped_items و ungrouped_drug_items در sections
// ③ نمایش aliases و primary_name
// ④ سایدبار شناور قرص‌شکل با درخت قابل کلیک (scroll-to-section)
// ⑤ پاپ‌آپ مرکزی بزرگ با blur به جای popover کوچک
// ⑥ اگر فرزند محتوا نداشت → فلش و دراپ‌داون نیاد
// ⑦ حفظ تمام امکانات: watermark, security, premium, save, share, copy slug, question
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

    // مدال نمایش فیلد (متن بلند)
    fieldModal: { open: false, title: "", subtitle: "", content: "", isHtml: false },

    // تب فعال در بخش رسانه: 'images' | 'videos'
    mediaTab: "images",

    watermarkText: "drcode-med.ir",

    // داده‌های API
    disposition: null,
    dynamicFields: null,
    media: null,
    sections: null,

    // پاپ‌آپ مرکزی (جایگزین popover)
    activePopup: null,
    popupData: { title: "", content: "" },
    popupTheme: { style: "", iconTextStyle: "" },

    // سایدبار شناور
    sidebarOpen: false,
    activeSidebarSection: null,
    activeAnchor: null,
    sidebarTree: {
      preclinical: [],
      orderFields: [],
      orderSections: [],
      disposition: null,
    },
    expandedSidebarSections: {
      preclinical: true,
      order: true,
      disposition: true,
    },
    _sidebarHoverTimer: null,
    _sidebarLeaveTimer: null,
    _scrollSpyHandler: null,

    showBackToTop: false,

    // ----- NEW state (sidebar search / copy / toast / current-section) -----
    sidebarFilter: "",
    copiedKey: null,
    toast: { visible: false, message: "" },
    _toastTimer: null,
    currentSectionLabel: "",

    // ----- NEW state (CRON-REVIEW-2: theme picker / collapsible sections / keyboard nav) -----
    mpProgress: 0,
    themeColor: null,  // null = use order.color (preserves existing behavior); set by setTheme()
    themeOptions: [
      { color: "#0ea5e9", name: "آبی آسمانی" },
      { color: "#10b981", name: "سبز زمردی" },
      { color: "#e11d48", name: "قرمز رز" },
      { color: "#8b5cf6", name: "بنفش" },
      { color: "#f59e0b", name: "کهربایی" },
    ],
    collapsedSections: { preclinical: false, orderinfo: false, sections: false, disposition: false, media: false },
    _kbFocusIndex: -1,
    _viewerInstance: null,
    // ----- NEW state (DJANGO-SYNC-3: dark mode / share / reading time / prev-next / history) -----
    isDarkMode: false,
    shareModalOpen: false,
    shareUrl: "",
    shareTitle: "",
    qrDataUrl: "",
    readingTimeMin: 0,
    sectionNavList: [],
    sectionNavIndex: -1,

    // ----- NEW state (DJANGO-SYNC-4: bookmarks / help / font size / tour / minimap) -----
    bookmarks: [],
    helpOpen: false,
    fontSizeIdx: 1, // 0=sm,1=md,2=lg,3=xl
    fontSizes: ["sm","md","lg","xl"],
    fontLabels: ["کوچک","متوسط","بزرگ","خیلی بزرگ"],
    tourActive: false,
    tourStep: 0,
    tourSteps: [
      { selector:".mp-theme-picker", title:"انتخابگر تم رنگ", desc:"با کلیک روی نقاط رنگی، تم اوردر را به سلیقه خود تغییر دهید. انتخاب شما ذخیره می‌شود." },
      { selector:".mp-dark-toggle", title:"حالت تاریک/روشن", desc:"با کلیک روی این دکمه بین حالت تاریک و روشن جابه‌جا شوید. مناسب مطالعه در شب." },
      { selector:".mp-rail", title:"فهرست اوردر", desc:"با هاور روی این نوار، فهرست کامل اوردر باز می‌شود. می‌توانید جستجو کنید یا بخش‌ها را باز/بسته کنید." },
      { selector:".mp-prevnext", title:"ناوبری بخش‌ها", desc:"با این دکمه‌ها یا کلیدهای PageUp/PageDown بین بخش‌های اوردر جابه‌جا شوید." },
      { selector:".mp-minimap", title:"نقشهٔ کوچک", desc:"این نقاط نشان‌دهنده‌ی بخش‌های اوردر هستند. بخش فعلی هایلایت شده است." },
      { selector:"#anchor-order-info", title:"اطلاعات پایه", desc:"مقادیر فیلدها را می‌توانید با دکمه کپی کپی کنید. برای مقادیر طولانی، دکمه نمایش کامل موجود است." },
      { selector:".mp-star-btn", title:"نشان‌گذاری", desc:"با کلیک روی ستاره، بخش‌های مهم را نشان‌گذاری کنید. نشان‌ها در سایدبار نمایش داده می‌شوند." },
      { selector:".mp-help-overlay", title:"میانبرهای کیبورد", desc:"هر زمان با فشردن کلید ? این راهنما را ببینید. میانبرهای زیادی برای استفاده سریع موجود است." },
    ],
    tourSpotlightStyle: "",
    tourCardStyle: "",
    minimapSegments: [],
    // NEW (DJANGO-SYNC-5): content stats
    statsOpen: false,
    contentStats: { totalWords: 0, totalSections: 0, sectionStats: [] },
    // NEW (DJANGO-SYNC-5): focus mode
    focusMode: false,

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
      this._setupScrollbarVar();

      // بارگذاری موازی برای پرفورمنس بهتر
      await Promise.all([
        this.loadDisposition(slug),
        this.loadDynamicFields(slug),
        this.loadSections(slug),
        this.loadMedia(slug),
      ]);

      // DJANGO-SYNC-3: load persisted theme + dark mode, compute reading time, build section nav, load history
      this.loadTheme();
      this.loadDarkMode();
      // DJANGO-SYNC-4: load font size, bookmarks, build mini-map, check onboarding
      this.loadFontSize();
      this.loadBookmarks();
      this.computeReadingTime();
      this.$nextTick(() => { this.buildMinimap(); });

      // ساخت درخت سایدبار بعد از لود داده‌ها
      this.$nextTick(() => {
        this.buildSidebarTree();
        this.autoExpandDisposition();
        this.initMediaTab();
        this.initScrollSpy();
        // CRON-REVIEW-2: URL hash deep-linking (e.g. /ordering/<slug>#df-node-123)
        this.initHashHandler();
        // CRON-REVIEW-2: Viewer.js initialization is handled by the inline script at the
        // bottom of the page, which exposes window.myOrderMediaGalleryInstance.
        // openLightbox() reads from there, so no initViewer() call is needed here.
      });
    },

    getSlugFromURL() {
      const path = window.location.pathname;
      const segments = path.split("/").filter(Boolean);
      return segments.length ? segments[segments.length - 1] : null;
    },

    // محاسبه عرض اسکرول‌بار برای جلوگیری از jump وقتی modal باز می‌شه
    _setupScrollbarVar() {
      const setVar = () => {
        const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
        document.documentElement.style.setProperty("--sbw", Math.max(0, scrollbarWidth) + "px");
      };
      setVar();
      let resizeTimer;
      window.addEventListener("resize", () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(setVar, 200);
      }, { passive: true });
    },

    hasRealContent(value) {
      if (!value || typeof value !== "string") return false;
      if (value.trim() === "") return false;

      const textOnly = value
        .replace(/<[^>]*>/g, " ")
        .replace(/&nbsp;|&#160;|\s+/g, " ") 
        .trim();

      return textOnly.length > 0;
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

    // ─────────────────────────────────────────────────────────────────────────
    // سایدبار شناور — مدیریت باز/بسته شدن
    // ─────────────────────────────────────────────────────────────────────────

    onSidebarEnter() {
      // وقتی موس میره روی سایدبار
      clearTimeout(this._sidebarLeaveTimer);
      if (!this.sidebarOpen) {
        // باز کردن با تاخیر کوتاه برای جلوگیری از باز شدن ناخواسته
        this._sidebarHoverTimer = setTimeout(() => {
          this.sidebarOpen = true;
        }, 200);
      }
    },

    onSidebarLeave() {
      // وقتی موس از سایدبار خارج میشه
      clearTimeout(this._sidebarHoverTimer);
      this._sidebarLeaveTimer = setTimeout(() => {
        this.sidebarOpen = false;
      }, 300);
    },

    closeSidebar() {
      this.sidebarOpen = false;
    },

    // باز/بسته کردن یک سکشن در سایدبار
    toggleSidebarSection(section, forceOpen = false) {
      if (forceOpen) this.sidebarOpen = true;
      this.activeSidebarSection = this.activeSidebarSection === section && !forceOpen ? null : section;
      this.expandedSidebarSections[section] = true;
    },

    // ساخت درخت سایدبار از روی داده‌های لود شده
    buildSidebarTree() {
      // پیش‌بالینی
      this.sidebarTree.preclinical = (this.dynamicFields?.dynamic_field_groups || []).map(g => ({
        id: g.id,
        title: g.title,
        nodes: (g.nodes || []).map(n => ({
          id: n.id,
          title: n.title,
          children: (n.children || []).map(c => ({ id: c.id, title: c.title })),
        })),
      }));

      // فیلدهای پایه اوردر
      this.sidebarTree.orderFields = this.infoFields();

      // بخش‌های اوردر
      this.sidebarTree.orderSections = (this.sections?.sections || []).map(s => ({
        id: s.id,
        title: s.title,
        color: isValidHexColor(s.color) ? s.color : ORDER_DEFAULT_COLOR,
      }));

      // تعیین تکلیف
      if (this.disposition?.emergency_disposition) {
        const disp = this.disposition.emergency_disposition;
        this.sidebarTree.disposition = {
          id: disp.id,
          title: disp.title,
          color: isValidHexColor(disp.color) ? disp.color : ORDER_DEFAULT_COLOR,
          nodes: (disp.nodes || []).map(n => ({
            id: n.id,
            title: n.title,
            children: (n.children || []).map(c => ({ id: c.id, title: c.title })),
          })),
        };
      }

      // رسانه‌ها (media)
      const imgs = (this.media?.images || []).slice().sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0));
      const vids = (this.media?.videos || []).slice().sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0));
      this.sidebarTree.media = {
        imagesCount: imgs.length,
        videosCount: vids.length,
        totalCount: imgs.length + vids.length,
        images: imgs,
        videos: vids,
      };

      // انتخاب سکشن اول به‌صورت پیش‌فرض
      if (this.sidebarTree.preclinical.length > 0) {
        this.activeSidebarSection = "preclinical";
      } else if (this.sidebarTree.orderFields.length > 0 || this.sidebarTree.orderSections.length > 0) {
        this.activeSidebarSection = "order";
      } else if (this.sidebarTree.disposition) {
        this.activeSidebarSection = "disposition";
      } else if (this.sidebarTree.media && this.sidebarTree.media.totalCount > 0) {
        this.activeSidebarSection = "media";
      }
    },

    // باز کردن والد(های) یک anchor قبل از اسکرول — تا زیرمجموعه‌های پیش‌بالینی
    // و تعیین تکلیف اورژانسی که در حالت جمع‌شده (display:none) هستند، باز و قابل
    // دیدن شوند. این متد روی داده‌های واکنش‌گرای Alpine (dynamicFields / disposition)
    // عمل می‌کند و پرچم _open را روی والد و خود فرزند (در صورت داشتن محتوا) set می‌کند.
    expandToAnchor(anchorId) {
      if (!anchorId) return;

      // ── پیش‌بالینی: df-node / df-child ──
      if (anchorId.startsWith("df-node-")) {
        const nodeId = parseInt(anchorId.replace("df-node-", ""));
        for (const group of (this.dynamicFields?.dynamic_field_groups || [])) {
          for (const node of (group.nodes || [])) {
            if (node.id === nodeId) { node._open = true; return; }
          }
        }
        return;
      }
      if (anchorId.startsWith("df-child-")) {
        const childId = parseInt(anchorId.replace("df-child-", ""));
        for (const group of (this.dynamicFields?.dynamic_field_groups || [])) {
          for (const node of (group.nodes || [])) {
            const child = (node.children || []).find(c => c.id === childId);
            if (child) {
              node._open = true;                       // باز کردن گروه/گره والد
              if (this.hasChildContent(child)) child._open = true; // باز کردن خود زیرمجموعه
              return;
            }
          }
        }
        return;
      }

      // ── تعیین تکلیف اورژانسی: disp-node / disp-child ──
      if (anchorId.startsWith("disp-node-")) {
        const nodeId = parseInt(anchorId.replace("disp-node-", ""));
        for (const node of (this.disposition?.emergency_disposition?.nodes || []) ) {
          if (node.id === nodeId) { node._open = true; return; }
        }
        return;
      }
      if (anchorId.startsWith("disp-child-")) {
        const childId = parseInt(anchorId.replace("disp-child-", ""));
        for (const node of (this.disposition?.emergency_disposition?.nodes || []) ) {
          const child = (node.children || []).find(c => c.id === childId);
          if (child) {
            node._open = true;
            if (this.hasDispositionChildContent(child)) child._open = true;
            return;
          }
        }
        return;
      }
    },

    // اسکرول به یک anchor خاص — ابتدا والد(ها) را باز می‌کند، بعد از رندر
    // Alpine و پایان transition، به‌صورت نرم به عنصر اسکرول می‌کند.
    scrollToAnchor(anchorId) {
      this.expandToAnchor(anchorId);
      // CRON-REVIEW-2: update URL hash so the section is shareable / back-button friendly
      this.updateHash(anchorId);
      // DJANGO-SYNC-3: update prev/next nav index + record in viewed history

      const doScroll = () => {
        let el = document.getElementById(anchorId);
        if (!el) {
          // fallback: anchor های section-level
          const map = {
            "order-info": "anchor-order-info",
            "order-sections": "anchor-order-sections",
          };
          if (map[anchorId]) el = document.getElementById(map[anchorId]);
        }
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "start" });
          this.activeAnchor = anchorId;
        }
      };

      // $nextTick محتوای واکنش‌گرا را به‌روز می‌کند؛ setTimeout کوتاه به transition
      // های x-transition فرصت می‌دهد تا عنصر را ارتفاع دهد و scrollIntoView درست کار کند.
      if (this.$nextTick) {
        this.$nextTick(() => setTimeout(doScroll, 220));
      } else {
        setTimeout(doScroll, 240);
      }
    },

    // scroll spy — تشخیص سکشن فعال بر اساس اسکرول
    initScrollSpy() {
      if (this._scrollSpyHandler) {
        window.removeEventListener("scroll", this._scrollSpyHandler);
      }

      let ticking = false;
      this._scrollSpyHandler = () => {
        if (!ticking) {
          requestAnimationFrame(() => {
            this._updateActiveAnchor();
            ticking = false;
          });
          ticking = true;
        }
      };
      window.addEventListener("scroll", this._scrollSpyHandler, { passive: true });
      this._scrollSpyHandler();
    },

    _updateActiveAnchor() {
      const allAnchors = this._collectAllAnchors();
      if (allAnchors.length === 0) return;

      const scrollPos = window.scrollY + 150;
      let current = allAnchors[0];
      for (const a of allAnchors) {
        if (a.top <= scrollPos) {
          current = a;
        } else {
          break;
        }
      }
      if (current) {
        this.activeAnchor = current.id;
        // NEW: auto-follow - section فعلی را در سایدبار باز می‌گذارد و لیبل هدر را به‌روز می‌کند
        this._syncCurrentSection(current.id);
      }
    },

    _collectAllAnchors() {
      const ids = [];
      // preclinical
      (this.sidebarTree.preclinical || []).forEach(g => {
        ids.push("df-group-" + g.id);
        (g.nodes || []).forEach(n => {
          ids.push("df-node-" + n.id);
          (n.children || []).forEach(c => ids.push("df-child-" + c.id));
        });
      });
      // order fields
      (this.sidebarTree.orderFields || []).forEach(f => ids.push("field-" + f.key));
      ids.push("order-info");
      ids.push("order-sections");
      // sections
      (this.sidebarTree.orderSections || []).forEach(s => ids.push("section-" + s.id));
      // disposition
      if (this.sidebarTree.disposition) {
        (this.sidebarTree.disposition.nodes || []).forEach(n => {
          ids.push("disp-node-" + n.id);
          (n.children || []).forEach(c => ids.push("disp-child-" + c.id));
        });
      }
      // media
      if (this.sidebarTree.media && this.sidebarTree.media.totalCount > 0) {
        ids.push("anchor-media");
        ids.push("media-images");
        ids.push("media-videos");
      }

      const result = [];
      for (const id of ids) {
        const el = document.getElementById(id);
        if (el) {
          const rect = el.getBoundingClientRect();
          const top = rect.top + window.scrollY;
          result.push({ id, top });
        }
      }
      result.sort((a, b) => a.top - b.top);
      return result;
    },

    // ─────────────────────────────────────────────────────────────────────────
    // مدیریت پاپ‌آپ مرکزی (جایگزین popover)
    // ─────────────────────────────────────────────────────────────────────────

    openPopup(event, id) {
      if (event) {
        event.stopPropagation();
        event.preventDefault();
      }

      // اگر روی همان آیتم کلیک شد، بسته شود
      if (this.activePopup === id) {
        this.closePopup();
        return;
      }

      const data = this.findPopupContent(id);
      if (!data) return;

      this.popupData = data;
      this.popupTheme = data.theme || { style: "", iconTextStyle: "" };
      this.activePopup = id;
      document.body.classList.add("modal-open");
    },

    closePopup() {
      this.activePopup = null;
      this.popupData = { title: "", content: "" };
      document.body.classList.remove("modal-open");
    },

    // یافتن محتوای پاپ‌آپ بر اساس ID
    // ساختار API: sections[].relationship_groups[].text_items / drug_items
    // + sections[].ungrouped_items / ungrouped_drug_items
    findPopupContent(id) {
      // field-{key}
      if (id.startsWith("field-")) {
        const key = id.replace("field-", "");
        const field = this.infoFields().find(f => f.key === key);
        if (field) {
          return {
            title: "توضیحات: " + field.labelFa,
            content: field.notes || "",
            theme: {
              style: `--popup-c: ${this.theme().color};`,
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
              style: `--popup-c: ${color};`,
              iconTextStyle: `color: ${color};`,
            },
          };
        }
      }

      // item-{id} — جستجو در: relationship_groups[].text_items، ungrouped_items، items
      // (پشتیبانی از هر دو شکل API)
      if (id.startsWith("item-") && this.sections?.sections) {
        const itemId = parseInt(id.replace("item-", ""));
        for (const section of this.sections.sections) {
          // ۱. جستجو در relationship_groups[].text_items
          if (section.relationship_groups) {
            for (const rg of section.relationship_groups) {
              if (!rg.text_items) continue;
              const item = rg.text_items.find(i => i.id === itemId);
              if (item) {
                const color = isValidHexColor(section.color) ? section.color : ORDER_DEFAULT_COLOR;
                return {
                  title: "توضیحات آیتم" + (item.item_number ? " #" + item.item_number : ""),
                  content: item.notes || "",
                  theme: {
                    style: `--popup-c: ${color};`,
                    iconTextStyle: `color: ${color};`,
                  },
                };
              }
            }
          }
          // ۲. جستجو در ungrouped_items (شکل Swagger)
          if (section.ungrouped_items) {
            const item = section.ungrouped_items.find(i => i.id === itemId);
            if (item) {
              const color = isValidHexColor(section.color) ? section.color : ORDER_DEFAULT_COLOR;
              return {
                title: "توضیحات آیتم" + (item.item_number ? " #" + item.item_number : ""),
                content: item.notes || "",
                theme: {
                  style: `--popup-c: ${color};`,
                  iconTextStyle: `color: ${color};`,
                },
              };
            }
          }
          // ۳. جستجو در items (شکل API واقعی تولید)
          if (section.items) {
            const item = section.items.find(i => i.id === itemId);
            if (item) {
              const color = isValidHexColor(section.color) ? section.color : ORDER_DEFAULT_COLOR;
              return {
                title: "توضیحات آیتم" + (item.item_number ? " #" + item.item_number : ""),
                content: item.notes || "",
                theme: {
                  style: `--popup-c: ${color};`,
                  iconTextStyle: `color: ${color};`,
                },
              };
            }
          }
        }
      }

      // drug-{id} — جستجو در: relationship_groups[].drug_items، ungrouped_drug_items، drug_items
      // (پشتیبانی از هر دو شکل API)
      if (id.startsWith("drug-") && this.sections?.sections) {
        const drugId = parseInt(id.replace("drug-", ""));
        for (const section of this.sections.sections) {
          // ۱. جستجو در relationship_groups[].drug_items
          if (section.relationship_groups) {
            for (const rg of section.relationship_groups) {
              if (!rg.drug_items) continue;
              const drug = rg.drug_items.find(d => d.id === drugId);
              if (drug) {
                const color = isValidHexColor(section.color) ? section.color : ORDER_DEFAULT_COLOR;
                return {
                  title: "توضیحات دارو: " + (drug.drug?.title || ""),
                  content: drug.notes || "",
                  theme: {
                    style: `--popup-c: ${color};`,
                    iconTextStyle: `color: ${color};`,
                  },
                };
              }
            }
          }
          // ۲. جستجو در ungrouped_drug_items (شکل Swagger)
          if (section.ungrouped_drug_items) {
            const drug = section.ungrouped_drug_items.find(d => d.id === drugId);
            if (drug) {
              const color = isValidHexColor(section.color) ? section.color : ORDER_DEFAULT_COLOR;
              return {
                title: "توضیحات دارو: " + (drug.drug?.title || ""),
                content: drug.notes || "",
                theme: {
                  style: `--popup-c: ${color};`,
                  iconTextStyle: `color: ${color};`,
                },
              };
            }
          }
          // ۳. جستجو در drug_items (شکل API واقعی تولید — در سطح سکشن)
          if (section.drug_items) {
            const drug = section.drug_items.find(d => d.id === drugId);
            if (drug) {
              const color = isValidHexColor(section.color) ? section.color : ORDER_DEFAULT_COLOR;
              return {
                title: "توضیحات دارو: " + (drug.drug?.title || ""),
                content: drug.notes || "",
                theme: {
                  style: `--popup-c: ${color};`,
                  iconTextStyle: `color: ${color};`,
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
            style: `--popup-c: ${color};`,
            iconTextStyle: `color: ${color};`,
          },
        };
      }

      // dfgroup-{id} — توضیحات گروه در dynamic fields
      if (id.startsWith("dfgroup-") && this.dynamicFields?.dynamic_field_groups) {
        const groupId = parseInt(id.replace("dfgroup-", ""));
        const group = this.dynamicFields.dynamic_field_groups.find(g => g.id === groupId);
        if (group) {
          const color = isValidHexColor(group.color) ? group.color : ORDER_DEFAULT_COLOR;
          return {
            title: "توضیحات گروه: " + (group.title || ""),
            content: group.notes || "",
            theme: {
              style: `--popup-c: ${color};`,
              iconTextStyle: `color: ${color};`,
            },
          };
        }
      }

      // image-{idx} — توضیحات کپشن تصویر
      if (id.startsWith("image-") && this.media?.images) {
        const idx = parseInt(id.replace("image-", ""));
        const img = this.media.images[idx];
        if (img) {
          const c = this.theme().color;
          return {
            title: "توضیحات تصویر #" + (idx + 1),
            content: img.caption || "<p class='text-gray-500 text-sm'>کپشنی ثبت نشده است.</p>",
            theme: {
              style: `--popup-c: ${c};`,
              iconTextStyle: `color: ${c};`,
            },
          };
        }
      }

      // video-{idx} — توضیحات ویدیو
      if (id.startsWith("video-") && this.media?.videos) {
        const idx = parseInt(id.replace("video-", ""));
        const vid = this.media.videos[idx];
        if (vid) {
          const c = this.theme().color;
          const html = `
            <div class="space-y-2">
              <p class="font-bold text-base">${vid.title || "ویدیو پیوست شده"}</p>
              ${vid.description ? `<div class="text-sm text-gray-700 leading-relaxed">${vid.description}</div>` : ""}
              <a href="${vid.video_url || "#"}" target="_blank" rel="noopener noreferrer"
                 class="inline-flex items-center gap-2 text-sm font-bold px-3 py-2 rounded-lg text-white"
                 style="background: ${c};">
                <i class="fas fa-external-link-alt"></i>
                <span>مشاهده در منبع</span>
              </a>
            </div>
          `;
          return {
            title: "جزئیات ویدیو #" + (idx + 1),
            content: html,
            theme: {
              style: `--popup-c: ${c};`,
              iconTextStyle: `color: ${c};`,
            },
          };
        }
      }

      return null;
    },

    // ─────────────────────────────────────────────────────────────────────────
    // قانون: اگر فرزند محتوا نداشت → فلش و دراپ‌داون نیاد
    // ─────────────────────────────────────────────────────────────────────────

    // برای nodes در dynamic-fields: محتوا دارد اگر content یا children داشته باشد
    hasNodeContent(node) {
      if (!node) return false;
      const hasContent = node.content && String(node.content).trim() !== "";
      const hasChildren = node.children && node.children.length > 0;
      return hasContent || hasChildren;
    },

    // برای children در dynamic-fields: محتوا دارد اگر content داشته باشد
    hasChildContent(child) {
      if (!child) return false;
      return child.content && String(child.content).trim() !== "";
    },

    // برای nodes در disposition: محتوا دارد اگر children داشته باشد
    hasDispositionContent(node) {
      if (!node) return false;
      return node.children && node.children.length > 0;
    },

    // برای children در disposition: محتوا دارد اگر content داشته باشد
    hasDispositionChildContent(child) {
      if (!child) return false;
      return child.content && String(child.content).trim() !== "";
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
          labelEn: "Activity",
          labelFa: "فعالیت",
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
      // CRON-REVIEW-2: if user picked a theme via the picker, use it; otherwise fall back to order.color.
      const raw = this.themeColor || this.order?.color;
      const c = isValidHexColor(raw) ? raw.trim() : ORDER_DEFAULT_COLOR;
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
    // groupItemsByCondition (LEGACY — نگه داشته شد برای backward compat)
    // ورودی: آرایه‌ای از text_items یا drug_items
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

    // ─────────────────────────────────────────────────────────────────────────
    // flattenSectionRows — رندر مسطح آیتم‌های یک سکشن بر اساس order_index واقعی
    //
    // ⚠️ این متد هر دو شکل API را پشتیبانی می‌کند:
    //
    //   شکل ۱ (API واقعی تولید — در ۱۰ نمونه‌ی واقعی سایت):
    //     section.items         → آرایه آیتم‌های متنی (در سطح سکشن)
    //     section.drug_items    → آرایه آیتم‌های دارویی (در سطح سکشن)
    //     section.all_conditions
    //     (بدون ungrouped_* یا relationship_groups)
    //     (آیتم‌ها معمولاً item_number ندارند → خودمان شماره می‌دهیم)
    //
    //   شکل ۲ (مستندات Swagger — نمونه‌ی قدیمی/تمیز):
    //     section.ungrouped_items
    //     section.ungrouped_drug_items
    //     section.relationship_groups (با text_items + drug_items داخل گروه)
    //
    // منطق:
    //   ۱. text items: ترجیح ungrouped_items (اگر غیرخالی)، وگرنه items
    //   ۲. drug items: ترجیح ungrouped_drug_items (اگر غیرخالی)، وگرنه drug_items
    //   ۳. relationship_groups: اگر موجود باشد، پشتیبانی می‌شود
    //   ۴. هر سه دسته با هم بر اساس order_index مرتب می‌شوند
    //   ۵. داخل هر گروه: ابتدا text_items سپس drug_items (هر کدام بر اساس order_index)
    //   ۶. بین آیتم‌های متوالیِ داخل یک گروه، اپراتور درج می‌شود (AND/OR/THEN)
    //   ۷. is_drug_section فقط یک badge در هدر است؛ هر سکشن می‌تواند هم text و هم drug داشته باشد
    //   ۸. اگر آیتم item_number نداشت، شمارهٔ متوالی محاسبه می‌شود
    //
    // خروجی: آرایه‌ای از ردیف‌ها با یکی از این شکل‌ها:
    //   { kind: 'text',     item, inGroup, groupId? }
    //   { kind: 'drug',     item, inGroup, groupId? }
    //   { kind: 'operator', operator, groupId }
    // ─────────────────────────────────────────────────────────────────────────
    flattenSectionRows(section) {
      if (!section) return [];

      // ── نرمالایز: پشتیبانی از هر دو شکل API ──
      const textItemsSource =
        (section.ungrouped_items && section.ungrouped_items.length > 0)
          ? section.ungrouped_items
          : (section.items || []);
      const drugItemsSource =
        (section.ungrouped_drug_items && section.ungrouped_drug_items.length > 0)
          ? section.ungrouped_drug_items
          : (section.drug_items || []);
      const groupsSource = section.relationship_groups || [];

      // ساخت entry های قابل مرتب‌سازی
      const entries = [];

      textItemsSource.forEach((item) => {
        if (!item) return;
        entries.push({ _type: "text", item, _oi: item.order_index ?? 0 });
      });
      drugItemsSource.forEach((item) => {
        if (!item) return;
        entries.push({ _type: "drug", item, _oi: item.order_index ?? 0 });
      });
      groupsSource.forEach((group) => {
        if (!group) return;
        entries.push({ _type: "group", group, _oi: group.order_index ?? 0 });
      });

      // stable sort by order_index (ترتیب واقعی نمایش)
      entries.sort((a, b) => (a._oi ?? 0) - (b._oi ?? 0));

      // ساخت ردیف‌های نهایی + شماره‌گذاری خودکار در صورت نبود item_number
      const rows = [];
      let autoCounter = 0;

      const withNumber = (item) => {
        autoCounter++;
        if (item.item_number === undefined || item.item_number === null) {
          // کپی سطحی با item_number محاسبه‌شده
          return { ...item, item_number: autoCounter };
        }
        return item;
      };

      entries.forEach((entry) => {
        if (entry._type === "text") {
          rows.push({
            kind: "text",
            item: withNumber(entry.item),
            inGroup: false,
          });
        } else if (entry._type === "drug") {
          rows.push({
            kind: "drug",
            item: withNumber(entry.item),
            inGroup: false,
          });
        } else if (entry._type === "group") {
          const g = entry.group;
          const textInGroup = (g.text_items || [])
            .slice()
            .sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0));
          const drugInGroup = (g.drug_items || [])
            .slice()
            .sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0));
          const combined = [
            ...textInGroup.map((i) => ({ kind: "text", item: i, inGroup: true, groupId: g.id })),
            ...drugInGroup.map((i) => ({ kind: "drug", item: i, inGroup: true, groupId: g.id })),
          ];

          combined.forEach((row, idx) => {
            if (idx > 0) {
              rows.push({
                kind: "operator",
                operator: (g.operator || "AND").toUpperCase(),
                groupId: g.id,
              });
            }
            rows.push({
              kind: row.kind,
              item: withNumber(row.item),
              inGroup: true,
              groupId: g.id,
            });
          });
        }
      });

      return rows;
    },

    // کلاس CSS برای badge اپراتور
    operatorBadgeClass(op) {
      const o = (op || "AND").toUpperCase();
      if (o === "OR") return "op-or";
      if (o === "THEN") return "op-then";
      return "op-and";
    },

    // لیبل فارسی اپراتور
    operatorLabel(op) {
      const o = (op || "AND").toUpperCase();
      if (o === "OR") return "یا (OR)";
      if (o === "THEN") return "سپس (THEN)";
      if (o === "AND") return "و (AND)";
      return o;
    },

    // ─────────────────────────────────────────────────────────────────────────
    // رسانه‌ها (Media API)
    // ─────────────────────────────────────────────────────────────────────────

    // تصاویر مرتب‌شده بر اساس order_index
    sortedImages() {
      if (!this.media?.images) return [];
      return this.media.images
        .slice()
        .sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0));
    },

    // ویدیوهای مرتب‌شده بر اساس order_index
    sortedVideos() {
      if (!this.media?.videos) return [];
      return this.media.videos
        .slice()
        .sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0));
    },

    hasMedia() {
      return (
        !!this.media &&
        (((this.media.images || []).length > 0) || ((this.media.videos || []).length > 0))
      );
    },

    // تنظیم تب پیش‌فرض وقتی media بارگذاری شد
    initMediaTab() {
      if (this.sortedImages().length > 0) {
        this.mediaTab = "images";
      } else if (this.sortedVideos().length > 0) {
        this.mediaTab = "videos";
      }
    },

    // تشخیص اینکه آیا URL مربوط به آپارات است یا یوتیوب یا هرچیز دیگر
    detectVideoProvider(url) {
      if (!url) return "unknown";
      const u = String(url).toLowerCase();
      if (u.includes("aparat.com") || u.includes("/aparat/")) return "aparat";
      if (u.includes("youtube.com") || u.includes("youtu.be")) return "youtube";
      if (u.includes("vimeo.com")) return "vimeo";
      return "link";
    },

    // ساخت embed URL برای آپارات/یوتیوب در صورت نیاز (fallback: استفاده از URL مستقیم)
    buildEmbedUrl(url) {
      const provider = this.detectVideoProvider(url);
      if (provider === "youtube") {
        // استخراج video id از URL یوتیوب
        const m = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([A-Za-z0-9_-]{11})/);
        if (m) return `https://www.youtube.com/embed/${m[1]}`;
        return url;
      }
      if (provider === "aparat") {
        // آپارات هم embed path داره
        const m = url.match(/aparat\.com\/video\/[^/]+\/([A-Za-z0-9]+)/);
        if (m) return `https://www.aparat.com/video/video/embed/videohash/${m[1]}/vt/frame`;
        return url;
      }
      return url;
    },

    // شناسه‌سازی ویدیو (برای نمایش آیکون یا badge)
    videoProviderLabel(url) {
      const p = this.detectVideoProvider(url);
      const map = {
        aparat: "آپارات",
        youtube: "یوتیوب",
        vimeo: "Vimeo",
        link: "لینک خارجی",
        unknown: "نامشخص",
      };
      return map[p] || "لینک خارجی";
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
      document.body.classList.add("modal-open");
    },

    showNotesModal() {
      // order.notes توسط ادمین با CKEditor نوشته می‌شود → باید به‌صورت HTML رندر شود
      this.fieldModal = {
        open: true,
        title: "یادداشت تکمیلی اوردر",
        subtitle: "",
        content: this.order?.notes || "",
        isHtml: true,
      };
      document.body.classList.add("modal-open");
    },

    closeFieldModal() {
      this.fieldModal.open = false;
      this.fieldModal.isHtml = false;
      document.body.classList.remove("modal-open");
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (CRON-REVIEW-2): Theme picker override + helpers
    // ─────────────────────────────────────────────────────────────────────────
    themeStyle() { return `--theme-c: ${this.theme().color};`; },
    setTheme(color) {
        this.themeColor = color;
        try { localStorage.setItem("drcode_order_theme", color); } catch (e) {}
        this.showToast("تم تغییر کرد");
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-3): Load persisted theme from localStorage
    // ─────────────────────────────────────────────────────────────────────────
    loadTheme() {
        try {
            const t = localStorage.getItem("drcode_order_theme");
            if (t) this.themeColor = t;
        } catch (e) {}
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-3): Dark mode toggle — persisted via localStorage
    // ─────────────────────────────────────────────────────────────────────────
    toggleDarkMode() {
        this.isDarkMode = !this.isDarkMode;
        document.documentElement.setAttribute("data-theme", this.isDarkMode ? "dark" : "light");
        try { localStorage.setItem("drcode_order_dark", this.isDarkMode ? "1" : "0"); } catch (e) {}
        this.showToast(this.isDarkMode ? "حالت تاریک فعال شد 🌙" : "حالت روشن فعال شد ☀️");
    },
    loadDarkMode() {
        try {
            const v = localStorage.getItem("drcode_order_dark");
            this.isDarkMode = v === "1";
            if (this.isDarkMode) document.documentElement.setAttribute("data-theme", "dark");
        } catch (e) {}
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-3): Share modal — generates share URL + QR code
    // ─────────────────────────────────────────────────────────────────────────
    openShareModal() {
        this.shareUrl = window.location.origin + window.location.pathname + (window.location.hash || "");
        this.shareTitle = this.order?.name || "اوردر پزشکی";
        this.shareModalOpen = true;
        document.body.classList.add("modal-open");
        // Generate QR code (using api.qrserver.com — no key needed)
        this.qrDataUrl = "https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=" + encodeURIComponent(this.shareUrl);
    },
    closeShareModal() {
        this.shareModalOpen = false;
        document.body.classList.remove("modal-open");
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-3): Reading time estimate (~200 wpm)
    // ─────────────────────────────────────────────────────────────────────────
    computeReadingTime() {
        this.$nextTick(() => {
            const sec = document.getElementById("order__section");
            if (!sec) return;
            const text = sec.innerText || "";
            const words = text.trim().split(/\s+/).filter(Boolean).length;
            this.readingTimeMin = Math.max(1, Math.ceil(words / 200));
        });
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (CRON-REVIEW-2): Collapsible main sections
    // ─────────────────────────────────────────────────────────────────────────
    toggleSectionCollapse(key) { this.collapsedSections[key] = !this.collapsedSections[key]; },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (CRON-REVIEW-2): Copy deep link to a section
    // ─────────────────────────────────────────────────────────────────────────
    copySectionLink(anchorId) {
      const url = window.location.origin + window.location.pathname + "#" + anchorId;
      this.copyText(url, "link-" + anchorId);
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (CRON-REVIEW-2): URL hash deep-linking
    // ─────────────────────────────────────────────────────────────────────────
    initHashHandler() {
      const hash = window.location.hash.replace("#", "");
      if (hash) { setTimeout(() => { this.scrollToAnchor(hash); }, 600); }
      window.addEventListener("hashchange", () => {
        const h = window.location.hash.replace("#", "");
        if (h) this.scrollToAnchor(h);
      });
    },
    updateHash(anchorId) {
      if (window.location.hash !== "#" + anchorId) {
        history.replaceState(null, "", "#" + anchorId);
      }
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (CRON-REVIEW-2): Image lightbox — uses the Viewer.js instance created
    // by the inline script at the bottom of the page (window.myOrderMediaGalleryInstance).
    // ─────────────────────────────────────────────────────────────────────────
    openLightbox(idx) {
      const v = this._viewerInstance || window.myOrderMediaGalleryInstance;
      if (v) { try { v.view(idx); } catch (e) {} }
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (CRON-REVIEW-2): Keyboard arrow navigation in the sidebar tree
    // ─────────────────────────────────────────────────────────────────────────
    _kbCollectNodes() { return [...document.querySelectorAll(".mp-rail-drawer-body .fp-tree-node")]; },
    _kbApplyFocus() {
      const nodes = this._kbCollectNodes();
      nodes.forEach((n, i) => { n.classList.toggle("is-kb-focus", i === this._kbFocusIndex); });
      const target = nodes[this._kbFocusIndex];
      if (target) target.scrollIntoView({ block: "nearest", behavior: "smooth" });
    },
    _kbActivate() {
      const nodes = this._kbCollectNodes();
      const target = nodes[this._kbFocusIndex];
      if (target) target.click();
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW: نگاشت anchor → section + لیبل فارسی برای pill هدر + auto-follow
    // ─────────────────────────────────────────────────────────────────────────
    _syncCurrentSection(anchorId) {
      // نگاشت prefix → {section key, label}
      let sectionKey = null, label = null;
      if (anchorId.startsWith("df-")) { sectionKey = "preclinical"; label = "پیش‌بالینی"; }
      else if (anchorId.startsWith("field-") || anchorId === "order-info") { sectionKey = "order"; label = "اطلاعات پایه"; }
      else if (anchorId.startsWith("section-") || anchorId === "order-sections") {
        sectionKey = "order";
        // پیدا کردن عنوان section برای لیبل دقیق‌تر
        if (anchorId.startsWith("section-")) {
          const sid = parseInt(anchorId.replace("section-", ""));
          const s = (this.sidebarTree.orderSections || []).find(x => x.id === sid);
          label = s ? s.title : "بخش‌ها و دستورات";
        } else { label = "بخش‌ها و دستورات"; }
      }
      else if (anchorId.startsWith("disp-")) { sectionKey = "disposition"; label = this.sidebarTree.disposition?.title || "تعیین تکلیف"; }
      else if (anchorId.startsWith("media-") || anchorId === "anchor-media") { sectionKey = "media"; label = "رسانه‌ها"; }
      else if (anchorId === "order-question-section") { sectionKey = null; label = "پرسش سوال"; }

      this.currentSectionLabel = label || "";
      // DJANGO-SYNC-3: keep prev/next nav in sync with current section

      // auto-follow: اگر سایدبار بسته است، section فعال را عوض می‌کنیم تا دکمه‌ی rail
      // درست هایلایت شود. اگر سایدبار باز است و کاربر در حال مرور دستی است، مزاحم نمی‌شویم.
      if (sectionKey && !this.sidebarOpen && this.activeSidebarSection !== sectionKey) {
        this.activeSidebarSection = sectionKey;
        this.expandedSidebarSections[sectionKey] = true;
      }

      // DJANGO-SYNC-5: re-apply focus-mode highlight if active (active section changed)
      if (this.focusMode) { this._applyFocusHighlight(); }
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW: Bulk expand / collapse for the currently-active section
    // ─────────────────────────────────────────────────────────────────────────
    expandAllCurrent() {
      const sec = this.activeSidebarSection;
      if (sec === "preclinical") {
        (this.dynamicFields?.dynamic_field_groups || []).forEach(g => {
          (g.nodes || []).forEach(n => {
            n._open = true;
            (n.children || []).forEach(c => { if (this.hasChildContent(c)) c._open = true; });
          });
        });
      } else if (sec === "disposition") {
        (this.disposition?.emergency_disposition?.nodes || []).forEach(n => {
          n._open = true;
          (n.children || []).forEach(c => { if (this.hasDispositionChildContent(c)) c._open = true; });
        });
      }
      // برای order و media چیززی برای expand نیست (flat lists)
      this.showToast("همه‌ی زیرمجموعه‌ها باز شدند");
    },
    collapseAllCurrent() {
      const sec = this.activeSidebarSection;
      if (sec === "preclinical") {
        (this.dynamicFields?.dynamic_field_groups || []).forEach(g => {
          (g.nodes || []).forEach(n => {
            n._open = false;
            (n.children || []).forEach(c => c._open = false);
          });
        });
      } else if (sec === "disposition") {
        (this.disposition?.emergency_disposition?.nodes || []).forEach(n => {
          n._open = false;
          (n.children || []).forEach(c => c._open = false);
        });
      }
      this.showToast("همه‌ی زیرمجموعه‌ها جمع شدند");
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW: Sidebar search - flat filtered hits across all sections
    // ─────────────────────────────────────────────────────────────────────────
    get filteredHits() {
      const q = (this.sidebarFilter || "").trim().toLowerCase();
      if (!q) return [];
      const hits = [];
      const push = (anchor, title, section, icon, color = "#0ea5e9") => {
        if ((title || "").toLowerCase().includes(q)) hits.push({ anchor, title: title || "(بدون عنوان)", section, icon, color });
      };
      (this.sidebarTree.preclinical || []).forEach(g => {
        push("df-group-" + g.id, g.title, "پیش‌بالینی", "fa-folder-open");
        (g.nodes || []).forEach(n => {
          push("df-node-" + n.id, n.title, "پیش‌بالینی", "fa-circle-nodes");
          (n.children || []).forEach(c => push("df-child-" + c.id, c.title, "پیش‌بالینی", "fa-circle-dot"));
        });
      });
      (this.sidebarTree.orderFields || []).forEach(f => push("field-" + f.key, f.labelFa, "اطلاعات پایه", "fa-clipboard-list"));
      (this.sidebarTree.orderSections || []).forEach(s => push("section-" + s.id, s.title, "بخش‌ها", "fa-list-check"));
      if (this.sidebarTree.disposition) {
        const d = this.sidebarTree.disposition;
        const dColor = isValidHexColor(d.color) ? d.color : "#e11d48";
        (d.nodes || []).forEach(n => {
          push("disp-node-" + n.id, n.title, d.title || "تعیین تکلیف", "fa-sitemap", dColor);
          (n.children || []).forEach(c => push("disp-child-" + c.id, c.title, d.title || "تعیین تکلیف", "fa-circle-dot", dColor));
        });
      }
      return hits;
    },
    get filteredTreeEmpty() { return this.filteredHits.length === 0; },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW: Copy-to-clipboard + toast
    // ─────────────────────────────────────────────────────────────────────────
    copyText(text, key) {
      if (!text) return;
      const done = () => {
        this.copiedKey = key;
        this.showToast("کپی شد");
        clearTimeout(this._toastTimer);
        this._toastTimer = setTimeout(() => { this.copiedKey = null; }, 2000);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(String(text)).then(done).catch(() => this._legacyCopy(text, done));
      } else { this._legacyCopy(text, done); }
    },
    _legacyCopy(text, cb) {
      try {
        const ta = document.createElement("textarea");
        ta.value = String(text);
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        cb();
      } catch (e) { this.showToast("کپی ناموفق بود"); }
    },
    showToast(message) {
      this.toast = { visible: true, message };
      clearTimeout(this._toastTimer);
      this._toastTimer = setTimeout(() => { this.toast = { visible: false, message: "" }; }, 1800);
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

        if (e.key === "Escape") {
          // DJANGO-SYNC-3: share modal closes first
          if (this.shareModalOpen) {
            this.closeShareModal();
          } else if (this.statsOpen) {
            this.closeStats();
          } else if (this.activePopup) {
            this.closePopup();
          } else if (this.fieldModal.open) {
            this.closeFieldModal();
          } else if (this.helpOpen) {
            this.closeHelp();
          } else if (this.focusMode) {
            this.toggleFocusMode();
          } else if (this.sidebarOpen) {
            this.closeSidebar();
          }
        }
        // DJANGO-SYNC-5: "F" toggles focus mode (when not typing & no popup open)
        if (e.key.toLowerCase() === "f" && !["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName) && !this.activePopup && !this.fieldModal.open && !this.shareModalOpen && !this.statsOpen && !this.helpOpen) {
          e.preventDefault();
          this.toggleFocusMode();
        }
        // DJANGO-SYNC-5: "S" opens content stats
        if (e.key.toLowerCase() === "s" && !["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName) && !this.activePopup && !this.fieldModal.open && !this.shareModalOpen && !this.statsOpen && !this.helpOpen && !this.sidebarFilter) {
          e.preventDefault();
          this.openStats();
        }

        // NEW: "/" focuses the sidebar search (when sidebar open & not typing in an input)
        if (e.key === "/" && this.sidebarOpen && !["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName)) {
          e.preventDefault();
          const inp = document.querySelector(".mp-search-input");
          if (inp) inp.focus();
        }

        // CRON-REVIEW-2: Arrow keys navigate sidebar tree (only when sidebar open,
        // not typing in an input, and not actively searching — search has its own keyboard model)
        if (this.sidebarOpen && !["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName) && !this.sidebarFilter) {
          if (e.key === "ArrowDown" || e.key === "ArrowUp") {
            e.preventDefault();
            const nodes = this._kbCollectNodes();
            if (nodes.length === 0) return;
            if (e.key === "ArrowDown") this._kbFocusIndex = Math.min(nodes.length - 1, this._kbFocusIndex + 1);
            else this._kbFocusIndex = Math.max(-1, this._kbFocusIndex - 1);
            this._kbApplyFocus();
          }
          if (e.key === "Enter" && this._kbFocusIndex >= 0) {
            e.preventDefault();
            this._kbActivate();
          }
        }

        // DJANGO-SYNC-4: "?" opens help overlay (when not typing & no popup open)
        if (e.key === "?" && !["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName) && !this.activePopup && !this.fieldModal.open && !this.shareModalOpen) {
          e.preventDefault();
          if (this.helpOpen) { this.closeHelp(); } else { this.openHelp(); }
        }
        // DJANGO-SYNC-4: Ctrl+D toggles dark mode
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "d" && !["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName)) {
          e.preventDefault();
          this.toggleDarkMode();
        }
        // DJANGO-SYNC-4: Ctrl++ (or Ctrl+=) increases font size
        if ((e.ctrlKey || e.metaKey) && (e.key === "+" || e.key === "=") && !["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName)) {
          e.preventDefault();
          this.increaseFont();
        }
        // DJANGO-SYNC-4: Ctrl+- decreases font size
        if ((e.ctrlKey || e.metaKey) && e.key === "-" && !["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName)) {
          e.preventDefault();
          this.decreaseFont();
        }
      });
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-4): Keyboard shortcuts help overlay (?)
    // ─────────────────────────────────────────────────────────────────────────
    openHelp() { this.helpOpen = true; document.body.classList.add("modal-open"); },
    closeHelp() { this.helpOpen = false; document.body.classList.remove("modal-open"); },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-4): Font size control (A-/A+ accessibility)
    // ─────────────────────────────────────────────────────────────────────────
    get fontSizeLabel() { return this.fontLabels[this.fontSizeIdx] || "متوسط"; },
    increaseFont() { if (this.fontSizeIdx < 3) { this.fontSizeIdx++; this.applyFontSize(); } },
    decreaseFont() { if (this.fontSizeIdx > 0) { this.fontSizeIdx--; this.applyFontSize(); } },
    applyFontSize() { document.documentElement.setAttribute("data-font-size", this.fontSizes[this.fontSizeIdx]); try { localStorage.setItem("drcode_order_fontsize", String(this.fontSizeIdx)); } catch (e) {} },
    loadFontSize() { try { const v = localStorage.getItem("drcode_order_fontsize"); if (v !== null) { this.fontSizeIdx = parseInt(v) || 1; } } catch (e) {} this.applyFontSize(); },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-4): Bookmarks / favorites
    // ─────────────────────────────────────────────────────────────────────────
    isBookmarked(anchorId) { return this.bookmarks.some(b => b.anchor === anchorId); },
    toggleBookmark(anchorId, label) {
      const idx = this.bookmarks.findIndex(b => b.anchor === anchorId);
      if (idx >= 0) { this.bookmarks.splice(idx, 1); this.showToast("نشان حذف شد"); }
      else { this.bookmarks.push({ anchor: anchorId, label: label }); this.showToast("نشان‌گذاری شد ⭐"); }
      this.saveBookmarks();
    },
    clearBookmarks() { this.bookmarks = []; this.saveBookmarks(); this.showToast("نشان‌ها پاک شدند"); },
    saveBookmarks() { try { localStorage.setItem("drcode_order_bookmarks", JSON.stringify(this.bookmarks)); } catch (e) {} },
    loadBookmarks() { try { const b = localStorage.getItem("drcode_order_bookmarks"); if (b) this.bookmarks = JSON.parse(b) || []; } catch (e) {} },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-4): TOC mini-map (visual section overview)
    // ─────────────────────────────────────────────────────────────────────────
    buildMinimap() {
      this.$nextTick(() => {
        const list = this.sectionNavList.map(s => {
          const el = document.getElementById(s.anchor);
          return { anchor: s.anchor, label: s.label, height: el ? el.offsetHeight : 40, prefix: this._prefixFor(s.anchor) };
        });
        this.minimapSegments = list;
      });
    },
    _prefixFor(anchorId) {
      if (anchorId === "anchor-preclinical") return "df-";
      if (anchorId === "anchor-order-info") return "field-";
      if (anchorId === "anchor-order-sections") return "section-";
      if (anchorId === "anchor-disposition") return "disp-";
      if (anchorId === "anchor-media") return "media-";
      return "";
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-5): Print-to-PDF (premium) — bypasses @media print protection
    // ─────────────────────────────────────────────────────────────────────────
    printToPdf() {
      if (!this.isPremiumUser) { this.showToast("چاپ ویژه کاربران Premium است"); return; }
      this.showToast("در حال آماده‌سازی برای چاپ...");
      this.$nextTick(() => {
        document.body.classList.add("mp-print-mode");
        setTimeout(() => {
          window.print();
          // Cleanup after print dialog closes
          setTimeout(() => { document.body.classList.remove("mp-print-mode"); }, 500);
        }, 300);
      });
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-5): Export order content to Markdown file
    // ─────────────────────────────────────────────────────────────────────────
    exportMarkdown() {
      let md = "# " + (this.order?.name || "اوردر") + "\n\n";
      if (this.order?.notes) { md += "> " + this.order.notes.replace(/<[^>]+>/g, "").slice(0, 200) + "\n\n"; }
      md += "**دسته:** " + (this.order?.category?.title || "-") + "  \n";
      md += "**زمان مطالعه:** " + this.readingTimeMin + " دقیقه  \n\n";
      // Preclinical
      if (this.dynamicFields?.dynamic_field_groups?.length) {
        md += "## پیش‌بالینی\n\n";
        this.dynamicFields.dynamic_field_groups.forEach(g => {
          md += "### " + g.title + "\n\n";
          (g.nodes || []).forEach(n => {
            md += "- **" + n.title + "**\n";
            if (n.content) { md += "  " + n.content.replace(/<[^>]+>/g, "").slice(0, 150) + "\n"; }
            (n.children || []).forEach(c => { md += "  - " + c.title + "\n"; });
          });
          md += "\n";
        });
      }
      // Base info
      md += "## اطلاعات پایه\n\n";
      this.infoFields().forEach(f => { md += "- **" + f.labelFa + ":** " + (f.value || "-") + "\n"; });
      md += "\n";
      // Sections
      if (this.sections?.sections?.length) {
        md += "## بخش‌ها و دستورات\n\n";
        this.sections.sections.forEach(s => {
          md += "### " + s.title + "\n\n";
          (s.items || []).forEach(it => { md += "- " + (it.text || "") + "\n"; });
          md += "\n";
        });
      }
      // Disposition
      if (this.disposition?.emergency_disposition) {
        const d = this.disposition.emergency_disposition;
        md += "## " + d.title + "\n\n";
        (d.nodes || []).forEach(n => {
          md += "### " + n.title + "\n\n";
          (n.children || []).forEach(c => { md += "- " + c.title + "\n"; });
          md += "\n";
        });
      }
      // Download
      const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = (this.order?.name || "order").replace(/[^a-zA-Z0-9آ-ی]/g, "_") + ".md";
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
      this.showToast("فایل Markdown دانلود شد 📥");
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-5): Content stats modal
    // ─────────────────────────────────────────────────────────────────────────
    openStats() { this.computeContentStats(); this.statsOpen = true; document.body.classList.add("modal-open"); },
    closeStats() { this.statsOpen = false; document.body.classList.remove("modal-open"); },
    computeContentStats() {
      this.$nextTick(() => {
        const sections = this.sectionNavList.map(s => {
          const el = document.getElementById(s.anchor);
          const text = el ? el.innerText : "";
          const words = text.trim().split(/\s+/).filter(Boolean).length;
          return { anchor: s.anchor, label: s.label, words };
        });
        const totalWords = sections.reduce((sum, s) => sum + s.words, 0);
        const maxWords = Math.max(...sections.map(s => s.words), 1);
        sections.forEach(s => { s.percent = Math.round((s.words / maxWords) * 100); });
        this.contentStats = { totalWords, totalSections: sections.length, sectionStats: sections };
      });
    },

    // ─────────────────────────────────────────────────────────────────────────
    // NEW (DJANGO-SYNC-5): Focus mode — dims other sections, highlights active
    // ─────────────────────────────────────────────────────────────────────────
    toggleFocusMode() {
      this.focusMode = !this.focusMode;
      if (this.focusMode) {
        document.body.classList.add("mp-focus-mode");
        this._applyFocusHighlight();
        this.showToast("حالت تمرکز فعال شد — Esc برای خروج");
      } else {
        document.body.classList.remove("mp-focus-mode");
        this._clearFocusHighlight();
        this.showToast("حالت تمرکز غیرفعال شد");
      }
    },
    _applyFocusHighlight() {
      const sections = document.querySelectorAll("#order__section > .main-section, #order__section > section.main-section, #order__section section[id^='anchor-']");
      // Also include the question section
      const all = [...sections, document.getElementById("order-question-section")].filter(Boolean);
      all.forEach(sec => sec.classList.remove("mp-focused"));
      // Find the currently active section
      if (this.activeAnchor) {
        const activeSec = this._findSectionForAnchor(this.activeAnchor);
        if (activeSec) activeSec.classList.add("mp-focused");
      }
    },
    _clearFocusHighlight() {
      document.querySelectorAll(".mp-focused").forEach(el => el.classList.remove("mp-focused"));
    },
    _findSectionForAnchor(anchorId) {
      // Map anchor to its parent section element
      const map = {
        "df-": "anchor-preclinical",
        "field-": "anchor-order-info",
        "order-info": "anchor-order-info",
        "section-": "anchor-order-sections",
        "order-sections": "anchor-order-sections",
        "disp-": "anchor-disposition",
        "media-": "anchor-media",
        "anchor-media": "anchor-media",
        "order-question-section": "order-question-section",
      };
      for (const prefix in map) {
        if (anchorId.startsWith(prefix) || anchorId === map[prefix]) {
          return document.getElementById(map[prefix]);
        }
      }
      return null;
    },
  };
}

// =============================================================================
// Watermark Protection
// =============================================================================
function createOrderProtectedWatermark() {
  // ـــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــ
  // واترمارک — نسخهٔ ۲٫۰
  // از یک SVG tile با متن چرخیده استفاده میکند و آن را بهصورت background-image
  // تکرارپذیر روی کل ارتفاع #order__section میچیند. این‌طوری:
  //   ① واترمارک کل اوردر (پیش‌بالینی، اطلاعات پایه، بخش‌ها، تعیین تکلیف) را می‌پوشاند
  //   ② وقتی یک node باز/بسته می‌شود و ارتفاع section تغییر میکند، تایل‌ها بهصورت
  //      خودکار کل سطح جدید را پر میکنند — بدون نیاز به recompute و بدون پرش
  //   ③ واترمارک روی هیچ بخشی «متوقف» نمی‌شود و از روی اطلاعات پایه هم برداشته نمی‌شود
  // ــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــــ
  function buildWatermarkSvgDataUri(text, fontSize, tileW, tileH) {
    const safe = String(text || "drcode-med.ir")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

    const cx1 = tileW / 2;
    const cy1 = tileH / 2;
    const cx2 = tileW / 2;
    const cy2 = tileH / 2 + tileH; // ردیف دوم — انتهای tile (با شروع tile بعدی تراز می‌شود)

    const svg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="' + tileW + '" height="' + tileH + '">' +
        '<g fill="rgba(15,23,42,0.06)" font-family="Arial, Helvetica, sans-serif" font-size="' + fontSize + '" font-weight="700">' +
          '<text x="' + cx1 + '" y="' + cy1 + '" text-anchor="middle" dominant-baseline="middle" transform="rotate(-45 ' + cx1 + ' ' + cy1 + ')">' + safe + '</text>' +
          '<text x="' + cx2 + '" y="' + cy2 + '" text-anchor="middle" dominant-baseline="middle" transform="rotate(-45 ' + cx2 + ' ' + cy2 + ')">' + safe + '</text>' +
        '</g>' +
      '</svg>';

    return 'data:image/svg+xml;charset=utf8,' + encodeURIComponent(svg);
  }

  function addWatermark() {
    const targetSection = document.getElementById("order__section");
    if (!targetSection) return;

    const style = getComputedStyle(targetSection);
    if (style.display === "none" || style.visibility === "hidden" || targetSection.offsetHeight === 0) return;

    if (targetSection.querySelector("#order-protected-watermark")) return;

    const computedStyle = getComputedStyle(targetSection);
    if (computedStyle.position === "static") {
      targetSection.style.position = "relative";
    }

    let medi, mediObject;
    try {
      medi = localStorage.getItem("drcode_user_profile");
      mediObject = JSON.parse(medi)?.data;
    } catch (e) {
      medi = null;
    }
    const text = (medi && mediObject?.medical_code) ? mediObject.medical_code : "drcode-med.ir";

    const isMobile = window.innerWidth < 768;
    const fontSize = isMobile ? 22 : 28;
    const tileW = isMobile ? 220 : 280;
    const tileH = isMobile ? 180 : 220;

    const bgUrl = buildWatermarkSvgDataUri(text, fontSize, tileW, tileH);

    const watermark = document.createElement("div");
    watermark.id = "order-protected-watermark";
    // height:100% → با رشد محتوای #order__section بزرگ می‌شود؛ background-repeat:repeat
    // بهصورت خودکار کل سطح (حتی قسمت‌های جدید) را تایل میکند.
    watermark.style.cssText =
      "position: absolute; top: 0; left: 0; width: 100%; height: 100%;" +
      "pointer-events: none; z-index: 1; overflow: hidden;" +
      "background-image: url(\"" + bgUrl + "\");" +
      "background-repeat: repeat;" +
      "background-position: 0 0;" +
      "background-size: " + tileW + "px " + tileH + "px;";

    targetSection.insertBefore(watermark, targetSection.firstChild);
  }

  function rebuildWatermark() {
    const targetSection = document.getElementById("order__section");
    if (!targetSection) return;
    const existing = targetSection.querySelector("#order-protected-watermark");
    if (existing) existing.remove();
    addWatermark();
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
    resizeTimeout = setTimeout(rebuildWatermark, 300);
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