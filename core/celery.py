import os
from celery import Celery

# تنظیم Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.production')

# ساخت app سلری
app = Celery('core')

# خواندن config از Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# پیدا کردن خودکار taskها
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """تسک تستی برای دیباگ"""
    print(f'Request: {self.request!r}')
