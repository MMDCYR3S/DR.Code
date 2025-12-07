import requests
import json
import logging
from django.conf import settings

# ایجاد لاگر اختصاصی که در تنظیمات تعریف کردیم
logger = logging.getLogger('zarinpal')

class ZarinpalService:
    """
    سرویسی برای مدیریت تمام عملیات‌های مربوط به درگاه پرداخت زرین‌پال.
    دارای سیستم لاگ‌گیری کامل برای ردیابی تراکنش‌ها.
    """

    def __init__(self):
        try:
            config = settings.ZARINPAL_CONFIG
            self.merchant_id = config['MERCHANT_ID']
            self.is_sandbox = config.get('SANDBOX', False)

            if self.is_sandbox:
                base_url = 'https://sandbox.zarinpal.com/pg/v4/payment/'
                self.start_pay_url_template = 'https://sandbox.zarinpal.com/pg/StartPay/{authority}'
                logger.info("ZarinpalService initialized in SANDBOX mode.")
            else:
                base_url = 'https://api.zarinpal.com/pg/v4/payment/'
                self.start_pay_url_template = 'https://www.zarinpal.com/pg/StartPay/{authority}'
                logger.info("ZarinpalService initialized in PRODUCTION mode.")
                
            self.request_url = f"{base_url}request.json"
            self.verify_url = f"{base_url}verify.json"
            
        except Exception as e:
            logger.critical(f"Failed to initialize ZarinpalService. Check settings. Error: {str(e)}")
            raise

    def create_payment_request(self, amount: int, description: str, callback_url: str, metadata: dict = None) -> dict:
        """
        ایجاد درخواست پرداخت با لاگ‌گیری دقیق.
        """
        # لاگ شروع عملیات (بدون متادیتا برای جلوگیری از شلوغی، مگر نیاز باشد)
        logger.info(f"Create Payment Request | Amount: {amount} | Desc: {description}")

        request_data = {
            "merchant_id": self.merchant_id,
            "amount": int(amount),
            "description": description,
            "callback_url": callback_url,
        }
        if metadata:
            request_data["metadata"] = metadata

        try:
            response = requests.post(
                url=self.request_url,
                data=json.dumps(request_data),
                headers={'Content-Type': 'application/json'},
                timeout=10 # اضافه کردن تایم‌اوت برای جلوگیری از هنگ کردن
            )
            
            # اگر خطای http (مثل 500 یا 404) باشد اینجا ریز می‌شود
            if response.status_code != 200:
                logger.error(f"HTTP Error in Request | Status: {response.status_code} | Body: {response.text}")
                response.raise_for_status()

            response_json = response.json()
            data = response_json.get('data', {})
            errors = response_json.get('errors', [])

            if data and data.get('code') == 100:
                authority = data['authority']
                payment_url = self.start_pay_url_template.format(authority=authority)
                
                # لاگ موفقیت‌آمیز بودن درخواست با Authority
                logger.info(f"Payment Request Success | Authority: {authority} | Amount: {amount}")
                
                return {
                    'success': True,
                    'authority': authority,
                    'payment_url': payment_url,
                    'error': None
                }
            else:
                # لاگ خطای منطقی از سمت زرین‌پال
                error_code = errors.get('code', 'Unknown')
                error_message = errors.get('message', 'خطای نامشخص')
                logger.error(f"Zarinpal API Error (Request) | Code: {error_code} | Message: {error_message}")
                
                return {
                    'success': False,
                    'error': f"خطا در ایجاد تراکنش ({error_code}): {error_message}",
                    'authority': None,
                    'payment_url': None
                }

        except requests.exceptions.Timeout:
            logger.error("Zarinpal Request Timeout")
            return {
                'success': False,
                'error': "خطای مهلت زمانی (Timeout) در اتصال به درگاه.",
                'authority': None,
                'payment_url': None
            }
        except requests.exceptions.RequestException as e:
            logger.exception(f"Connection Error in create_payment_request: {str(e)}")
            return {
                'success': False,
                'error': "خطای ارتباط با درگاه پرداخت.",
                'authority': None,
                'payment_url': None
            }
        except Exception as e:
            logger.exception("Unexpected Error in create_payment_request")
            return {
                'success': False,
                'error': "خطای پیش‌بینی نشده در سیستم.",
                'authority': None,
                'payment_url': None
            }

    def verify_payment(self, authority: str, amount: int) -> dict:
        """
        تایید نهایی پرداخت با لاگ‌گیری وضعیت.
        """
        logger.info(f"Verify Payment Started | Authority: {authority} | Amount: {amount}")

        request_data = {
            "merchant_id": self.merchant_id,
            "authority": authority,
            "amount": int(amount),
        }
        
        try:
            response = requests.post(
                url=self.verify_url,
                data=json.dumps(request_data),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"HTTP Error in Verify | Authority: {authority} | Status: {response.status_code}")
                response.raise_for_status()

            response_json = response.json()
            data = response_json.get('data', {})
            errors = response_json.get('errors', [])
            
            code = data.get('code') if data else None

            if code in [100, 101]:
                ref_id = data.get('ref_id')
                card_pan = data.get('card_pan', 'Unknown')
                
                # لاگ تراکنش موفقیت آمیز (مهمترین لاگ)
                msg_type = "Verified" if code == 100 else "Already Verified"
                logger.info(f"Payment {msg_type} Success | Authority: {authority} | RefID: {ref_id} | Card: {card_pan}")
                
                return {
                    'success': True,
                    'ref_id': ref_id,
                    'card_pan': card_pan,
                    'code': code,
                    'error': None
                }
            else:
                error_code = errors.get('code', 'Unknown')
                error_message = errors.get('message', 'خطای نامشخص')
                
                # لاگ شکست تراکنش (مثلا کاربر انصراف داده یا موجودی نداشته)
                logger.warning(f"Payment Verify Failed | Authority: {authority} | Code: {error_code} | Msg: {error_message}")
                
                return {
                    'success': False,
                    'error': f"پرداخت ناموفق بود ({error_code}): {error_message}",
                    'ref_id': None
                }

        except requests.exceptions.RequestException as e:
            logger.exception(f"Connection Error in verify_payment | Authority: {authority}")
            return {
                'success': False,
                'error': "خطای ارتباط با درگاه برای تایید پرداخت.",
                'ref_id': None
            }
        except Exception as e:
            logger.exception(f"Unexpected Error in verify_payment | Authority: {authority}")
            return {
                'success': False,
                'error': "خطای پیش‌بینی نشده در تایید پرداخت.",
                'ref_id': None
            }