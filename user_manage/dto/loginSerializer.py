from rest_framework import serializers


class BigIntCharField(serializers.CharField):
    def to_integernal_value(self,data):
        
        value = super().to_internal_value(data)
        try:
            return int(value)
        except ValueError:
            raise serializers.ValidationError("It's not numeric type ")

class LoginSerializer(serializers.Serializer):
    id = BigIntCharField()
    userId = serializers.CharField(max_length=150)
    role = serializers.CharField(max_length=32)
    access_token = serializers.CharField(max_length=512)
    refresh_token = serializers.CharField(max_length=512)
