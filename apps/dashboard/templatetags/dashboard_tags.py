"""
templatetags/dashboard_tags.py

استفاده در تمپلیت:
  {% load dashboard_tags %}

  {# وضعیت access_level #}
  {% access_level_badge prescription %}

  {# رنگ‌دار کردن ردیف جدول با رنگ دسته‌بندی #}
  {% category_color_dot color_code %}

  {# تبدیل تاریخ میلادی به شمسی (اگر کتابخانه jdatetime نصب باشه) #}
  {{ some_date|jalali_date }}

  {# کوتاه کردن متن با تعداد کلمه دلخواه #}
  {{ long_text|truncate_words_fa:10 }}

  {# نمایش عدد با جداکننده هزارگان فارسی #}
  {{ number|persian_number }}
"""

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


# ─────────────────────────────────────────────
# Badge سطح دسترسی
# ─────────────────────────────────────────────
@register.simple_tag
def access_level_badge(obj, field_name='access_level'):
    """
    نمایش badge وضعیت دسترسی.
    مقادیر: PREMIUM → «ویژه» (سبز) | هر چیز دیگری → «رایگان» (آبی)
    """
    level = getattr(obj, field_name, None)
    if level == 'PREMIUM':
        return format_html(
            '<span class="px-2.5 py-0.5 text-xs font-semibold text-white '
            'bg-green-500 rounded-full">ویژه</span>'
        )
    return format_html(
        '<span class="px-2.5 py-0.5 text-xs font-semibold text-blue-700 '
        'bg-blue-100 rounded-full">رایگان</span>'
    )


# ─────────────────────────────────────────────
# نقطه رنگی دسته‌بندی
# ─────────────────────────────────────────────
@register.simple_tag
def category_color_dot(color_code, size='sm'):
    """
    نمایش یک دایره رنگی Tailwind.
    size: 'sm' (w-3 h-3) | 'md' (w-4 h-4) | 'lg' (w-5 h-5)
    """
    size_classes = {'sm': 'w-3 h-3', 'md': 'w-4 h-4', 'lg': 'w-5 h-5'}
    s = size_classes.get(size, 'w-3 h-3')
    safe_color = color_code or 'bg-slate-400'
    return format_html(
        '<span class="inline-block {} {} rounded-full flex-shrink-0"></span>',
        s, safe_color
    )


# ─────────────────────────────────────────────
# فیلتر: تبدیل تاریخ به شمسی
# ─────────────────────────────────────────────
@register.filter(name='jalali_date')
def jalali_date(value, fmt='%Y/%m/%d'):
    """
    تبدیل datetime میلادی به شمسی.
    نیازمند نصب: pip install jdatetime
    """
    if not value:
        return '—'
    try:
        import jdatetime
        if hasattr(value, 'date'):
            jd = jdatetime.datetime.fromgregorian(datetime=value)
        else:
            jd = jdatetime.date.fromgregorian(date=value)
        return jd.strftime(fmt)
    except ImportError:
        return value.strftime('%Y/%m/%d') if hasattr(value, 'strftime') else str(value)
    except Exception:
        return str(value)


# ─────────────────────────────────────────────
# فیلتر: کوتاه کردن با کلمه
# ─────────────────────────────────────────────
@register.filter(name='truncate_words_fa')
def truncate_words_fa(value, max_words=10):
    """کوتاه کردن متن بر اساس تعداد کلمه."""
    if not value:
        return ''
    words = str(value).split()
    if len(words) <= int(max_words):
        return value
    return ' '.join(words[:int(max_words)]) + '…'


# ─────────────────────────────────────────────
# فیلتر: اعداد با جداکننده
# ─────────────────────────────────────────────
@register.filter(name='persian_number')
def persian_number(value):
    """نمایش عدد با جداکننده هزارگان."""
    try:
        return '{:,}'.format(int(value))
    except (ValueError, TypeError):
        return value


# ─────────────────────────────────────────────
# Tag: Empty State
# ─────────────────────────────────────────────
@register.inclusion_tag('dashboard/partials/_empty_state.html')
def empty_state(icon='fa-inbox', title='موردی یافت نشد',
                description='', action_url='', action_label=''):
    """
    نمایش حالت خالی همگانی.
    مثال:
      {% empty_state icon="fa-file-medical" title="هیچ اوردری یافت نشد"
                     action_url="/orders/create/" action_label="اوردر جدید" %}
    """
    return {
        'icon': icon,
        'title': title,
        'description': description,
        'action_url': action_url,
        'action_label': action_label,
    }


# ─────────────────────────────────────────────
# Tag: Active Nav Class
# ─────────────────────────────────────────────
@register.simple_tag(takes_context=True)
def active_if(context, url_name):
    """
    اگر URL فعلی با url_name مطابقت داشت، کلاس 'active' برمی‌گردونه.
    مثال: class="{% active_if 'dashboard:ordering:order_list' %}"
    """
    request = context.get('request')
    if not request:
        return ''
    try:
        from django.urls import resolve
        resolved = resolve(request.path_info)
        if resolved.view_name == url_name:
            return mark_safe('active')
    except Exception:
        pass
    return ''