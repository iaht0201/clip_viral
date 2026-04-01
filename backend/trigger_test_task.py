import asyncio
import uuid
import sys
from arq import create_pool
from arq.connections import RedisSettings

async def trigger_task():
    redis = await create_pool(RedisSettings())
    task_id = str(uuid.uuid4())
    url = "https://www.youtube.com/watch?v=Bx_AD5kfp0Q"
    print(f"Triggering task {task_id} for {url}")
    
    await redis.enqueue_job(
        "process_video_task",
        task_id=task_id,
        url=url,
        source_type="youtube",
        user_id="test_user",
        task_mode="clips",
        _queue_name="supoclip_tasks"
    )
    print("Task enqueued! Monitor logs/backend.log for progress.")

if __name__ == "__main__":
    asyncio.run(trigger_task())
