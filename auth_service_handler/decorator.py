from django.http import JsonResponse
import jwt
from dotenv import load_dotenv
import os

def jwt_required(view_func):

    def _wrapped_view(request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', None)
        if token is None:
            return JsonResponse({'error': 'Authorization header missing'}, status=401)

        load_dotenv()
        SECRET_KEY = os.getenv('SECRET_KEY')
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        return view_func(request, *args, **kwargs)

    return _wrapped_view