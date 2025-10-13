from rest_framework import serializers

from apps.prescriptions.models import Prescription
from apps.home.models import Tutorial

# ========== RECENT PRESCRIPTION SERIALIZER ========== #
class RecentPrescriptionSerializer(serializers.ModelSerializer):
    """ سریالایزر برای نمایش نسخه های اخیر """

    category_name = serializers.StringRelatedField(source="category.title", read_only=True)

    class Meta:
        model = Prescription
        fields = ["title", "slug", "category_name", "access_level", "created_at"]

# ========== RECENT TUTORIAL SERIALIZER ========== #
class RecentTutorialSerializer(serializers.ModelSerializer):
    """ سریالایزر برای نمایش آموزش های اخیر """
    
    class Meta:
        model = Tutorial
        fields = ["title", "aparat_url", "created_at"]