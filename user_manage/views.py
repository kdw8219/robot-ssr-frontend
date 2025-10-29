from django.shortcuts import render, HttpResponse, redirect
import requests

from auth_service_handler.decorator import jwt_required
from auth_service_handler.jwt_handler import validate_access_token
from dotenv import load_dotenv
import os
import django.contrib.messages as messages
import json
from user_manage.dto.loginSerializer import LoginSerializer
from django.views.decorators.csrf import csrf_exempt

def HTMLRenderer(request, template_name='user_manage/index.html', params={}):
    return render(request, template_name, params)

#login 시 세션이 남아있다면 index로 redirect(POST, GET 모두)
def login(request):
    
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
        
        # TODO : async view를 써서 post request 하는 부분도 바꿔야한다.
        response = requests.post(api_url, json=payload)
        serializer = LoginSerializer(data = response.json())
        
        if not serializer.is_valid():
            return HttpResponse("Log in failed. ", status=400)
        
        data = serializer.validated_data
        
        if response.status_code == 200 or response.status_code == 201:
            response = redirect('/index')
            default_header_set(response, data)
            
            return response
        elif response.status_code == 400:
            return HttpResponse("Log in failed: " + data.get('error', 'Unknown error'), status=400)
        else:
            return HttpResponse("An unexpected error occurred.", status=500)
        
    elif request.method == 'GET':
        access_token = get_access_token(request)
        
        if access_token is None:
            print("no access token")
            HttpResponse(HTMLRenderer(request, 'user_manage/login.html', params={}))
        try:
             validate_access_token(access_token)
             return redirect('/index')
        except Exception as e: #예외상황 시 어차피 로그인 페이지로 이동 필요.
            if str(e) == 'TokenExpired':
                pass
            elif str(e) == 'TokenInvalid':
                pass
    
    return HttpResponse(HTMLRenderer(request, 'user_manage/login.html', params={}))

def logout(request):
    
    load_dotenv()
    url_logout = os.getenv('AUTH_SERVICE_URL')
    
    # Logout 요청 후 Don't care
    requests.delete(url_logout, cookies=request.COOKIES, auth = request.headers.get('Authorization',''))
    
    return redirect('/')

@jwt_required
def index(request):
    return HttpResponse(HTMLRenderer(request,'user_manage/index.html', params={}))

def default_index(request):
    return HttpResponse(HTMLRenderer(request,'user_manage/index.html', params={}))

''' 
    TODO : signup view post 구현
     - POST로 요청이 오면 User Service로 회원가입 요청을 보낸다.
     - User Service에서 성공 응답이 오면 login 페이지로 redirect
     - 실패 응답이 오면 signup 페이지로 다시 돌아오도록 한다.
'''
def signup(request):
    
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
            api_response = requests.post(api_url, json=payload)
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

def default_header_set(response, data:dict):
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
        
    return response