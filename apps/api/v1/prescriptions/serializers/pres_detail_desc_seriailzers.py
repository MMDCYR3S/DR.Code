from rest_framework import serializers
from django.urls import reverse

from apps.prescriptions.models import Prescription
from .all_serializers import PrescriptionCategorySerializer, PrescriptionAliasSerializer

# ======== PRESCRIPTION DESCRIPTION SERIALIZER ======== #
class PrescriptionDescriptionSerializer(serializers.ModelSerializer):
    """
    سریالایزر مخصوص صفحه توضیحات - فقط اطلاعات ضروری
    """
    category_color = serializers.SerializerMethodField()
    back_to_prescription_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = [
            'detailed_description',
            'back_to_prescription_url',
            "category_color",
            'created_at', 'updated_at'
        ]
    
    def get_category_color(self, obj):
        return obj.get_category_color() if obj.category else None
    
    def get_back_to_prescription_url(self, obj):
        """لینک بازگشت به صفحه اصلی نسخه"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(
                reverse('api:v1:prescriptions_api:prescription-detail', 
                       kwargs={'slug': obj.slug})
            )
        return None