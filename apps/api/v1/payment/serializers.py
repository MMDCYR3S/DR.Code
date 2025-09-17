from rest_framework import serializers
from apps.payment.models import Payment

# ====== Payment Create Serializer ====== #
class PaymentCreateSerializer(serializers.Serializer):
    """ سریال سازی شناسه مشترک و همچنین کد تخفیف برای درگاه پرداخت """
    plan_id = serializers.IntegerField(required=True)
    # subscription_id = serializers.IntegerField(required=True)
    discount_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
# ====== Payment Serializer ====== #
class PaymentSerializer(serializers.ModelSerializer):
    """ سریال سازی اطلاعات مربوط به درگاه پرداخت """
    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'discount_amount', 'final_amount',
            'status', 'authority', 'ref_id', 'created_at', 'paid_at'
        ]
        read_only_fields = ['id', 'authority', 'ref_id', 'created_at', 'paid_at']
