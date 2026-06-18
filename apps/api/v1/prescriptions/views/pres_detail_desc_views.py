from rest_framework import generics, permissions
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.prescriptions.models import Prescription
from ..serializers import PrescriptionDescriptionSerializer
from .permissions import IsPrescriptionAccessible

# ========= PRESCRIPTION DESCRIPTION VIEW ========== #
@extend_schema_view(
    get=extend_schema(tags=['Prescriptions'], summary='نسخه‌های پزشکی'),
    post=extend_schema(tags=["Prescriptions"]),
)
class PrescriptionDescriptionView(generics.RetrieveAPIView):
    """
    View جداگانه برای نمایش توضیحات کامل (detailed_description) نسخه
    مسیر: api/v1/prescriptions/<slug>/description/
    """
    serializer_class = PrescriptionDescriptionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsPrescriptionAccessible]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """کوئری بهینه‌سازی شده"""
        return Prescription.objects.filter(
            is_active=True
        ).select_related(
            'category'
        ).prefetch_related(
            'aliases'
        )