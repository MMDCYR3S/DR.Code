from rest_framework import generics, throttling

from django.db.models import Prefetch

from apps.accounts.permissions import IsTokenJtiActive
from apps.prescriptions.models import Prescription, PrescriptionDrug
from ..serializers import PrescriptionDetailSerializer
from .permissions import IsPrescriptionAccessible

# ========== PRESCRIPTION DETAIL VIEW ========== #
class PrescriptionDetailView(generics.RetrieveAPIView):
    """
    جزئیات کامل یک نسخه
    """
    
    serializer_class = PrescriptionDetailSerializer
    permission_classes = [IsPrescriptionAccessible, IsTokenJtiActive]
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
            Prefetch('prescriptiondrug_set', queryset=PrescriptionDrug.objects.select_related('drug')),
            'images',
            'videos'
        )
