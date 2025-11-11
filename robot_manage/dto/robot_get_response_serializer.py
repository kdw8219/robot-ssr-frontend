from rest_framework import serializers
from .robot_serializer import RobotSerializer

def validation_checker(value):
    if value < 0:
        raise serializers.ValidationError('Not a positive value')

class RobotGetResponseSerializer(serializers.Serializer):
    robots = RobotSerializer(many=True)
    current_totalCount = serializers.IntegerField(validators=[validation_checker])
    totalCount = serializers.IntegerField(validators=[validation_checker])
    result = serializers.CharField(max_length=256)