from django.contrib.sitemaps import Sitemap
from .models import Prescription

class PrescriptionSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9
    protocol = 'https'

    def items(self):
        """
        فقط نسخه‌هایی را برمی‌گرداند که فعال هستند.
        اگر می‌خواهید فقط نسخه‌های رایگان ایندکس شوند، شرط access_level را هم اضافه کنید.
        """
        return Prescription.objects.filter(is_active=True)

    def lastmod(self, obj):
        """
        آخرین زمان تغییر را به گوگل اعلام می‌کند
        تا بداند آیا نیاز به خزش مجدد هست یا خیر
        """
        return obj.updated_at