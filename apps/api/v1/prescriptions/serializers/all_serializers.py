from rest_framework import serializers
from apps.prescriptions.models import (
    PrescriptionCategory, PrescriptionDrug, 
    PrescriptionImage, PrescriptionVideo, PrescriptionAlias
)

# ========= PRESCRIPTION ALIAS SERIALIZER ========= #
class PrescriptionAliasSerializer(serializers.ModelSerializer):
    """ سریال سازی نام های متفاوت هر نسخه """
    class Meta:
        model = PrescriptionAlias
        fields = ['name', 'is_primary']

# ========== PRESCRIPTION CATEGORY SERIALIZER ========== #
class PrescriptionCategorySerializer(serializers.ModelSerializer):
    """ سریال سازی دسته بندی ها """
    class Meta:
        model = PrescriptionCategory
        fields = ['id', 'title', 'slug', 'color_code']

# ======= PRESCRIPTION DRUG SERIALIZER ======= #
class PrescriptionDrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionDrug
        fields = [
            'title', 'code', 'dosage', 'amount', 
            'instructions', 'truncated_instructions',
            'is_combination', 'combination_group', 'order'
        ]

# ======= PRESCRIPTION IMAGE SERIALIZER ======== #
class PrescriptionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionImage
        fields = ['image', 'caption']

# ====== PRESCRIPTION VIDEO SERIALIZER ====== #
class PrescriptionVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionVideo
        fields = ['video_url', 'title', 'description']
