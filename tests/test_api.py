import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from api.main import app
from config import DATABASE_URL
from api import db
import shutil

@pytest.fixture
def async_session_maker():
    engine = create_async_engine(DATABASE_URL, echo=True)
    return sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

def get_override_db(async_session_maker):
    async def override_get_db():
        async with async_session_maker() as session:
            yield session
    return override_get_db

@pytest.mark.asyncio
async def test_upload_and_status(async_session_maker, tmp_path):
    app.dependency_overrides[db.get_db] = get_override_db(async_session_maker)
    # Copy the existing test image to the temp path
    test_file = tmp_path / "test_image.JPG"
    shutil.copyfile("test_image.JPG", test_file)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(test_file, "rb") as f:
            files = {"file": ("test_image.JPG", f, "image/jpeg")}
            response = await client.post("/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        task_id = data["task_id"]

        response = await client.get(f"/status/{task_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["status"] == "pending"

@pytest.mark.asyncio
async def test_status_not_found(async_session_maker):
    app.dependency_overrides[db.get_db] = get_override_db(async_session_maker)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/status/999999")
        assert response.status_code == 404
