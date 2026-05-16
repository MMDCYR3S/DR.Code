from django.db import models


class TailwindColor(models.TextChoices):
    """
    ۳۰ رنگ خالص از پالت Tailwind CSS.
    مقدار هر گزینه نام رنگ خالص است (بدون پیشوند bg- و بدون عدد shade).
    در قالب می‌توان به‌صورت دلخواه از آن‌ها استفاده کرد:
        bg-{{ obj.color }}-500  یا  text-{{ obj.color }}-700  و ...
    """
    SLATE      = "slate",      "اسلیت (خاکستری‌آبی)"
    GRAY       = "gray",       "خاکستری"
    ZINC       = "zinc",       "زینک"
    NEUTRAL    = "neutral",    "خنثی"
    STONE      = "stone",      "سنگی"
    RED        = "red",        "قرمز"
    ORANGE     = "orange",     "نارنجی"
    AMBER      = "amber",      "کهربایی"
    YELLOW     = "yellow",     "زرد"
    LIME       = "lime",       "لیمویی"
    GREEN      = "green",      "سبز"
    EMERALD    = "emerald",    "زمردی"
    TEAL       = "teal",       "فیروزه‌ای"
    CYAN       = "cyan",       "آبی‌فیروزه‌ای"
    SKY        = "sky",        "آبی آسمانی"
    BLUE       = "blue",       "آبی"
    INDIGO     = "indigo",     "نیلی"
    VIOLET     = "violet",     "بنفش"
    PURPLE     = "purple",     "ارغوانی"
    FUCHSIA    = "fuchsia",    "فوشیا"
    PINK       = "pink",       "صورتی"
    ROSE       = "rose",       "گلی"
    MAGENTA    = "magenta",    "سرخابی"
    OLIVE       = "olive",      "زیتونی"