from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from auth_service_handler.decorator import jwt_required
from dotenv import load_dotenv
import os
import httpx
import logging
import json
import django.contrib.messages as messages
from asgiref.sync import sync_to_async
from robot_manage.dto.robot_register_serializer import RobotRegisterSerializer
from robot_manage.dto.robot_register_response_serializer import RobotRegisterResponseSerializer as RobotNormalResponseSerializer
from robot_manage.dto.robot_get_response_serializer import RobotGetResponseSerializer
from robot_manage.dto.robot_del_response_serializer import RobotDelResponseSerializer
from robot_manage.dto.robot_patch_serializer import RobotPatchSerializer
from django.views.decorators.csrf import csrf_exempt


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
        logger.info('work here?')
        load_dotenv()
        robot_service_url = os.getenv('ROBOT_SERVICE_URL')
        parsed_data = None
        try:
            parsed_data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            messages.error(request, "요청 정보 확인이 필요합니다.")
            return redirect('/error/')
            
        serializer = RobotRegisterSerializer(data=parsed_data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        
        try:
            async with httpx.AsyncClient() as client:
                api_response = await client.post(robot_service_url, json=payload)
                print(api_response.json())
                api_response.raise_for_status()
                deserializer = RobotNormalResponseSerializer(data=api_response.json())
                if not deserializer.is_valid():
                    raise ValueError("Invalid value!")
                
                #log 등록
                print(deserializer.validated_data.get('result'))
                
                return await sync_to_async(redirect)("/robots/management/")
                
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 409:
                messages.error(request, "이미 등록된 로봇입니다.")
            else:
                messages.error(request, "로봇 등록 중 오류가 발생했습니다. 다시 시도해주세요.")
                
            return await sync_to_async(redirect)("/robots/management/")  # 다시 로봇 등록 페이지로 
        except ValueError as e:
            print('response format is invalid') #추후 로그로 변경
            return await sync_to_async(redirect)("/error/")
    else:
        logger.info(f'invalid request...:{request.method}')

@jwt_required
async def handling_robots(request):
    if request.method == 'GET':
        page = request.GET.get('page', 1)        # 기본값 1
        page_per = request.GET.get('per_page', 20) # 기본값 20
        
        params = {
            'page': int(page),
            'page_per': int(page_per)
        }
        
        try:
            async with httpx.AsyncClient() as client:
                load_dotenv()
                robot_service_url = os.getenv('ROBOT_SERVICE_URL')
                api_response = await client.get(robot_service_url, params = params)
                api_response.raise_for_status()
                deserializer = RobotGetResponseSerializer(data=api_response.json())
                if not deserializer.is_valid():
                    raise ValueError("Invalid value!")
                
                #log 등록
                logger.info('get result : '+deserializer.validated_data.get('result'))
                
                start = (int(page) - 1) * int(page_per)
                end = start + int(page_per)
                
                return await sync_to_async(JsonResponse)(deserializer.validated_data)
            
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 409:
                messages.error(request, "로봇 조회 중 오류가 발생했습니다.")
            else:
                messages.error(request, "로봇 조회 중 오류가 발생했습니다. 다시 시도해주세요.")
                
            return await sync_to_async(redirect)("/index/")  # 다시 초기 화면으로 
        except ValueError as e:
            logger.info('response format is invalid') #추후 로그로 변경
            return await sync_to_async(redirect)("/index/")
        
    elif request.method == 'DELETE':
        return delete_robot(request)
    elif request.method == 'PATCH':
        return patch_robot(request)
    else:
        logger.info('unexpected request.. '+ request.method) #추후 로그로 변경
        return await sync_to_async(redirect)("/index/")

async def delete_robot(request, robot_id):
    
    #이대로만 가면 지우기 너무 쉽게 되어 있기 때문에 사용자 정보도 같이 넣어준다(role, 권한 등등 넣기 위함)
    #당장은 그냥 지울 수 있게 구현.
    try:
        async with httpx.AsyncClient() as client:
            load_dotenv()
            robot_service_url = os.getenv('ROBOT_SERVICE_URL')
            logger.info(f'delete command : {robot_service_url+robot_id+'/'}')
            api_response = await client.delete(robot_service_url+robot_id+'/', params = {})
            api_response.raise_for_status()
            deserializer = RobotDelResponseSerializer(data=api_response.json())
            if not deserializer.is_valid():
                raise ValueError("Invalid value!")
                
            #log 등록
            logger.info(deserializer.validated_data.get('result'))
            #매번 업데이트 해준다. get 해올 때마다. 대신에 가져오는 수가 적기 때문에 메모리 유지해도 지장 없음
            return await sync_to_async(redirect)("/index/")
            
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 409:
            messages.error(request, "로봇 조회 중 오류가 발생했습니다.")
        else:
            messages.error(request, "로봇 조회 중 오류가 발생했습니다. 다시 시도해주세요.")
                
        return await sync_to_async(redirect)("/index/")  # 다시 초기 화면으로 
    except ValueError as e:
        logger.info('response format is invalid') #추후 로그로 변경
        return await sync_to_async(redirect)("/index/")
    
async def get_robot(request):
    res = HTMLRenderer(request, 'robot_manage/robot_patcher.html', params={})
    return await sync_to_async(HttpResponse)( res )

async def patch_robot(request):
    load_dotenv()
    robot_service_url = os.getenv('ROBOT_SERVICE_URL')
    parsed_data = None
    try:
        parsed_data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        messages.error(request, "요청 정보 확인이 필요합니다.")
        return redirect('/error/')
            
    serializer = RobotPatchSerializer(data=parsed_data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data
        
    try:
        async with httpx.AsyncClient() as client:
            api_response = await client.patch(robot_service_url+serializer.validated_data['robot_id']+'/', json=payload)
            print(api_response.json())
            api_response.raise_for_status()
            deserializer = RobotNormalResponseSerializer(data=api_response.json())
            if not deserializer.is_valid():
                raise ValueError("Invalid value!")
                
            #log 등록
            print(deserializer.validated_data.get('result'))
                
            return await sync_to_async(redirect)("/index/")
                
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        if status == 409:
             messages.error(request, "이미 등록된 로봇입니다.")
        else:
            messages.error(request, "로봇 수정 중 오류가 발생했습니다. 다시 시도해주세요.")
                
        return await sync_to_async(redirect)("/index/")  # 다시 로봇 등록 페이지로 
    except ValueError as e:
        print('response format is invalid') #추후 로그로 변경
        return await sync_to_async(redirect)("/error/")


async def modifying_robots(request, robot_id):
    if request.method == 'DELETE':
        logger.info('delete robot')
        return await delete_robot(request, robot_id)
        
    elif request.method == 'GET': #데이터는 sessionStorage에 저장되어 있음.
        logger.info('get modifying pages')
        return await get_robot(request)
    elif request.method == 'PATCH':
        logger.info('patch data')
        return await patch_robot(request)
    else:
        pass
    
    #show robot_mangae.html view and set data
    #after fixing data, send it to server using put_robot function
    response = redirect('/robots/management/')
    return response

async def detail_view_robots(request, robot_id):
    res = HTMLRenderer(request, 'robot_manage/robot_detail.html', params={'robotId':robot_id})
    return await sync_to_async(HttpResponse)( res ) 
    