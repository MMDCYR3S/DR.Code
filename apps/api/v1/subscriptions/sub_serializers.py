from rest_framework import serializers

from apps.subscriptions.models import Plan, Membership

# ============== PLAN PUBLIC SERIALIZER ================ #
class PlanPublicSerializer(serializers.ModelSerializer):
    """
    Serializer برای نمایش پلن‌ها در صفحات عمومی
    شامل اطلاعات پلن + نام اشتراک مربوطه
    """
    membership_name = serializers.CharField(source='membership.title', read_only=True)
    duration_months = serializers.ReadOnlyField()
    formatted_price = serializers.SerializerMethodField()
    
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
            'membership_name',
            'duration_days',
            'duration_months',
            'purchase_url',
            'formatted_price',
        ]
    
    def get_formatted_price(self, obj):
        """قیمت را به صورت فرمت شده برگردان (با جداکننده هزارگان)"""
        return f"{obj.price:,} تومان"