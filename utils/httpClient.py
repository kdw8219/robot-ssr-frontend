import atexit 
import asyncio 
import httpx 

async_client = httpx.AsyncClient() 

atexit.register(lambda: asyncio.run(async_client.aclose()))