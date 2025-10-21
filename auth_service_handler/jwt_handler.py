def validate_jwt_token(token):
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
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception('TokenExpired')
    except jwt.InvalidTokenError:
        raise Exception('TokenInvalid')