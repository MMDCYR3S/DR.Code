# payments/management/commands/test_zarinpal_simple.py
from django.core.management.base import BaseCommand
from apps.payment.services import ZarinpalService
import json

class Command(BaseCommand):
    help = 'Simple Zarinpal connection test'

    def handle(self, *args, **options):
        service = ZarinpalService()
        
        self.stdout.write("🚀 Testing Zarinpal Connection...")
        
        # تست درخواست
        result = service.create_payment_request(
            amount=1000,
            description='تست ساده اتصال',
            callback_url='http://127.0.0.1:8000/test/'
        )
        
        if result['success']:
            authority = result['authority']
            self.stdout.write(
                self.style.SUCCESS(f'✅ SUCCESS! Authority: {authority}')
            )
            
            # تست تایید با همان authority
            verify_result = service.verify_payment(authority, 1000)
            
            if verify_result['success']:
                self.stdout.write(
                    self.style.SUCCESS('✅ Verify API also works!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Verify returned: {verify_result["error"]}')
                )
                self.stdout.write(
                    self.style.HTTP_INFO('💡 This is normal - payment not actually made')
                )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ FAILED: {result["error"]}')
            )
