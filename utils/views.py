from django.shortcuts import render
import jwt
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger("utils")

# Create your views here.
def validate_access_token(token:str) -> bool:
        load_dotenv()
        
        logger.debug('vaidation works')
        
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
            logger.info(f"Token has expired. {token}")
            return False
        except jwt.exceptions.InvalidTokenError:
            logger.info(f"Invalid token. {token}")
            return False