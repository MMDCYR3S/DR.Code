from rest_framework.generics import ListAPIView
from drf_spectacular.views import extend_schema

from apps.home.models import Tutorial
from apps.prescriptions.models import Prescription, AccessChoices
from ..serializers import (
    RecentPrescriptionSerializer,
    RecentTutorialSerializer
)

@extend_schema(tags=["Home"])
class RecentPrescriptionsAPIView(ListAPIView):
    """
    نمایش نسخه های اخیر و لیست کردن 4 تا از آن ها
    """
    
    serializer_class = RecentPrescriptionSerializer
    permission_classes = []
    queryset = Prescription.objects.filter(is_active=True, access_level=AccessChoices.free.value).order_by("-created_at")[:4]
    
class RecentTutorialAPIView(ListAPIView):
    """
    نمایش نسخه های اخیر و لیست کردن 4 تا از آن ها
    """
    
    serializer_class = RecentTutorialSerializer
    permission_classes = []
    queryset = Tutorial.objects.all().order_by("-created_at")[:4]
    