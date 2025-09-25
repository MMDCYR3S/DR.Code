from rest_framework import generics, permissions
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.filters import OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Prefetch

from apps.prescriptions.models import Prescription, PrescriptionCategory,Drug, AccessChoices
from ..serializers import PrescriptionListSerializer
from .filters import PrescriptionFilter
from .pagination import PrescriptionPagination

# ========= PRESCRIPTION LIST VIEW ========== #
class PrescriptionListView(generics.ListAPIView):
    """
    لیست نسخه‌ها با قابلیت جستجو، فیلتر و صفحه‌بندی
    """
    
    serializer_class = PrescriptionListSerializer
    filterset_class = PrescriptionFilter
    pagination_class = PrescriptionPagination
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
            """کوئری بهینه‌سازی شده"""
            queryset = Prescription.objects.filter(
                is_active=True
            ).select_related(
                'category'
            ).prefetch_related(
                'aliases'
            ).distinct()

            if not self.request.user.is_authenticated:
                queryset = queryset.all()

            return queryset

    def list(self, request, *args, **kwargs):
        """Override برای اضافه کردن اطلاعات فیلتر"""
        response = super().list(request, *args, **kwargs)
        
        # اضافه کردن اطلاعات فیلتر
        response.data['filters'] = self.get_filter_options()
        return response

    def get_filter_options(self):
        """دریافت گزینه‌های فیلتر برای فرانت‌اند"""
        categories = PrescriptionCategory.objects.all().values(
            'id', 'title', 'slug', 'color_code'
        )
        
        access_levels = [
            {'value': 'FREE', 'label': 'رایگان'},
            {'value': 'PREMIUM', 'label': 'ویژه'},
        ]

        return {
            'categories': list(categories),
            'access_levels': access_levels,
        }
        
        
