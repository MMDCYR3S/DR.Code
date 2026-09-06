from rest_framework import serializers

from apps.prescriptions.models import Prescription
from apps.ordering.models import Order
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

# ========== RECENT ORDER SERIALIZER ========== #
class RecentOrderSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای نمایش اوردرهای رایگان اخیر در صفحه اصلی
    """

    category_name = serializers.StringRelatedField(source='category.title', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    primary_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'name',
            'slug',
            'imp',
            'category_name',
            'category_color',
            'access_level',
            'created_at',
            'primary_name',
        ]

    def get_primary_name(self, obj):
        """برگرداندن نام اصلی (primary alias) در صورت وجود"""
        return obj.get_primary_name()