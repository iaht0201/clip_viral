import asyncio
import redis.asyncio as redis

async def check_redis():
    r = redis.Redis()
    print(f"Keys: {await r.keys('*')}")
    # Inspect job list?
    # In arq, it uses a LIST for the queue?
    print(f"supoclip_tasks: {await r.lrange('supoclip_tasks', 0, -1)}")
    print(f"arq:queue: {await r.lrange('arq:queue', 0, -1)}")

if __name__ == "__main__":
    asyncio.run(check_redis())
