from rest_framework import serializers
from django.urls import reverse
from django.utils.html import format_html
from apps.prescriptions.models import Prescription

from .all_serializers import PrescriptionAliasSerializer, PrescriptionCategorySerializer

# ========== PRESCRIPTION LIST SERIALIZER ========== #
class PrescriptionListSerializer(serializers.ModelSerializer):
    """سریالایزر برای لیست نسخه‌ها - اطلاعات محدود"""
    category = PrescriptionCategorySerializer(read_only=True)
    aliases = PrescriptionAliasSerializer(many=True, read_only=True)
    detail_url = serializers.SerializerMethodField()
    
    all_names = serializers.SerializerMethodField()
    primary_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'title', 'slug', 'category', 'aliases', 
            'all_names', 'primary_name', 'access_level',
            'detail_url', 'created_at', 'updated_at'
        ]
    
    def get_detail_url(self, obj):
        """ایجاد hyperlink برای جزئیات"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(
                reverse('api:v1:prescriptions_api:prescription-detail', kwargs={'slug': obj.slug})
            )
        return None
    
    def get_all_names(self, obj):
        """تمام نام‌های نسخه"""
        return obj.get_all_names()
    
    def get_primary_name(self, obj):
        """نام اصلی نسخه"""
        return obj.get_primary_name()