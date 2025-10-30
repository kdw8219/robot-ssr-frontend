from django.shortcuts import render
import jwt
from dotenv import load_dotenv
import os

# Create your views here.
def validate_access_token(token:str) -> bool:
        load_dotenv()
        
        print('vaidation works')
        
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