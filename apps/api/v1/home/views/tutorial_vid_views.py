from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from apps.home.models import Tutorial
from ..serializers import (
    TutorialSerializer
)

from .base_views import BaseAPIView

# ================= TUTORIAL LIST VIEW ================= #
class TutorialListView(BaseAPIView):
    """
    لیست ویدیوهای آموزشی
    
    GET: دریافت لیست تمام ویدیوها
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    
    def get(self, request, *args, **kwargs):
        """دریافت لیست ویدیوهای آموزشی"""
        try:
            tutorials = Tutorial.objects.all().order_by('-created_at')
            serializer = TutorialSerializer(tutorials, many=True)
            
            response_data = {
                'success': True,
                'count': len(serializer.data),
                'data': serializer.data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return self.handle_exception(e)
