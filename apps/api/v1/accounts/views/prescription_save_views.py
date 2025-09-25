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
        دریافت نسخه مورد نظر و کاربری که میخواد اون رو سیو کنه.
        بعد از اینکه شناسه نسخه پیدا شد، وقتی که کاربر روی دکمه سیو کلیک کرد،
        به صورت خودکار، خاصیت is_save که در اکانت کاربر تعبیه شده، به حالت True
        در میاد.
        """
        prescription = get_object_or_404(Prescription, slug=slug)
        user = request.user
        
        is_saved = user.saved_prescriptions.filter(pk=prescription.pk).exists()
        
        if is_saved:
            user.saved_prescriptions.remove(prescription)
            
            return Response(
                {"detail": "نسخه با موفقیت از حالت ذخیره‌شده خارج شد.", "saved": False},
                status=status.HTTP_200_OK
            )
            
        else:
            user.saved_prescriptions.add(prescription)
            
            return Response(
                {"detail": "نسخه با موفقیت ذخیره شد.", "saved": True},
                status=status.HTTP_201_CREATED # استفاده از 201 برای عملیات ایجاد
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
