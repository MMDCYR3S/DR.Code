from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status, throttling
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from django.shortcuts import get_object_or_404

from apps.prescriptions.models import Prescription
from ..serializers import SavedPrescriptionListSerializer
from ...prescriptions.views.pagination import PrescriptionPagination

# ============= PRESCRIPTION SAVE/UNSAVE VIEW ============= #
class PrescriptionSaveToggleView(APIView):
    """
    برای ذخیره (Bookmark) کردن یا حذف ذخیره‌سازی یک نسخه توسط کاربر لاگین شده.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug):
        """
        نسخه را بر اساس اسلاگ پیدا کرده و وضعیت ذخیره آن را برای کاربر فعلی تغییر می‌دهد (toggle).
        """
        prescription = get_object_or_404(Prescription, slug=slug)
        user = request.user
        slug = request.data.get('slug')
        is_saved = user.saved_prescriptions.filter(pk=prescription.pk).exists()
        
        if is_saved:
            user.saved_prescriptions.remove(prescription)
            message = "نسخه با موفقیت از لیست حذف شد."
            new_saved_status = False
            response_status = status.HTTP_200_OK
            
        else:
            user.saved_prescriptions.add(prescription)
            message = "نسخه با موفقیت ذخیره شد."
            new_saved_status = True
            response_status = status.HTTP_201_CREATED

        return Response(
            {
                "detail": message,
                "is_saved": new_saved_status 
            },
            status=response_status
        )
            
# ============= SAVED PRESCRIPTION LIST VIEW ============= #
class SavedPrescriptionListView(ListAPIView):
    """
    نمایش لیست نسخه‌های ذخیره‌شده (Bookmarked) توسط کاربر فعلی.
    قابلیت جستجو بر اساس عنوان نسخه را دارد.
    """
    serializer_class = SavedPrescriptionListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PrescriptionPagination
    filter_backends = [SearchFilter]
    throttle_classes = [throttling.UserRateThrottle]
    
    search_fields = ['title']
    
    def get_queryset(self):
        """
        فقط نسخه‌هایی را برمی‌گرداند که توسط کاربر لاگین شده ذخیره شده‌اند
        و فعال (is_active=True) هستند.
        """
        user = self.request.user
        queryset = user.saved_prescriptions.filter(is_active=True).select_related('category').order_by('-created_at')
        
        return queryset
