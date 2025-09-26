from rest_framework.generics import ListAPIView

from apps.home.models import Tutorial
from apps.prescriptions.models import Prescription
from ..serializers import (
    RecentPrescriptionSerializer,
    RecentTutorialSerializer
)

class RecentPrescriptionsAPIView(ListAPIView):
    """
    نمایش نسخه های اخیر و لیست کردن 4 تا از آن ها
    """
    
    serializer_class = RecentPrescriptionSerializer
    permission_classes = []
    queryset = Prescription.objects.filter(is_active=True).order_by("-created_at")[:4]
    
class RecentTutorialAPIView(ListAPIView):
    """
    نمایش نسخه های اخیر و لیست کردن 4 تا از آن ها
    """
    
    serializer_class = RecentTutorialSerializer
    permission_classes = []
    queryset = Tutorial.objects.all().order_by("-created_at")[:4]
    