from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from drf_spectacular.views import extend_schema

from .question_serializers import QuestionCreateSerializer
from apps.accounts.permissions import HasActiveSubscription

from drf_spectacular.utils import extend_schema

# ======== QUESTION CREATE VIEW ========= #
@extend_schema(tags=['Questions'])
class QuestionCreateView(generics.CreateAPIView):
    """
    ایجاد سوال جدید - فقط کاربران با اشتراک فعال
    """
    serializer_class = QuestionCreateSerializer
    permission_classes = [permissions.IsAuthenticated, HasActiveSubscription]
    throttle_classes = [UserRateThrottle]
    
    def perform_create(self, serializer):
        """ثبت سوال با کاربر فعلی"""
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """ایجاد سوال با پیام موفقیت"""
        response = super().create(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_201_CREATED:
            return Response({
                'success': True,
                'data': response.data,
                'message': 'سوال شما با موفقیت ثبت شد و به زودی پاسخ داده خواهد شد.'
            }, status=status.HTTP_201_CREATED)