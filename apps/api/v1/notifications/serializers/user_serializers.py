from rest_framework import serializers
from django.urls import reverse

from apps.notifications.models import Notification

class UserNotificationSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای مدل Notification.
    """
    
    recipient_username = serializers.CharField(source='recipient.username', read_only=True)
    created_at_jalali = serializers.CharField(source='shamsi_created_at', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'recipient_username',
            'message',
            'is_read',
            'created_at_jalali',
            'content_type',
            'object_id',
        ]
        read_only_fields = [
            'id', 
            'recipient', 
            'recipient_username', 
            'message', 
            'created_at_jalali', 
            'content_type',
            'object_id',
        ]
                    