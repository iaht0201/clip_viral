import asyncio
import redis.asyncio as redis

async def check_redis():
    r = redis.Redis()
    key = 'progress:e0b9f4ad-358e-4be1-bc46-5b4372a51d6a'
    val = await r.get(key)
    print(f"Progress for e0b9: {val}")

if __name__ == "__main__":
    asyncio.run(check_redis())
