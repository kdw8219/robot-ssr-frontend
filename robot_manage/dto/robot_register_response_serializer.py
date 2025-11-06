from rest_framework import serializers

class RobotRegisterResponseSerializer(serializers.Serializer):
    robot_id = serializers.CharField(max_length=128)
    result = serializers.CharField(max_length=256)