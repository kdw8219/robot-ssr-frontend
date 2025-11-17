from rest_framework import serializers

class RobotRegisterSerializer(serializers.Serializer):
    robot_id = serializers.CharField(max_length=128)
    robot_secret = serializers.CharField(max_length=256)
    model = serializers.CharField(max_length=64)
    firmware_version = serializers.CharField(max_length=64)
    location = serializers.CharField(max_length=128)