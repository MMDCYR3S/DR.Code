import requests
from datetime import datetime
from typing import List, Optional

# ===== Amoot SMS Service ===== #
class AmootSMSService:
    """
    سرویس ارسال پیامک از طریق پیام‌رسان آموت اس ام اس
    """
    
    BASE_URL = "https://portal.amootsms.com/rest/SendSimple"

    def __init__(self, token: str = "MyToken", line_number: str = "public"):
        """
        بررسی اولیه سرویس با استفاده از توکن و شماره خط ثابت
        
        :param token: توکن امنیتی برای ارتباط با API
        :param line_number: شماره خط ثابت برای ارسال پیامک
        """
        self.token = token
        self.line_number = line_number

    def send_message(self, mobiles: List[str], message_text: str) -> Optional[str]:
        """
        ارسال پیامک به یک یا چند شماره موبایل

        :param mobiles: لیست از شماره موبایل (رشته).
        :param message_text: متن پیامک.
        :return: پاسخ API در صورت موفقیت، None در صورت عدم موفقیت.
        """
        
        # ===== زمان ارسال پیامک ===== #
        send_date_time = datetime.now().isoformat()
        
        # ===== پارامترهای ارسالی ===== #
        data = {
            "SendDateTime": send_date_time,
            "SMSMessageText": message_text,
            "LineNumber": self.line_number,
            "Mobiles": ",".join(mobiles),
        }

        try:
            # ===== ارسال پیامک ===== #
            response = requests.post(self.BASE_URL, data=data)
            response.raise_for_status()
            
            # ===== پاسخ را دریافت و بازگرداندن ===== #
            return response.text
            
        except requests.RequestException as e:
            # ===== در صورت خطایی، پیام خطا را چاپ کرده و چیزی را باز نمی گرداند ===== #
            print(f"خطا در ارسال پیامک: {e}")
            return None

    def send_verification_code(self, mobile: str, code_length: int = 4, optional_code: str = "") -> Optional[str]:
        """
        ارسال پیام اعتبارسنجی به شماره تلفن کاربر
        
        :param mobile: شماره تلفن کاربر
        :param code_length: طول کد اعتبارسنجی
        :param optional_code: کد اعتبارسنجی اختیاری
        :return: پاسخ آدرس در صورت موفقیت، در صورت عدم موفقیت، خطا.
        """
        
        data = {
            "Mobile": mobile,
            "CodeLength": str(code_length),
            "OptionalCode": optional_code,
        }

        try:
            # ===== ارسال کد اعتبارسنجی ===== #
            response = requests.post("https://portal.amootsms.com/rest/SendQuickOTP", data=data)
            response.raise_for_status()
            
            # ===== پاسخ را دریافت و بازگرداندن ===== #
            return response.text
            
        except requests.RequestException as e:
            print(f"خطا در ارسال پیامک: {e}")
            return None
