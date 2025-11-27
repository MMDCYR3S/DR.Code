import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

from django.conf import settings

# ===== Google Analytics Service ===== #
class GoogleAnalyticsService:
    """
    سرویس گوگل که اطلاعات مربوط به وبسایت رو دریافت میکنه
    و در یک قالب نمایش میده.
    """
    def __init__(self):
        """
        مقداردهی اولیه کلاینت و تنظیم فایل اعتبارسنجی
        """
        # دریافت تنظیمات از settings.py
        self.property_id = getattr(settings, 'GA4_PROPERTY_ID', None)
        self.key_file_path = os.path.join(settings.BASE_DIR, 'dr-code-analytics.json')

        if not self.property_id:
            raise ValueError("GA4_PROPERTY_ID is not set in Django settings.")

        # تنظیم Environment Variable برای دسترسی کتابخانه گوگل
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.key_file_path
        self.client = BetaAnalyticsDataClient()

    def get_last_7_days_report(self):
        """
        دریافت گزارش بازدید ۷ روز گذشته
        خروجی: لیستی از دیکشنری‌ها شامل تاریخ، کاربران فعال و بازدید صفحات
        """
        try:
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name="date")],
                metrics=[
                    Metric(name="activeUsers"),
                    Metric(name="screenPageViews")
                ],
                date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            )

            response = self.client.run_report(request)

            data = []
            for row in response.rows:
                data.append({
                    "date": row.dimension_values[0].value,
                    # مقادیر متریک به صورت رشته برمی‌گردند، تبدیل به int می‌کنیم
                    "active_users": int(row.metric_values[0].value),
                    "page_views": int(row.metric_values[1].value),
                })

            # ===== مرتب سازی براساس تاریخ بازدید ===== #
            data.sort(key=lambda x: x['date'])
            return data

        except Exception as e:
            print(f"Google Analytics API Error: {e}")
            return []
