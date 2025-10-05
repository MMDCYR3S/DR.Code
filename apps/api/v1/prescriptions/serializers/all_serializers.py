from rest_framework import serializers
from apps.prescriptions.models import (
    PrescriptionCategory, Drug, PrescriptionDrug,
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
class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = [
            'title', 'code', 
        ]

class PrescriptionDrugSerializer(serializers.ModelSerializer):
    drug = DrugSerializer(read_only=True)
    
    class Meta:
        model = PrescriptionDrug
        fields = [
            "drug", "dosage",
            "instructions", "amount", "is_combination",
            "order", "group_number"
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
