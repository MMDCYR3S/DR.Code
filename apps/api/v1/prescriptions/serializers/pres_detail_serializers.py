from rest_framework import serializers

from django.urls import reverse

from apps.prescriptions.models import Prescription
from .all_serializers import (
    PrescriptionAliasSerializer,
    PrescriptionCategorySerializer,
    PrescriptionDrugSerializer,
    PrescriptionImageSerializer,
    PrescriptionVideoSerializer,
    DrugSerializer,
)

# ======== PRESCRIPTION DETAIL SERIALIZER ======== #
class PrescriptionDetailSerializer(serializers.ModelSerializer):
    """سریالایزر برای جزئیات کامل نسخه"""
    category = PrescriptionCategorySerializer(read_only=True)
    all_names = serializers.SerializerMethodField()
    prescription_drugs = PrescriptionDrugSerializer(source="prescriptiondrug_set" ,many=True, read_only=True)
    images = PrescriptionImageSerializer(many=True, read_only=True)
    videos = PrescriptionVideoSerializer(many=True, read_only=True)
    primary_name = serializers.SerializerMethodField()
    description_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'title', 'all_names',
            'category', 'prescription_drugs',
            'images', 'videos', 
            'access_level',
            'primary_name', "description_url",
            'created_at',
        ]
    
    def get_description_url(self, obj):
        """ایجاد hyperlink برای جزئیات"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(
                reverse('api:v1:prescriptions_api:prescription-description', kwargs={'slug': obj.slug})
            )
        return None
    
    def get_all_names(self, obj):
        return obj.get_all_names()
    
    def get_primary_name(self, obj):
        return obj.get_primary_name()
    
    def get_category_color(self, obj):
        return obj.get_category_color() if obj.category else None