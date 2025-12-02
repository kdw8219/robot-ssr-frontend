import json
from channels.generic.websocket import AsyncWebsocketConsumer
import httpx
from utils import httpClient as hc
import os

REDIS_HOST = os.getenv("ROBOT_API_URL", "localhost")

class RobotRTCConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.robot_id = self.scope["url_route"]["kwargs"]["robot_id"]#url에서 id 가져오기
        self.group_name = f"robot_{self.robot_id}"

        # Redis 채널 레이어에 그룹 가입
        # 이러면 channel_name이 여럿 들어가는 구조가 됨
        # 한개 서버만 화면을 공유할 수 있도록 해야 한다.
        await self.channel_layer.group_add(self.group_name, self.channel_name) 
        
        await self.accept()
        
    async def disconnect(self, message):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        
    async def receive(self, data):
        
        payload = json.loads(data)
        req_robot_id = payload['robot_id']
    
        if payload['type'] == 'client_answer':
            await self.forward_payload(payload['type'], req_robot_id, payload['answer'])
        
        elif payload['type'] == 'client_ice':
            await self.forward_payload(payload['type'], req_robot_id, payload['ice'])
        
        elif payload['type'] == 'request_screen':
            await self.request(req_robot_id)
    
    
    async def request(self, req_robot_id):
        try:
            global REDIS_HOST
            await hc.async_client.post(
                f"{REDIS_HOST}/offer-request",
                json={"robot_id": req_robot_id},
                timeout=3
            )
        except Exception as e:
            await self.send(json.dumps({
                "type": "webrtc_error",
                "error": str(e),
            }))
        
    async def forward_payload(self, msg_type, req_robot_id, payload):
        try:
            global REDIS_HOST
            await hc.async_client.post(
                f"{REDIS_HOST}/signaling",
                json={
                    "type": msg_type,
                    "robot_id": req_robot_id,
                    "payload": payload
                },
                timeout=3
            )
        except Exception as e:
            await self.send(json.dumps({
                "type": "webrtc_error",
                "error": str(e)
            }))