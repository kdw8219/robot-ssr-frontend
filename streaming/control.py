import json
from channels.generic.websocket import AsyncWebsocketConsumer
from utils import httpClient as hc
import os
import logging

logger = logging.getLogger('streaming')
ROBOT_HOST = os.getenv("ROBOT_API_URL", "localhost")

class RobotControlConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.robot_id = self.scope["url_route"]["kwargs"]["robot_id"]#url에서 id 가져오기
        self.group_name = f"robot_{self.robot_id}"

        # Redis 채널 레이어에 그룹 가입
        # 이러면 channel_name이 여럿 들어가는 구조가 됨
        # 한개 서버만 화면을 공유할 수 있도록 해야 한다.
        
        logger.info(f'insert Control WebSocket...{self.robot_id} / {self.group_name}')
        
        await self.channel_layer.group_add(self.group_name, self.channel_name) 
        
        await self.accept()
        
    async def disconnect(self, message):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        
    async def receive(self, text_data=None, bytes_data=None):
        
        data = None
        
        if text_data != None:
            data = text_data
        else:
            data = bytes_data
        
        payload = json.loads(data)
        req_robot_id = self.robot_id
        
        '''
        move
        stop
        e_stop
        set_speed
        dock
        path_follow
        '''
        try:
            if payload['type'] == 'move':
                await self.forward_command(payload['type'], req_robot_id, payload)
            
            elif payload['type'] == 'stop':
                await self.forward_command(payload['type'], req_robot_id, payload)
            
            elif payload['type'] == 'e_stop':
                await self.forward_command(payload['type'], req_robot_id, payload)
                
            elif payload['type'] == 'set_speed':
                await self.forward_command(payload['type'], req_robot_id, payload)    
                
            elif payload['type'] == 'dock':
                await self.forward_command(payload['type'], req_robot_id, payload)
            
            elif payload['type'] == 'path_follow':
                await self.forward_command(payload['type'], req_robot_id, payload)
            else:
                raise Exception('Unsupported Command')
            
        except Exception as e:
            await self.send(json.dumps({
                "type": "webrtc_error",
                "error": str(e)
            }))
        
    
    async def forward_command(self, msg_type, req_robot_id, payload = None):
        try:
            global ROBOT_HOST
            await hc.async_client.post(
                f"{ROBOT_HOST}control",
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