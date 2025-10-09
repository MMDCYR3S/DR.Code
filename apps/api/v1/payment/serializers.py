from rest_framework import serializers
from apps.payment.models import Payment, PaymentGateway

# ====== Payment Create Serializer ====== #
class PaymentCreateSerializer(serializers.Serializer):
    """سریالایزر ایجاد پرداخت"""
    plan_id = serializers.IntegerField(required=True)
    discount_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    gateway = serializers.ChoiceField(
        choices=PaymentGateway.choices,
        required=True,
        help_text="نوع درگاه پرداخت (ZARINPAL یا PAR SPAL)"
    )
    
    def validate_gateway(self, value):
        """اعتبارسنجی درگاه پرداخت"""
        if value not in [PaymentGateway.ZARINPAL, PaymentGateway.PARSPAL]:
            raise serializers.ValidationError("درگاه پرداخت انتخابی معتبر نیست.")
        return value

    
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
