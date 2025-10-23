def validate_access_token(token):
    """
    Validates a JWT token and returns the payload if valid.
    Raises an exception if the token is invalid or expired.
    """
    import jwt
    from dotenv import load_dotenv
    import os

    load_dotenv()
    SECRET_KEY = os.getenv('SECRET_KEY')

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        #non expired, valid token...
        #simple check이기 때문에 이 정도로만 체크한다.(Access Token)
        
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception('TokenExpired')
    except jwt.InvalidTokenError:
        raise Exception('TokenInvalid')