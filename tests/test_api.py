from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
import pytest
from api.main import app

@pytest.mark.asyncio
async def test_upload_and_status(tmp_path):
    test_file = tmp_path / "test.jpg"
    test_file.write_bytes(b"dummy image data")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(test_file, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response = await client.post("/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        task_id = data["task_id"]

        response = await client.get(f"/status/{task_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["status"] == "pending"
