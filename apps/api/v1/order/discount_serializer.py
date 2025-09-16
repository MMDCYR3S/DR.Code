# api/v1/marketing/serializers.py
from rest_framework import serializers
from apps.accounts.models import User
from apps.order.models import DiscountCode
from apps.subscriptions.models import Plan

# ========= PURCHASE DETAIL SERIALIZER ========= #
class PurchaseDetailSerializer(serializers.Serializer):
    """Serializer برای نمایش جزئیات خرید"""
    
    # اطلاعات پلن
    plan_id = serializers.IntegerField()
    plan_name = serializers.CharField(read_only=True)
    plan_duration_days = serializers.IntegerField(read_only=True)
    membership_name = serializers.CharField(read_only=True)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    
    # کدهای تخفیف
    discount_code = serializers.CharField(
        max_length=20, 
        required=False, 
        allow_blank=True,
        help_text="کد تخفیف (اختیاری)"
    )
    referral_code = serializers.CharField(
        max_length=20, 
        required=False, 
        allow_blank=True,
        help_text="کد معرف (اختیاری)"
    )
    
    # محاسبات قیمت
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    discount_percent = serializers.IntegerField(read_only=True, default=0)
    
    # اطلاعات اضافی
    savings = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    is_discounted = serializers.BooleanField(read_only=True)

    def validate_discount_code(self, value):
        """اعتبارسنجی کد تخفیف"""
        if not value:
            return value
            
        try:
            discount = DiscountCode.objects.get(code=value.upper())
            if not discount.is_usable:
                raise serializers.ValidationError("کد تخفیف معتبر نیست یا منقضی شده است.")
            return value.upper()
        except DiscountCode.DoesNotExist:
            raise serializers.ValidationError("کد تخفیف وارد شده معتبر نیست.")

    def validate_referral_code(self, value):
        """اعتبارسنجی کد معرف"""
        if not value:
            return value
            
        try:
            # بررسی وجود کاربر با این کد معرف
            referrer = User.objects.get(profile__referral_code=value.upper())
            
            # بررسی اینکه کاربر خودش را معرفی نکند
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                if referrer.id == request.user.id:
                    raise serializers.ValidationError("نمی‌توانید کد معرف خودتان را استفاده کنید.")
            
            return value.upper()
        except User.DoesNotExist:
            raise serializers.ValidationError("کد معرف وارد شده معتبر نیست.")

    def validate(self, attrs):
        """اعتبارسنجی کلی"""
        plan_id = attrs.get('plan_id')
        
        try:
            plan = Plan.objects.select_related('membership').get(
                id=plan_id, 
                is_active=True
            )
        except Plan.DoesNotExist:
            raise serializers.ValidationError({"plan_id": "پلن انتخابی معتبر نیست."})
        
        # محاسبه قیمت‌ها
        original_price = plan.price
        discount_amount = 0
        discount_percent = 0
        
        # اعمال تخفیف کد تخفیف
        discount_code = attrs.get('discount_code')
        if discount_code:
            try:
                discount = DiscountCode.objects.get(code=discount_code)
                if discount.is_usable:
                    discount_percent = discount.discount_percent
                    discount_amount = (original_price * discount_percent) / 100
            except DiscountCode.DoesNotExist:
                pass
        
        # محاسبه قیمت نهایی
        final_price = max(0, original_price - discount_amount)
        
        # اضافه کردن اطلاعات محاسبه شده
        attrs.update({
            'plan_name': plan.name,
            'plan_duration_days': plan.duration_days,
            'membership_name': plan.membership.title,
            'original_price': original_price,
            'discount_amount': discount_amount,
            'discount_percent': discount_percent,
            'final_price': final_price,
            'savings': discount_amount,
            'is_discounted': discount_amount > 0
        })
        
        return attrs

# ========== PURCHASE SUMMARY SERIALIZER ========== #
class PurchaseSummarySerializer(serializers.Serializer):
    """Serializer برای خلاصه خرید"""
    
    plan_info = serializers.SerializerMethodField()
    pricing_info = serializers.SerializerMethodField()
    discount_info = serializers.SerializerMethodField()
    
    def get_plan_info(self, obj):
        """اطلاعات پلن"""
        return {
            'name': obj.get('plan_name'),
            'duration_days': obj.get('plan_duration_days'),
            'membership': obj.get('membership_name'),
            'duration_text': self._get_duration_text(obj.get('plan_duration_days'))
        }
    
    def get_pricing_info(self, obj):
        """اطلاعات قیمت‌گذاری"""
        return {
            'original_price': obj.get('original_price'),
            'final_price': obj.get('final_price'),
            'savings': obj.get('savings'),
            'formatted_original_price': f"{obj.get('original_price'):,} تومان",
            'formatted_final_price': f"{obj.get('final_price'):,} تومان",
            'formatted_savings': f"{obj.get('savings'):,} تومان"
        }
    
    def get_discount_info(self, obj):
        """اطلاعات تخفیف"""
        return {
            'is_discounted': obj.get('is_discounted', False),
            'discount_percent': obj.get('discount_percent', 0),
            'discount_code': obj.get('discount_code', ''),
            'referral_code': obj.get('referral_code', ''),
            'discount_text': f"{obj.get('discount_percent', 0)}% تخفیف" if obj.get('discount_percent') else None
        }
    
    def _get_duration_text(self, days):
        """تبدیل روز به متن فارسی"""
        if days == 30:
            return "یک ماهه"
        elif days == 90:
            return "سه ماهه"
        elif days == 180:
            return "شش ماهه"
        elif days == 365:
            return "یک ساله"
        else:
            return f"{days} روزه"
