from django.urls import path
from streaming import consumer as streaming_consumer
from streaming import control as control_consumer

websocket_urlpatterns = [
    #path('admin/', admin.site.urls),
    path("ws/screen/<robot_id>/", streaming_consumer.RobotRTCConsumer.as_asgi()),
    path("ws/control/<robot_id>/", control_consumer.RobotControlConsumer.as_asgi()),
]