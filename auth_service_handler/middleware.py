# auth/middleware.py
from django.http import JsonResponse
from .jwt_handler import decode_jwt, refresh_jwt
from jwt import ExpiredSignatureError

class JWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Access Token 가져오기 (Cookie 또는 Header)
        token = request.COOKIES.get('access_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return JsonResponse({'detail': 'Unauthorized'}, status=401)

        # 2. JWT 파싱
        try:
            payload = decode_jwt(token)
            request.user = payload  # SSR에서 template context로 활용 가능
        except ExpiredSignatureError:
            # Access Token 만료 시 Refresh Token 사용
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                try:
                    new_token = refresh_jwt(refresh_token)
                    request.user = decode_jwt(new_token)
                    response = self.get_response(request)
                    response.set_cookie('access_token', new_token, httponly=True)
                    return response
                except Exception:
                    return JsonResponse({'detail': 'Unauthorized'}, status=401)
            else:
                return JsonResponse({'detail': 'Unauthorized'}, status=401)
        except Exception:
            return JsonResponse({'detail': 'Invalid token'}, status=401)

        # 3. 요청 처리
        response = self.get_response(request)
        return response
