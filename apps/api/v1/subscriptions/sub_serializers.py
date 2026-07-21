from rest_framework import serializers
from apps.subscriptions.models import Plan, Feature

class FeatureSimpleSerializer(serializers.ModelSerializer):
    """نمایش لیست ویژگی‌های یک اشتراک"""
    class Meta:
        model = Feature
        fields = ['name', 'description', 'feature_type']


class PlanPublicSerializer(serializers.ModelSerializer):
    """
    Serializer برای نمایش پلن‌ها در صفحات عمومی
    شامل اطلاعات کامل پلن + امکانات اشتراک و برچسب
    """
    membership_name = serializers.CharField(source='membership.title', read_only=True)
    membership_description = serializers.CharField(source='membership.description', read_only=True)
    
    # استفاده از SerializerMethodField برای دریافت ویژگی‌های فعال
    features = serializers.SerializerMethodField()
    
    duration_months = serializers.ReadOnlyField()
    formatted_price = serializers.SerializerMethodField()
    
    # نمایش برچسب (هم عنوان فارسی و هم کلید انگلیسی)
    tag_value = serializers.CharField(source='tag', read_only=True)
    tag_display = serializers.CharField(source='get_tag_display', read_only=True)
    
    purchase_url = serializers.HyperlinkedIdentityField(
        view_name='api:v1:order:purchase-detail',
        lookup_field='id',
        lookup_url_kwarg='plan_id'
    )
    
    class Meta:
        model = Plan
        fields = [
            'id',
            'name', 
            'tag_value',
            'tag_display',
            'membership_name',
            'membership_description',
            'features',
            'duration_days',
            'duration_months',
            'purchase_url',
            'formatted_price',
        ]
    
    def get_formatted_price(self, obj):
        """قیمت را به صورت فرمت شده برگردان (با جداکننده هزارگان)"""
        return f"{obj.price:,} تومان"
        
    def get_features(self, obj):
        """دریافت ویژگی‌های فعال مرتبط با اشتراک این پلن"""
        active_features = obj.membership.features.all() 
        return FeatureSimpleSerializer(active_features, many=True).data
