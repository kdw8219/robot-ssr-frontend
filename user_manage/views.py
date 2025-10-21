from django.shortcuts import render, HttpResponse, redirect
import requests

from auth_service_handler.decorator import jwt_required
from auth_service_handler.jwt_handler import validate_jwt_token
from dotenv import load_dotenv
import os

def HTMLRenderer(request, template_name='user_manage/index.html', params={}):
    return render(request, template_name, params)

# Create your views here.
def login(request):
    
    if request.method == 'POST':
        # ID/PWD validation check --> to User Service
        
        load_dotenv()
        
        api_url = os.getenv('USER_SERVICE_URL')
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        payload = {
            "username": username,
            "password": password,
            "email": email,
            "role": role,
        }

        response = requests.post(api_url, json=payload)

        if response.status_code == 201:
            return HttpResponse(HTMLRenderer(request, 'user_manage/login.html', params={}))
        elif response.status_code == 400:
            return HttpResponse("Signup failed: " + response.json().get('error', 'Unknown error'), status=400)
        else:
            return HttpResponse("An unexpected error occurred.", status=500)
        
    elif request.method == 'GET':
        access_token = get_access_token(request)
        
        if access_token is None:
            HttpResponse(HTMLRenderer(request, 'user_manage/login.html', params={}))
        try:
             validate_jwt_token(access_token)
             return redirect('/index/')
        except Exception as e:
            if str(e) == 'TokenExpired':
                pass
            elif str(e) == 'TokenInvalid':
                pass
    
    return HttpResponse(HTMLRenderer(request, 'user_manage/login.html', params={}))

@jwt_required
def index(request):
    return HttpResponse(HTMLRenderer(request,'user_manage/index.html', params={}))

def signup(request):
    
    if request.method == 'POST':
        # signup avaiability check --> to User Service
        # User Service return success or fail and response it to user
        if True: # signup success
            return HttpResponse(HTMLRenderer(request, 'user_manage/login.html', params={}))
        else:
            return 
    
    else: # GET
       return HttpResponse(HTMLRenderer(request,'user_manage/signup.html', params={}))
   

def get_access_token(request):
    auth_header = request.header.get('Authorization', None)
    
    if auth_header is None:
        return None
    
    parts = auth_header.split(' ')
    if len(parts) != 2 or parts[0] != 'Bearer':
        return None
    
    return parts[1]

def get_refresh_token(request):
    refresh_token = request.COOKIES.get('refresh_token', None)
    
    return refresh_token