from rest_framework import serializers
from apps.ordering.models import Order
from apps.prescriptions.models import Prescription


class OrderSearchSerializer(serializers.ModelSerializer):
    """
    سریالایزر جستجوی اوردرها.
    خروجی استانداردشده برای بخش «جستجوی پیشرفته»:
      - aliases: فقط نام‌های جایگزین (به جای نمایش رشته‌ای مدل)
      - category_color: رنگ دسته‌بندی برای نمایش بَج رنگی
      - access_level_display: برچسب فارسی سطح دسترسی (رایگان/ویژه)
      - imp: پیش‌نمایش تشخیص اصلی برای نمایش در کارت نتیجه
    """
    category_name = serializers.StringRelatedField(source="category.title", read_only=True)
    category_color = serializers.CharField(source="category.color_code", read_only=True)
    aliases = serializers.SerializerMethodField()
    access_level_display = serializers.CharField(source="get_access_level_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "name",
            "slug",
            "imp",
            "category_name",
            "category_color",
            "access_level",
            "access_level_display",
            "created_at",
            "aliases",
        ]

    def get_aliases(self, obj):
        # فقط نام‌های جایگزین را برمی‌گرداند (بدون نام اوردر اضافه شده در __str__)
        return list(obj.aliases.values_list("name", flat=True))


class PrescriptionSearchSerializer(serializers.ModelSerializer):
    """
    سریالایزر جستجوی نسخه‌ها.
    هم‌ساختار با OrderSearchSerializer برای نمایش یکپارچه نتایج.
    """
    category_name = serializers.StringRelatedField(source="category.title", read_only=True)
    category_color = serializers.CharField(source="category.color_code", read_only=True)
    aliases = serializers.SerializerMethodField()
    access_level_display = serializers.CharField(source="get_access_level_display", read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "id",
            "title",
            "slug",
            "category_name",
            "category_color",
            "access_level",
            "access_level_display",
            "created_at",
            "aliases",
        ]

    def get_aliases(self, obj):
        # فقط نام‌های جایگزین را برمی‌گرداند
        return list(obj.aliases.values_list("name", flat=True))


class CategorySearchSerializer(serializers.Serializer):
    """
    سریالایزر سبک برای لیست دسته‌بندی‌ها در دراپ‌داون فیلتر پیشرفته.
    """
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    color_code = serializers.CharField(read_only=True)
