from django.http import JsonResponse
from django.shortcuts import redirect
from dotenv import load_dotenv
import os
import httpx
from functools import wraps
from typing import Optional, Tuple, Dict
import json
from utils.views import validate_access_token
import logging
import asyncio
from utils import httpClient as hc

logger = logging.getLogger("auth_service_handler")

def jwt_required(view_func):
    def get_access_token(request) -> Optional[str]:
        access_token = request.COOKIES.get('access_token')
        return access_token
    
    #auth에서 refresh 유효성 체크를 진행
    async def refresh_tokens(client: httpx.AsyncClient, refresh_token: str) -> Tuple[bool, Optional[Dict]]:
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
                logger.info(f'refresh success {response.status_code}')    
                response_string = response.content.decode()
                data = json.loads(response_string)
                logger.info(f'token loading complete {data['access_token']}')    
                return True, {'access_token' : data['access_token'] ,'refresh_token': refresh_token}
             
            return False, None
        except Exception as e:
            logger.info(f'refresh fail...{e}')
            return False, None
        
    async def refresh_token_process(request, *args, **kwargs):
        # 액세스 토큰이 만료된 경우, 리프레시 토큰으로 갱신 시도
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return JsonResponse({'error': 'Refresh token missing'}, status=401)
        
        # refresh_token 토큰 검증
        is_valid, payload = await refresh_tokens(hc.async_client, refresh_token)
        if is_valid:
            # 토큰이 유효하면 access token 취득 후 단말로 전달
            logger.info("refresh token is valid")
            request.COOKIES['access_token'] = payload.get('access_token')
            if asyncio.iscoroutinefunction(view_func):
                response = await view_func(request, *args, **kwargs)
            else:
                response = view_func(request, *args, **kwargs)
            
            response.set_cookie('access_token',
                        payload.get('access_token'), 
                        httponly=True, 
                        secure=True, 
                        samesite='Lax')    
            
            return response
        
        else:
            logger.error("refresh token is invalid")
            response = redirect('/login')
            response.delete_cookie('refresh_token')
            response.delete_cookie('access_token')
            return response
    
    @wraps(view_func)
    async def _wrapped_view(request, *args, **kwargs):
        access_token = get_access_token(request)
        
        if access_token: #access가 있으면
            if validate_access_token(access_token):
                
                response = None
                if asyncio.iscoroutinefunction(view_func):
                    response = await view_func(request, *args, **kwargs)
                else:
                    response = view_func(request, *args, **kwargs)
                return response
            else: #invalid access token
                return await refresh_token_process(request, *args, **kwargs)
        else: #refresh token check logic
            return await refresh_token_process(request, *args, **kwargs)
            
        
    return _wrapped_view