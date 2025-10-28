from django.http import JsonResponse
from dotenv import load_dotenv
import os
import httpx
from functools import wraps
from typing import Optional, Tuple, Dict
import json
import jwt


def jwt_required(view_func):
    def get_access_token(request) -> Optional[str]:
        access_token = request.COOKIES.get('access_token')
        return access_token
    
    def validate_access_token(token:str) -> bool:
        load_dotenv()
        
        SECRET_KEY = os.getenv('ACCESS_SECRET_KEY')
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=["HS256"],
                options={"require": ["exp", "iat"]}
            )
            
            return True

        except jwt.exceptions.ExpiredSignatureError:
            print("Token has expired.")
            return False
        except jwt.exceptions.InvalidTokenError:
            print("Invalid token.")
            return False
        
    async def validate_refresh_token(client: httpx.AsyncClient, token: str) -> Tuple[bool, Optional[Dict]]:
        """토큰 유효성 검증, valid하면 새 access 발급"""
        load_dotenv()
        auth_url = os.getenv('AUTH_SERVICE_URL')
        
        try:
            response = await client.post(
                f'{auth_url}validate/',
                json={'refresh_token': token}
            )
            if response.status_code == 200:
                return True, response.json()
            return False, None
        except Exception as e:
            print(f"validate refresh token fail : {e}")
            return False, None
        
    async def refresh_tokens(client: httpx.AsyncClient, refresh_token: str) -> Optional[Dict]:
        # service url 획득
        load_dotenv()
        auth_url = os.getenv('AUTH_SERVICE_URL')
        
        try:
            #Auth Service에 토큰 갱신 요청
            response = await client.post(
                f'{auth_url}refresh/',
                json={'refresh_token': refresh_token}
            )
            
            if response.status_code == 200 or response.status_code == 201:
                response_string = response.content.decode()
                data = json.loads(response_string)
                
                return {'access_token' : data['access_token'] ,'refresh_token': data['refresh_token']}
             
            return None
        except Exception as e:
            print(f'refresh fail...{e}')
            return None

    async def refresh_token_process(request, *args, **kwargs):
        
        async with httpx.AsyncClient() as client:
            # 액세스 토큰이 만료된 경우, 리프레시 토큰으로 갱신 시도
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return JsonResponse({'error': 'Refresh token missing'}, status=401)
            
            # refresh_token 토큰 검증
            is_valid, payload = await validate_refresh_token(client, refresh_token)
            if is_valid:
                # 토큰이 유효하면 access token 취득 후 단말로 전달
                request.user_id = payload.get('user_id')
                response = view_func(request, *args, **kwargs)
                return response
        
            # 새 토큰 발급 시도
            new_tokens = await refresh_tokens(client, refresh_token)
            if not new_tokens:
                return JsonResponse({'error': 'Failed to refresh tokens'}, status=401)
            
            # 새 토큰으로 요청 처리
            request.user_id = new_tokens.get('user_id')
            response = view_func(request, *args, **kwargs)
            
            # 새 토큰을 쿠키에 설정 -> 이건 Refresh Token에서만.
            # 수정 필요 
            
            response.set_cookie(
                'refresh_token',
                new_tokens['refresh_token'],
                httponly=True,
                secure=True,
                samesite='Lax'
            )
            
            response.set_cookie(
                'access_token',
                new_tokens['access_token'],
                httponly=True,
                secure=True,
                samesite='Lax'
            )
            
            return response
    
    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        access_token = get_access_token(request)
        
        if access_token: #access가 있으면
            if validate_access_token(access_token): # access validation check
                response = view_func(request, *args, **kwargs)
                return response
            else: #invalid access token
                return await refresh_token_process(request, *args, **kwargs)
        else: #refresh token check logic
            return await refresh_token_process(request, *args, **kwargs)
            
        
    return _wrapped_view