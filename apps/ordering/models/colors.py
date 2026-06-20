from django.db import models


class TailwindColor(models.TextChoices):
    """
    رنگ‌ها به صورت مقدار HEX ذخیره می‌شوند.
    label فارسی برای نمایش در admin/forms استفاده می‌شود.
    """
    SLATE      = "#64748b",  "اسلیت (خاکستری‌آبی)"
    GRAY       = "#6b7280",  "خاکستری"
    ZINC       = "#71717a",  "زینک"
    NEUTRAL    = "#737373",  "خنثی"
    STONE      = "#78716c",  "سنگی"
    RED        = "#ef4444",  "قرمز"
    ORANGE     = "#f97316",  "نارنجی"
    AMBER      = "#f59e0b",  "کهربایی"
    YELLOW     = "#eab308",  "زرد"
    LIME       = "#84cc16",  "لیمویی"
    GREEN      = "#22c55e",  "سبز"
    EMERALD    = "#10b981",  "زمردی"
    TEAL       = "#14b8a6",  "فیروزه‌ای"
    CYAN       = "#06b6d4",  "آبی‌فیروزه‌ای"
    SKY        = "#0ea5e9",  "آبی آسمانی"
    BLUE       = "#3b82f6",  "آبی"
    INDIGO     = "#6366f1",  "نیلی"
    VIOLET     = "#8b5cf6",  "بنفش"
    PURPLE     = "#a855f7",  "ارغوانی"
    FUCHSIA    = "#d946ef",  "فوشیا"
    PINK       = "#ec4899",  "صورتی"
    ROSE       = "#f43f5e",  "گلی"
    MAGENTA    = "#c026d3",  "سرخابی"
    OLIVE      = "#65a30d",  "زیتونی"
