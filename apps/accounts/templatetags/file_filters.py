from django import template
import os

register = template.Library()

@register.filter(name='file_filter')
def file_filter(file_url):
    """
    پسوند فایل را از URL یا مسیر فایل استخراج می‌کند.
    مثال: {{ doc.file.url|extension }} -> 'pdf'
    """
    try:
        name, ext = os.path.splitext(file_url)
        return ext.lower().replace('.', '')
    except (ValueError, AttributeError):
        return ''