from django.urls import re_path
from streaming import consumer

websocket_urlpatterns = [
    #path('admin/', admin.site.urls),
    re_path(r"ws/screen/$", consumer.RobotRTCConsumer.as_asgi()),
]