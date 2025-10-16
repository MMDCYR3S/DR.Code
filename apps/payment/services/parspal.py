import requests
import logging
import uuid
from typing import Dict, Any, Optional

from django.conf import settings

from apps.payment.models import Payment, PaymentStatus

logger = logging.getLogger(__name__)


class ParspalService:
    """سرویس درگاه پرداخت پارس‌پال"""
    
    def __init__(self):
        self.config = settings.PARSPAL_CONFIG
        self.api_key = self.config.get('API_KEY')
        self.sandbox = self.config.get('SANDBOX', True)
        self.callback_url = self.config.get('PARSPAL_CALLBACK_URL')
        
        # تعیین URL بر اساس محیط (تست یا واقعی)
        if self.sandbox:
            self.base_url = "https://sandbox.api.parspal.com/v1/payment"
        else:
            self.base_url = "https://api.parspal.com/v1/payment"
    
    def _get_headers(self) -> Dict[str, str]:
        """هدرهای مورد نیاز برای درخواست"""
        return {
            'Content-Type': 'application/json',
            'ApiKey': self.api_key
        }
    
    def request_payment(
        self, 
        amount: int, 
        return_url: Optional[str] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        ارسال درخواست پرداخت به پارس‌پال
        
        Args:
            amount: مبلغ به ریال
            return_url: آدرس بازگشت (اختیاری)
            description: توضیحات تراکنش
            
        Returns:
            دیکشنری حاوی پاسخ از سرور
        """
        url = f"{self.base_url}/request"
        
        payload = {
            "amount": amount,
            "return_url": return_url or self.callback_url,
            "order_id": str(uuid.uuid4()),
            "currency": "IRT",
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Payment request successful: {data}")
            
            return {
                'success': True,
                'data': data,
                'status_code': response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500
            }
    
    def verify_payment(self, token: str) -> Dict[str, Any]:
        """
        تایید پرداخت انجام شده
        
        Args:
            token: توکن دریافتی از درگاه
            
        Returns:
            دیکشنری حاوی نتیجه تایید
        """
        url = f"{self.base_url}/verify"
        
        payload = {
            "token": token
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Payment verification successful: {data}")
            
            return {
                'success': True,
                'data': data,
                'status_code': response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment verification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500
            }
    
    def inquiry_payment(self, token: str) -> Dict[str, Any]:
        """
        استعلام وضعیت پرداخت
        
        Args:
            token: توکن تراکنش
            
        Returns:
            دیکشنری حاوی اطلاعات تراکنش
        """
        url = f"{self.base_url}/inquiry"
        
        payload = {
            "token": token
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Payment inquiry successful: {data}")
            
            return {
                'success': True,
                'data': data,
                'status_code': response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment inquiry failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500
            }
    
    def update_payment_status(
        self, 
        payment: Payment, 
        verification_data: Dict[str, Any]
    ) -> Payment:
        """
        بروزرسانی وضعیت پرداخت بر اساس پاسخ تایید
        
        Args:
            payment: شیء پرداخت
            verification_data: داده‌های دریافتی از تایید
            
        Returns:
            شیء پرداخت بروزرسانی شده
        """
        from django.utils import timezone
        
        if verification_data.get('success'):
            data = verification_data.get('data', {})
            
            # بروزرسانی اطلاعات پرداخت
            payment.status = PaymentStatus.COMPLETED
            payment.ref_id = data.get('ref_id') or data.get('transaction_id')
            payment.paid_at = timezone.now()
            
        else:
            payment.status = PaymentStatus.FAILED
        
        payment.save()
        return payment
