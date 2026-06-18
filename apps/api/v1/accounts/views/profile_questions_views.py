from rest_framework.generics import ListAPIView
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.accounts.permissions import IsTokenJtiActive, HasActiveSubscription
from apps.questions.models import Question
from ..serializers import QuestionListSerializer

# ========= Question List API View ========= #
@extend_schema_view(
    get=extend_schema(tags=['Profile'], summary='دریافت لیست سوالات پرسیده‌شده توسط کاربر')
)
class QuestionListAPIView(ListAPIView):
    """ نمایش لیست سوالاتی که کاربر پرسیده است. """
    
    serializer_class = QuestionListSerializer
    permission_classes = [IsAuthenticated, IsTokenJtiActive, HasActiveSubscription]
    throttle_classes = [UserRateThrottle]
    
    def get_queryset(self):
        queryset = Question.objects.select_related('prescription', 'user', "answered_by").filter(user=self.request.user)
        return queryset
