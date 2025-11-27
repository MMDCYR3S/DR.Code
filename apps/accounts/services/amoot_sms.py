import requests
import logging
from typing import Optional, List

# فراخوانی لاگر اختصاصی که در تنظیمات ساختیم
logger = logging.getLogger('user_verification')

class AmootSMSService:
    # ===== Constants ===== #
    BASE_URL = "https://portal.amootsms.com/rest/SendSimple"
    URL_SIMPLE = "https://portal.amootsms.com/rest/SendSimple"
    
    # *** آدرس صحیح پترن ***
    URL_PATTERN = "https://portal.amootsms.com/rest/SendWithPattern" 
    
    def __init__(self, token: str = "4A9869096131EA46E7A41BDCD99B2ADC560193B2", line_number: str = "public"):
        self.token = token
        self.line_number = line_number
        
    def send_with_pattern(self, mobile: str, pattern_code: int, values: List[str]) -> bool:
        """
        ارسال پیامک با الگوی خاص به همراه لاگ دقیق
        """
        headers = {"Authorization": self.token}
        
        # تبدیل لیست به رشته
        values_str = ",".join(str(v) for v in values)

        data = {
            "Mobile": mobile,
            "PatternCodeID": pattern_code,
            "PatternValues": values_str
        }

        # لاگ قبل از ارسال (برای دیدن دیتای خروجی)
        logger.info(f"--- [AMOOT SEND START] ---")
        logger.info(f"Target: {mobile} | Pattern: {pattern_code} | Values: {values_str}")

        try:
            response = requests.post(self.URL_PATTERN, data=data, headers=headers, timeout=10)
            
            # لاگ پاسخ دریافت شده (بسیار مهم برای دیباگ)
            logger.info(f"Amoot Response Status: {response.status_code}")
            logger.info(f"Amoot Response Body: {response.text}")

            if response.status_code == 200:
                # گاهی اوقات استاتوس 200 است اما در متن بادی خطا وجود دارد
                # آموت معمولاً در صورت موفقیت آبجکت جیسون برمی‌گرداند
                logger.info("--- [AMOOT SEND SUCCESS] ---")
                return True
            
            logger.error(f"--- [AMOOT SEND FAILED] Status: {response.status_code}")
            return False

        except requests.exceptions.RequestException as e:
            # خطاهای شبکه (تایم‌اوت، قطعی اینترنت و ...)
            logger.error(f"Network Error in Amoot Service: {str(e)}")
            return False
            
        except Exception as e:
            # خطاهای کلی پایتون
            logger.error(f"General Error in Amoot Service: {str(e)}")
            return False
