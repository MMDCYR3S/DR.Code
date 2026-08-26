from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.ordering.models import Order
from apps.prescriptions.models import Prescription
from ..serializers import OrderSearchSerializer, PrescriptionSearchSerializer


@extend_schema_view(
    get=extend_schema(
        tags=['Search'],
        summary='جستجو در اوردرها و نسخه‌ها',
        parameters=[
            OpenApiParameter(name='q', description='عبارت جستجو', required=True, type=str)
        ]
    )
)
class SearchAPIView(APIView):
    permission_classes = []
    
    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response(
                {"detail": "پارامتر q الزامی است."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # جستجو در اوردرها
        orders = Order.objects.filter(
            is_active=True
        ).filter(
            Q(name__icontains=q) |
            Q(slug__icontains=q) |
            Q(aliases__name__icontains=q)
        ).distinct().order_by('-created_at')
        
        # جستجو در نسخه‌ها
        prescriptions = Prescription.objects.filter(
            is_active=True
        ).filter(
            Q(title__icontains=q) |
            Q(slug__icontains=q) |
            Q(aliases__name__icontains=q) 
        ).distinct().order_by('-created_at')
        
        order_serializer = OrderSearchSerializer(orders, many=True)
        prescription_serializer = PrescriptionSearchSerializer(prescriptions, many=True)
        
        return Response({
            "orders": order_serializer.data,
            "prescriptions": prescription_serializer.data,
        })