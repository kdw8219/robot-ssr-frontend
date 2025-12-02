import jwt
import datetime
import os
from dotenv import load_dotenv
from typing import Optional
import logging
import redis.asyncio as asyncredis

logger = logging.getLogger('redis')

# 전역 Redis 객체
redis = None

async def get_redis():
    global redis
    if not redis:
        # 한 번만 연결 생성
        load_dotenv()
        URL = os.getenv('REDIS_URL')
        PORT = os.getenv('REDIS_PORT')
        PASSWORD = os.getenv('REDIS_AUTH')
        redis = await asyncredis.Redis(host=URL
                                       , port=PORT
                                       , password=PASSWORD
                                       , decode_responses=True)
    return redis

async def get_ws_session(session):
    
    conn = await get_redis()
    key = await conn.get(f'blacklist_{token}')
    
    if key is None:# conn 했더니 데이터가 없다. --> 유효하다 --> True
        return True
    
    return False
    
async def add_ws_session(token):
    logger.info('[tokens/add_token_to_blacklist] start adding token to blacklist')
    conn = await get_redis()
    res = await conn.set(f'blacklist_{token}', 1, ex = 10*24*60*60)  # 10일 동안 블랙리스트에 저장
    
    if res == None:
        logger.info('[tokens/add_token_to_blacklist] get auth post request!')
