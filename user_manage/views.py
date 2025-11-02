from django.shortcuts import render, HttpResponse, redirect
import requests

from auth_service_handler.decorator import jwt_required
from utils.views import validate_access_token
from dotenv import load_dotenv
import os
import django.contrib.messages as messages
from user_manage.dto.loginSerializer import LoginSerializer
from django.views.decorators.csrf import csrf_exempt
import logging
import httpx

logger = logging.getLogger('user_manage')

def HTMLRenderer(request, template_name='user_manage/index.html', params={}):
    return render(request, template_name, params)

#login 시 세션이 남아있다면 index로 redirect(POST, GET 모두)
async def login(request):
    
    if request.method == 'POST':
        # ID/PWD validation check --> to User Service
        load_dotenv()
        
        #사용자 정보 체크
        api_url = os.getenv('USER_SERVICE_LOGIN_URL')
        
        userid = request.POST.get('userid')
        password = request.POST.get('password')
        payload = {
            "userid": userid,
            "password": password,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload)
            serializer = LoginSerializer(data = response.json())
        
        if not serializer.is_valid():
            logger.info(f'serializer fail : {response.json()}')
            return HttpResponse("Log in failed. ", status=400)
        
        data = serializer.validated_data
        
        if response.status_code == 200 or response.status_code == 201:
            response = redirect('/index/')
            set_default_header(response, data)
            
            return response
        elif response.status_code == 400:
            return redirect('/error/')
        else:
            return redirect('/error/')
        
    elif request.method == 'GET':
        access_token = get_access_token(request)
        
        logger.info(access_token)
        
        if access_token is None:
            logger.info("GET-login : no access token")
            HttpResponse(HTMLRenderer(request, 'user_manage/login.html', params={}))
        else:
            try:
                if not validate_access_token(access_token):
                    
                    raise Exception
                return redirect('/index/')
            except Exception as e: #예외상황 시 어차피 로그인 페이지로 이동 필요.
                if str(e) == 'TokenExpired':
                    pass
                elif str(e) == 'TokenInvalid':
                    pass
    
    return HttpResponse(HTMLRenderer(request, 'user_manage/login.html', params={}))

async def logout(request):
    
    load_dotenv()
    url_logout = os.getenv('AUTH_SERVICE_URL') #  refresh, access만 지운다. 사용자 정보 체크는 굳이 불필요하다.
    
    # TODO : async view를 써서 post request 하는 부분도 바꿔야한다.
    async with httpx.AsyncClient() as client:
        print(request.COOKIES)
        await client.post(url_logout, cookies=request.COOKIES)
    
    response = redirect('/')
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    response.delete_cookie('userId')
    response.delete_cookie('id')
    response.delete_cookie('role')
    
    return response

@jwt_required
def index(request):
    
    params = get_default_header_data(request)
    
    if not params.get('id'):
        return HttpResponse(HTMLRenderer(request,'user_manage/index_default.html', {}))
    
    return HttpResponse(HTMLRenderer(request,'user_manage/index.html', params))

async def default_index(request):
    
    # 1. Access Token 가져오기 (Cookie 또는 Header)
    try:
        token = request.COOKIES['access_token']
        return redirect('/index')
            
    except Exception as e:
        return HttpResponse(HTMLRenderer(request,'user_manage/index_default.html', params={}))

def error(request):
    params = get_default_header_data(request)
    return HttpResponse(HTMLRenderer(request,'user_manage/error.html', params))
    
async def signup(request):
    
    if request.method == 'POST':
        load_dotenv()
        api_url = os.getenv('USER_SERVICE_URL') + 'signup/'
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        payload = {
            "userid": username,
            "password": password,
            "email": email,
            "role": role,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                api_response = await client.post(api_url, json=payload)
                api_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if status == 409:
                messages.error(request, "이미 가입된 회원입니다.")
            else:
                messages.error(request, "회원가입 중 오류가 발생했습니다. 다시 시도해주세요.")
                
            return redirect("/signup/")  # 다시 회원가입 페이지로    
        
        if api_response.status_code == 201: # 201 Created
            response = HttpResponse(HTMLRenderer(request, 'user_manage/login.html', params={}))
            
            # login이니까 사실 token으로 뭘 할 필요는 없다.
            return response
        
        else:
            messages.error(request, "입력하신 회원 정보를 다시 확인해주세요")
            return redirect("/signup/")  # 다시 회원가입 페이지로
    
    else: # GET
       return HttpResponse(HTMLRenderer(request,'user_manage/signup.html', params={}))
   

def get_access_token(request):
    access_token = request.COOKIES.get('access_token', None)
    
    return access_token

def get_refresh_token(request):
    refresh_token = request.COOKIES.get('refresh_token', None)
    
    return refresh_token

def set_default_header(response, data:dict):
    if None != data.get('access_token'):
        response.set_cookie('access_token',
                            data.get('access_token'), 
                            httponly=True, 
                            secure=True, 
                            samesite='Lax')
        
    if None != data.get('refresh_token') :
        response.set_cookie('refresh_token',
                            data.get('refresh_token'), 
                            httponly=True, 
                            secure=True, 
                            samesite='Lax')
        
    if None != data.get('userId') :
        response.set_cookie('userId',
                            data.get('userId'), 
                            httponly=True, 
                            secure=True, 
                            samesite='Lax')
    
    if None != data.get('id') :
        response.set_cookie('id',
                            data.get('id'), 
                            httponly=True, 
                            secure=True, 
                            samesite='Lax')
        
    if None != data.get('role') :
        response.set_cookie('role',
                            data.get('role'), 
                            httponly=True, 
                            secure=True, 
                            samesite='Lax')   
        
    return response

def get_default_header_data(request):
    res =  {'id': request.COOKIES.get('id'), 'userId': request.COOKIES.get('userId'), 'role': request.COOKIES.get('role')}
    
    return res