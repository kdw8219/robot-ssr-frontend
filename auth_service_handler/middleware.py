# auth/middleware.py
from django.http import JsonResponse

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # 인증이 필요 없는 path
        self.public_paths = [
            '/',
            '/login/',
            '/signup/',
        ]

    def __call__(self, request):
        if request.path in self.public_paths:
            return self.get_response(request)
        
        # 1. Access Token 가져오기 (Cookie 또는 Header)
        token = request.COOKIES['access_token']
        
        # 2. 토큰이 없다면 401 Unauthorized 반환. 기본적으로 access token이 없으면 안됨. 오히려 refresh token이 optional
        if not token:
            return JsonResponse({'detail': 'Unauthorized'}, status=401)

        # 3. 요청 처리
        response = self.get_response(request)
        return response
