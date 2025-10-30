# auth/middleware.py
from django.http import JsonResponse
from django.shortcuts import redirect
import logging

logger = logging.getLogger('auth_service_handler')

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # 인증이 필요 없는 path
        self.public_paths = [
            '/',
            '/login/',
            '/signup/',
            '/logout/',
        ]

    def __call__(self, request):
        logger.info(f'[JWTAuthMiddleware] check path : {request.path}')
        if request.path[-1] != '/':
            request.path += '/'
            
        if request.path in self.public_paths:
            return self.get_response(request)
        
        # 1. 토큰이 없다면 401 Unauthorized 반환. 기본적으로 access token이 없으면 안됨. 오히려 refresh token이 optional
        if 'access_token' not in request.COOKIES:
            logger.info(f'[JWTAuthMiddleware] no access token')
            return JsonResponse({'detail': 'Unauthorized'}, status=401)

        # 2. 요청 처리
        response = self.get_response(request)
        return response
