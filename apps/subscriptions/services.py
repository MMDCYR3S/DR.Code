from django.utils import timezone
from django.db.models import Max


def sync_user_profile(user):
    """
    نقش و تاریخ انقضای پروفایل کاربر را بر اساس همه اشتراک‌های فعالش همگام می‌کند.
    این تابع باید بعد از هر تغییر روی اشتراک‌ها صدا زده شود.
    """
    try:
        profile = user.profile
    except Exception:
        return

    # ادمین همیشه ادمین می‌مونه
    if profile.role == 'admin':
        return

    from apps.subscriptions.models import Subscription, SubscriptionStatusChoicesModel

    now = timezone.now()
    max_end = Subscription.objects.filter(
        user=user,
        status=SubscriptionStatusChoicesModel.active.value,
        end_date__gt=now,
    ).aggregate(m=Max('end_date'))['m']

    if max_end:
        profile.role = 'premium'
        profile.subscription_end_date = max_end
    else:
        profile.role = 'regular'
        profile.subscription_end_date = None

    profile.save(update_fields=['role', 'subscription_end_date'])