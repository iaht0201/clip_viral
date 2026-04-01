import pytest
from sqlalchemy import select
from src.models import Task, User, Source, generate_uuid_string

@pytest.mark.asyncio
async def test_create_task_with_json_list(db_session):
    # 1. Create a mandatory user first
    user_id = generate_uuid_string()
    new_user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        emailVerified=True
    )
    db_session.add(new_user)
    await db_session.commit()

    # 2. Test Task with JSON field mapping
    clip_ids = ["clip_1", "clip_2", "clip_3"]
    new_task = Task(
        id=generate_uuid_string(),
        user_id=user_id, # Link to created user
        status="completed",
        generated_clips_ids=clip_ids
    )
    
    db_session.add(new_task)
    await db_session.commit()
    
    # Query back to verify JSON mapping
    stmt = select(Task).where(Task.user_id == user_id)
    result = await db_session.execute(stmt)
    task = result.scalar_one()
    
    assert task.generated_clips_ids == clip_ids
    assert isinstance(task.generated_clips_ids, list)

@pytest.mark.asyncio
async def test_source_type_constraint(db_session):
    source = Source(
        id="src-1",
        type="youtube",
        title="Test Video Title",
        url="https://youtube.com/test"
    )
    db_session.add(source)
    await db_session.commit()
    
    stmt = select(Source).where(Source.id == "src-1")
    result = await db_session.execute(stmt)
    saved_source = result.scalar_one()
    assert saved_source.type == "youtube"
    assert saved_source.title == "Test Video Title"
