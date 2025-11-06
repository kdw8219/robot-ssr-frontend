from rest_framework import serializers

class RobotRegisterSerializer(serializers.Serializer):
    robot_id = serializers.CharField(max_length=128)
    model = serializers.CharField(max_length=64)
    firmware = serializers.CharField(max_length=64)
    location = serializers.CharField(max_length=128)