from django.shortcuts import render, redirect
from django.http import HttpResponse
from auth_service_handler.decorator import jwt_required
from dotenv import load_dotenv
import os
import httpx
from robot_manage.dto.robot_register_serializer import RobotRegisterSerializer
from robot_manage.dto.robot_register_response_serializer import RobotRegisterResponseSerializer
import django.contrib.messages as messages
import logging
from asgiref.sync import sync_to_async
import json

logger = logging.getLogger('user_manage')

def HTMLRenderer(request, template_name='user_manage/index.html', params={}):
    return render(request, template_name, params)

@jwt_required
async def signup(request):
    logger.info('which method we got? : ' + request.method)
    if request.method == 'GET':
        logger.info('start get method handling...')
        res = HTMLRenderer(request, 'robot_manage/robot_manage.html', params={})
        return await sync_to_async(HttpResponse)( res )
    
    elif request.method == 'POST':
        load_dotenv()
        robot_service_url = os.getenv('ROBOT_SERVICE_URL')
        parsed_data = None
        try:
            parsed_data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            messages.error(request, "요청 정보 확인이 필요합니다.")
            return redirect('/error/')
            
        serializer = RobotRegisterSerializer(data=parsed_data)
        print(parsed_data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        
        try:
            async with httpx.AsyncClient() as client:
                api_response = await client.post(robot_service_url, json=payload)
                print(api_response.json())
                api_response.raise_for_status()
                deserializer = RobotRegisterResponseSerializer(data=api_response.json())
                if not deserializer.is_valid():
                    raise ValueError("Invalid value!")
                
                #log 등록
                print(deserializer.validated_data.get('result'))
                
                return await sync_to_async(redirect)("/robot/management/")
                
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 409:
                messages.error(request, "이미 등록된 로봇입니다.")
            else:
                messages.error(request, "로봇 등록 중 오류가 발생했습니다. 다시 시도해주세요.")
                
            return await sync_to_async(redirect)("/robot/management/")  # 다시 로봇 등록 페이지로 
        except ValueError as e:
            print('response format is invalid') #추후 로그로 변경
            return await sync_to_async(redirect)("/error/")
        