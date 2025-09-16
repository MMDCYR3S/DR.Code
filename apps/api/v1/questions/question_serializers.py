from rest_framework import serializers
from django.utils import timezone

from apps.questions.models import Question


# ======== QUESTION CREATE SERIALIZER ======== #
class QuestionCreateSerializer(serializers.ModelSerializer):
    """Serializer برای ایجاد سوال جدید"""
    
    class Meta:
        model = Question
        fields = ['prescription', 'question_text']
    
    def validate_question_text(self, value):
        """اعتبارسنجی متن سوال"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("سوال باید حداقل ۱۰ کاراکتر باشد.")
        
        if len(value) > 1000:
            raise serializers.ValidationError("سوال نمی‌تواند بیشتر از ۱۰۰۰ کاراکتر باشد.")
        
        return value.strip()
    
    def validate(self, attrs):
        """اعتبارسنجی کلی"""
        user = self.context['request'].user
        
        # بررسی اشتراک فعال
        if not user.has_active_membership():
            raise serializers.ValidationError(
                "برای پرسیدن سوال باید اشتراک ویژه داشته باشید."
            )
        
        # بررسی محدودیت تعداد سوال در روز (مثلاً 5 سوال در روز)
        today_questions_count = Question.objects.filter(
            user=user,
            created_at__date=timezone.now().date()
        ).count()
        
        if today_questions_count >= 5:
            raise serializers.ValidationError(
                "حداکثر ۵ سوال در روز می‌توانید بپرسید."
            )
        
        return attrs
