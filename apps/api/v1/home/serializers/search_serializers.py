from rest_framework import serializers
from apps.ordering.models import Order
from apps.prescriptions.models import Prescription

class OrderSearchSerializer(serializers.ModelSerializer):
    category_name = serializers.StringRelatedField(source="category.title", read_only=True)
    aliases = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "name", "slug", "category_name", "access_level", "created_at", "aliases"]


class PrescriptionSearchSerializer(serializers.ModelSerializer):
    category_name = serializers.StringRelatedField(source="category.title", read_only=True)
    aliases = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Prescription
        fields = ["id", "title", "slug", "category_name", "access_level", "created_at", "aliases"]