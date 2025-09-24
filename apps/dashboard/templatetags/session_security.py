from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def clear_session_key(context, key):
    """
    پاک کردن یک کلید مشخص از session
    """
    request = context.get('request')
    if request and hasattr(request, 'session'):
        try:
            if key in request.session:
                del request.session[key]
                request.session.modified = True
                return f""
        except Exception as e:
            return f""
    return ""

@register.simple_tag(takes_context=True) 
def get_session_key(context, key, default=None):
    """
    دریافت یک کلید از session
    """
    request = context.get('request')
    if request and hasattr(request, 'session'):
        return request.session.get(key, default)
    return default

@register.filter
def to_json(value):
    """
    تبدیل به JSON برای استفاده در JavaScript
    """
    import json
    try:
        return json.dumps(value)
    except:
        return 'null'