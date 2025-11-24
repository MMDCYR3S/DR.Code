from rest_framework import serializers

class PhoneVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, min_length=4, required=True)
