from rest_framework import serializers

class RobotDelResponseSerializer(serializers.Serializer):
    result = serializers.CharField(max_length=256)