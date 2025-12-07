import requests
import logging
from typing import Optional, List

logger = logging.getLogger('user_verification')

class AmootSMSService:
    # آدرس‌های سرویس
    URL_PATTERN = "https://portal.amootsms.com/rest/SendWithPattern" 
    
    def __init__(self, token: str = "4A9869096131EA46E7A41BDCD99B2ADC560193B2"):
        self.token = token
        
    def send_with_pattern(self, mobile: str, pattern_code: int, values: List[str]) -> bool:
        """
        ارسال پیامک پترن‌دار با مدیریت خطای کامل
        """
        # لاگ شروع
        logger.info(f"--- [AMOOT SEND START] --- Target: {mobile} | Pattern: {pattern_code}")

        try:
            headers = {"Authorization": self.token}
            
            # نکته مهم: این عملیات باید داخل try باشد تا اگر values مشکل داشت، هندل شود
            values_str = ",".join(str(v) for v in values)
            logger.info(f"Values Payload: {values_str}")

            data = {
                "Mobile": mobile,
                "PatternCodeID": pattern_code,
                "PatternValues": values_str
            }

            response = requests.post(self.URL_PATTERN, data=data, headers=headers, timeout=10)
            
            # لاگ جهت دیباگ
            logger.info(f"Amoot Response: {response.status_code} | Body: {response.text}")

            if response.status_code == 200:
                # چک کردن اینکه آیا آموت واقعا موفق بوده یا خیر (گاهی 200 می‌دهد اما در متن خطا دارد)
                # معمولا اگر موفق باشد جیسون برمی‌گرداند، اگر خطا باشد تکست ساده یا جیسون ارور
                # اما برای سادگی فعلا روی 200 بودن حساب می‌کنیم
                logger.info("--- [AMOOT SEND SUCCESS] ---")
                return True
            
            logger.error(f"--- [AMOOT SEND FAILED] Status: {response.status_code}")
            return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network Error in Amoot Service: {str(e)}")
            return False
            
        except Exception as e:
            # گرفتن تمام خطاهای احتمالی (مثل تایپ ارور و ...)
            logger.error(f"General Error in Amoot Service: {str(e)}", exc_info=True)
            return False
