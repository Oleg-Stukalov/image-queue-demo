import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from api.models import ImageTask, TaskStatus
import shutil
import os

@pytest.mark.asyncio
async def test_worker_completes_task():
    # Use the shared uploads directory
    uploads_dir = os.getenv("UPLOADS_DIR") or os.path.abspath("uploads")
    test_file = os.path.join(uploads_dir, "test_image.JPG")
    if not os.path.exists(test_file):
        shutil.copyfile("test_image.JPG", test_file)

    # Use real HTTP requests to the running FastAPI app
    async with AsyncClient(base_url="http://localhost:8000") as client:
        with open(test_file, "rb") as f:
            response = await client.post("/upload", files={"file": ("test_image.JPG", f, "image/jpeg")})
        assert response.status_code == 200
        data = response.json()
        task_id = data["task_id"]

    # Wait for worker to process (max 10 sec)
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    for i in range(20):  # check every 0.5s for max 10s
        async with async_session() as session:
            task = await session.get(ImageTask, task_id)
            if task and task.status == TaskStatus.done:
                break
        await asyncio.sleep(0.5)
    else:
        pytest.fail("Task was not processed by worker")

    assert task.status == TaskStatus.done
