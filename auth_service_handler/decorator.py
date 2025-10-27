from django.http import JsonResponse
from dotenv import load_dotenv
import os
import httpx
from functools import wraps
from typing import Optional, Tuple, Dict
import json
import jwt


def jwt_required(view_func):
    async def get_access_token(request) -> Optional[str]:
        auth_header = request.META.get('AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None
    
    async def validate_access_token(token:str) -> bool:
        load_dotenv()
        
        SECRET_KEY = os.getenv('SECRET_KEY')
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=["HS256"],
                options={"require": ["exp", "iat"]}
            )
            
            return True

        except jwt.ExpiredSignatureError:
            print("Token has expired.")
            return False
        except jwt.InvalidTokenError:
            print("Invalid token.")
            return False
        
    async def validate_refresh_token(client: httpx.AsyncClient, token: str) -> Tuple[bool, Optional[Dict]]:
        """토큰 유효성 검증"""
        load_dotenv()
        auth_url = os.getenv('AUTH_SERVICE_URL')
        
        try:
            response = await client.post(
                f'{auth_url}/validate/',
                json={'refresh_token': token}
            )
            if response.status_code == 200:
                return True, response.json()
            return False, None
        except Exception:
            return False, None
        
    async def refresh_tokens(client: httpx.AsyncClient, refresh_token: str) -> Optional[Dict]:
        # service url 획득
        load_dotenv()
        auth_url = os.getenv('AUTH_SERVICE_URL')
        
        try:
            #Auth Service에 토큰 갱신 요층
            cookies = {
                'refresh_token': refresh_token,
                'httponly':True,
                'secure':True,
                'samesite':"Lax"
                }
            response = await client.post(
                f'{auth_url}/token/refresh/',
                cookies,
                json={'request': 'new_tokens'}
            )
            if response.status_code == 200:
                response_string = response.content.decode()
                data = json.loads(response_string)
                
                return {'access_token' : data['access_token'] ,'refresh_token': data['refresh_token']}
                
            return None
        except Exception:
            return None

    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        token = get_access_token(request)
        
        print('in decorator' + token)
        
        if token is None:
            return JsonResponse({'error': 'Authorization header missing'}, status=401)
        elif validate_access_token(token):
            response = view_func(request, *args, **kwargs)
            return response
            
        async with httpx.AsyncClient() as client:
            # 액세스 토큰이 만료된 경우, 리프레시 토큰으로 갱신 시도
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return JsonResponse({'error': 'Refresh token missing'}, status=401)
            
            # refresh_token 토큰 검증
            is_valid, payload = await validate_refresh_token(client, token)
            
            if is_valid:
                # 토큰이 유효하면 페이로드 설정하고 진행
                request.user_id = payload.get('user_id')
                response = await view_func(request, *args, **kwargs)
                return response
            
            # 새 토큰 발급 시도
            new_tokens = await refresh_tokens(client, refresh_token)
            if not new_tokens:
                return JsonResponse({'error': 'Failed to refresh tokens'}, status=401)
            
            # 새 토큰으로 요청 처리
            request.user_id = new_tokens.get('user_id')
            response = await view_func(request, *args, **kwargs)
            
            # 새 토큰을 쿠키에 설정 -> 이건 Refresh Token에서만.
            # 수정 필요 
            response.set_header('Authorization', f"Bearer {new_tokens['access_token']}")
            response.set_cookie(
                'refresh_token',
                new_tokens['refresh_token'],
                httponly=True,
                secure=True,
                samesite='Strict'
            )
            
            return response
        
    return _wrapped_view