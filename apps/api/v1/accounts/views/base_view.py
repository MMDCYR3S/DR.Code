from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging

logger = logging.getLogger(__name__)

# =========== Base API VIEW =========== #
class BaseAPIView(APIView):
    """Base class برای ویوهای مشترک"""
    
    def get_client_ip(self, request):
        """دریافت IP کلاینت"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_user_agent(self, request):
        """دریافت اطلاعات دستگاه کاربر"""
        return request.META.get('HTTP_USER_AGENT', 'Unknown Device')[:255]

    def handle_exception(self, exc):
        """مدیریت خطاهای کلی"""
        logger.error(f"خطای غیرمنتظره: {str(exc)}")
        return Response({
            'success': False,
            'message': f'{str(exc)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)