from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    """برای صفحات استاتیک مثل درباره ما و تماس با ما"""
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
       return [
            'home:index',      # صفحه اصلی
            'home:about',      # درباره ما
            'home:contact',    # تماس با ما
            'home:tutorials',  # آموزش‌ها
            'home:plan',       # پلن‌ها
            'home:rules',      # قوانین
            'home:privacy'     # حریم خصوصی
        ]
    def location(self, item):
        return reverse(item)