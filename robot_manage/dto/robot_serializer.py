from rest_framework import serializers

class RobotSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=256)
    robot_id = serializers.CharField(max_length=128)
    model = serializers.CharField(max_length=64)
    firmware_version = serializers.CharField(max_length=64)
    location = serializers.CharField(max_length=128)