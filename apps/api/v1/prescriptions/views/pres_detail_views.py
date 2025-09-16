from rest_framework import generics, permissions, throttling

from apps.prescriptions.models import Prescription
from ..serializers import PrescriptionDetailSerializer
from .permissions import IsPrescriptionAccessible

# ========== PRESCRIPTION DETAIL VIEW ========== #
class PrescriptionDetailView(generics.RetrieveAPIView):
    """
    جزئیات کامل یک نسخه
    """
    
    serializer_class = PrescriptionDetailSerializer
    permission_classes = [IsPrescriptionAccessible]
    throttle_classes = [throttling.AnonRateThrottle, throttling.UserRateThrottle]
    lookup_field = 'slug'

    def get_queryset(self):
        """کوئری بهینه‌سازی شده برای جزئیات"""
        return Prescription.objects.filter(
            is_active=True
        ).select_related(
            'category'
        ).prefetch_related(
            'aliases',
            'drugs',
            'images',
            'videos'
        )
