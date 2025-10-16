import requests
import json
from django.conf import settings

class ZarinpalService:
    """
    سرویسی برای مدیریت تمام عملیات‌های مربوط به درگاه پرداخت زرین‌پال.
    این کلاس با تنظیمات Sandbox یا Production کار می‌کند.
    """

    def __init__(self):
        """
        مقداردهی اولیه سرویس با خواندن تنظیمات از فایل settings.py
        """
        config = settings.ZARINPAL_CONFIG
        self.merchant_id = config['MERCHANT_ID']
        self.is_sandbox = config.get('SANDBOX', False)

        # تعیین URL ها بر اساس حالت sandbox یا production
        if self.is_sandbox:
            base_url = 'https://sandbox.zarinpal.com/pg/v4/payment/'
            self.start_pay_url_template = 'https://sandbox.zarinpal.com/pg/StartPay/{authority}'
        else:
            base_url = 'https://api.zarinpal.com/pg/v4/payment/'
            self.start_pay_url_template = 'https://www.zarinpal.com/pg/StartPay/{authority}'
            
        self.request_url = f"{base_url}request.json"
        self.verify_url = f"{base_url}verify.json"
        
    def create_payment_request(self, amount: int, description: str, callback_url: str, metadata: dict = None) -> dict:
        """
        ایجاد یک درخواست پرداخت جدید در زرین‌پال.

        :param amount: مبلغ تراکنش به تومان.
        :param description: توضیحات تراکنش.
        :param callback_url: آدرس URL برای بازگشت کاربر پس از پرداخت.
        :param metadata: اطلاعات اضافی (مانند payment_id) که به صورت JSON ذخیره می‌شود.
        :return: یک دیکشنری شامل وضعیت موفقیت، کد رهگیری (authority) و لینک پرداخت.
        """
        request_data = {
            "merchant_id": self.merchant_id,
            "amount": int(amount),  # زرین‌پال مبلغ را به صورت integer می‌پذیرد
            "description": description,
            "callback_url": callback_url,
            "currency": "IRT"
        }
        if metadata:
            request_data["metadata"] = metadata

        try:
            response = requests.post(
                url=self.request_url,
                data=json.dumps(request_data),
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()  # بررسی خطاهای HTTP
            response_json = response.json()
            
            data = response_json.get('data', {})
            errors = response_json.get('errors', [])

            if data and data.get('code') == 100:
                authority = data['authority']
                payment_url = self.start_pay_url_template.format(authority=authority)
                return {
                    'success': True,
                    'authority': authority,
                    'payment_url': payment_url,
                    'error': None
                }
            else:
                error_code = errors.get('code', 'Unknown')
                error_message = errors.get('message', 'خطای نامشخص از سمت درگاه پرداخت.')
                return {
                    'success': False,
                    'error': f"خطا در ایجاد تراکنش ({error_code}): {error_message}",
                    'authority': None,
                    'payment_url': None
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"خطای ارتباط با درگاه پرداخت: {str(e)}",
                'authority': None,
                'payment_url': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"خطای پیش‌بینی نشده: {str(e)}",
                'authority': None,
                'payment_url': None
            }

    def verify_payment(self, authority: str, amount: int) -> dict:
        """
        تایید نهایی پرداخت پس از بازگشت کاربر از درگاه.

        :param authority: کد رهگیری که از زرین‌پال دریافت شده.
        :param amount: مبلغ تراکنش به تومان.
        :return: یک دیکشنری شامل وضعیت موفقیت و شماره مرجع تراکنش (ref_id).
        """
        request_data = {
            "merchant_id": self.merchant_id,
            "authority": authority,
            "amount": int(amount),
            "currency": "IRR"
        }
        
        try:
            response = requests.post(
                url=self.verify_url,
                data=json.dumps(request_data),
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            response_json = response.json()
            
            data = response_json.get('data', {})
            errors = response_json.get('errors', [])
            
            # کد 100 یعنی تراکنش موفق بوده. کد 101 یعنی تراکنش قبلا تایید شده که آن هم موفقیت آمیز است.
            if data and data.get('code') in [100, 101]:
                return {
                    'success': True,
                    'ref_id': data.get('ref_id'),
                    'card_pan': data.get('card_pan', ''),
                    'code': data.get('code'),
                    'error': None
                }
            else:
                error_code = errors.get('code', 'Unknown')
                error_message = errors.get('message', 'خطای نامشخص در تایید پرداخت.')
                return {
                    'success': False,
                    'error': f"پرداخت ناموفق بود ({error_code}): {error_message}",
                    'ref_id': None
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"خطای ارتباط با درگاه برای تایید پرداخت: {str(e)}",
                'ref_id': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"خطای پیش‌بینی نشده در تایید پرداخت: {str(e)}",
                'ref_id': None
            }