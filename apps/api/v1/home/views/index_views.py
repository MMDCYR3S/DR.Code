from rest_framework.generics import ListAPIView
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.home.models import Tutorial
from apps.prescriptions.models import Prescription, AccessChoices
from ..serializers import (
    RecentPrescriptionSerializer,
    RecentTutorialSerializer
)

# ========= RECENT PRESCRIPTIONS VIEW  ========= #
@extend_schema_view(
    get=extend_schema(tags=['Home'], summary='نمایش ۴ نسخه اخیر (رایگان)')
)
class RecentPrescriptionsAPIView(ListAPIView):
    """
    نمایش نسخه های اخیر و لیست کردن 4 تا از آن ها
    """
    
    serializer_class = RecentPrescriptionSerializer
    permission_classes = []
    queryset = Prescription.objects.filter(is_active=True, access_level=AccessChoices.free.value).order_by("-created_at")[:4]

# ========= RECENT TUTORIAL VIEW  ========= #
@extend_schema_view(
    get=extend_schema(tags=['Home'], summary='نمایش ۴ آموزش اخیر')
)    
class RecentTutorialAPIView(ListAPIView):
    """
    نمایش نسخه های اخیر و لیست کردن 4 تا از آن ها
    """
    
    serializer_class = RecentTutorialSerializer
    permission_classes = []
    queryset = Tutorial.objects.all().order_by("-created_at")[:4]
    