from rest_framework import serializers
from apps.notifications.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای مدل Notification.
    """
    
    recipient_username = serializers.CharField(source='recipient.username', read_only=True)
    created_at_jalali = serializers.CharField(source='shamsi_created_at', read_only=True)
    
    related_object_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'recipient_username',
            'message',
            'is_read',
            'created_at',
            'created_at_jalali',
            'content_type',
            'object_id',
            'related_object_url', 
        ]
        read_only_fields = [
            'id', 
            'recipient', 
            'recipient_username', 
            'message', 
            'created_at', 
            'created_at_jalali', 
            'content_type',
            'object_id',
            'related_object_url'
        ]
    
    def get_related_object_url(self, obj):
        """
        یک URL برای دسترسی به جزئیات آبجکت مرتبط با اعلان برمی‌گرداند.
        این تابع باید بر اساس نوع آبجکت، URL مناسب را بسازد.
        """
        
        if obj.content_object:
            model_name = obj.content_type.model
            if model_name == 'question':
                return f'/api/questions/{obj.object_id}/'
        return None
    