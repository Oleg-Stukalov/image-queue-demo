from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import os
from config import NATS_URL, UPLOADS_DIR, PROCESSED_DIR
from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig
import asyncio
import logging
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from . import db
from . import models  # if you use models in this file

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs(UPLOADS_DIR, exist_ok=True)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...), session: AsyncSession = Depends(db.get_db)):
    logger.info(f"Received upload: {file.filename}")
    # Save file locally as before
    file_location = os.path.join(UPLOADS_DIR, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    logger.info(f"Saved file to {file_location}")
    # Save task in DB
    task = models.ImageTask(filename=file.filename, status=models.TaskStatus.pending)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    logger.info(f"Created DB task with id {task.id}")
    # Publish to NATS JetStream
    nc = NATS()
    await nc.connect(NATS_URL)
    js = nc.jetstream()
    try:
        await js.add_stream(name="image_tasks", subjects=["image_tasks"])
    except Exception:
        pass  # Stream probably already exists
    await js.publish("image_tasks", str(task.id).encode())
    await nc.drain()
    logger.info(f"Published task {task.id} to NATS JetStream")
    return {"task_id": task.id, "filename": task.filename, "message": "Upload successful"}

@app.get("/status/{task_id}")
async def get_status(task_id: int, session: AsyncSession = Depends(db.get_db)):
    result = await session.get(models.ImageTask, task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": result.id,
        "filename": result.filename,
        "status": result.status,
        "upload_time": result.upload_time,
    }