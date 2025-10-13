from rest_framework import serializers
from apps.home.models import Tutorial

# =========== TUTORIAL LIST SERIALIZER =========== #
class TutorialSerializer(serializers.ModelSerializer):
    """
    Serializer برای ویدیوهای آموزشی
    """
    
    class Meta:
        model = Tutorial
        fields = [
            'id', 
            'title', 
            'aparat_url',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']