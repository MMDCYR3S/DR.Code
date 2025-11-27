import requests
from typing import Optional

class AmootSMSService:
    # ===== Constants ===== #
    BASE_URL = "https://portal.amootsms.com/rest/SendSimple"
    URL_SIMPLE = "https://portal.amootsms.com/rest/SendSimple"
    URL_QUICK_OTP = "https://portal.amootsms.com/rest/SendQuickOTP"

    def __init__(self, token: str = "4A9869096131EA46E7A41BDCD99B2ADC560193B2", line_number: str = "public"):
        self.token = token
        self.line_number = line_number

    def send_verification_code(self, mobile: str = "", message_text: str = ""):
        """
        ارسال پیامک با متن دلخواه (متد قدیمی‌تر SendSimple)
        """
        # ===== Payload Configuration ===== #
        payload = {
            "Token": self.token,
            "SMSMessageText": message_text,
            "Mobiles": mobile,
            "LineNumber": self.line_number,
            "SendDateTime": ""
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # ===== Debug Logging ===== #
        print("\n" + "="*20 + " DEBUG: SendSimple " + "="*20)
        print(f"Sending to: {mobile}")
        
        try:
            response = requests.post(self.BASE_URL, data=payload, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            print("="*60 + "\n")

            return response.text

        except Exception as e:
            print(f"Error: {e}")
            return None
            
    def send_quick_otp(self, mobile: str, code_length: int = 6, optional_code: str = "") -> Optional[str]:
        """
        ارسال کد تایید سریع و بهینه (SendQuickOTP)
        """
        # ===== Authorization Headers ===== #
        headers = {"Authorization": self.token}

        data = {
            "Mobile": mobile,
            "CodeLength": str(code_length),
            "OptionalCode": optional_code
        }

        print(f"DEBUG: Sending QuickOTP to {mobile} with Code: {optional_code}")

        try:
            response = requests.post(self.URL_QUICK_OTP, data=data, headers=headers)
            
            print(f"QuickOTP Response Status: {response.status_code}")
            print(f"QuickOTP Response Body: {response.text}")

            if response.status_code == 200:
                return response.text
            return None

        except Exception as e:
            print(f"QuickOTP Service Error: {str(e)}")
            return None

    def send_message(self, mobile: str, message_text: str) -> Optional[str]:
        """
        ارسال پیامک اطلاع‌رسانی با متن دلخواه (SendSimple)
        """
        # ===== Payload Setup ===== #
        payload = {
            "Token": self.token,
            "SMSMessageText": message_text,
            "Mobiles": mobile,
            "LineNumber": self.line_number,
            "SendDateTime": ""
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        print(f"DEBUG: Sending Custom Message to {mobile}")

        try:
            response = requests.post(self.URL_SIMPLE, data=payload, headers=headers)
            
            print(f"SendSimple Status: {response.status_code}")
            
            if response.status_code == 200:
                return response.text
            
            print(f"SendSimple Failed Response: {response.text}")
            return None

        except Exception as e:
            print(f"SendSimple Error: {str(e)}")
            return None