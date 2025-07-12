from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import os
from nats.aio.client import Client as NATS
import asyncio

from . import db
from . import models  # if you use models in this file

app = FastAPI()

UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...), session: AsyncSession = Depends(db.get_db)):
    # Save file locally as before
    file_location = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    # Save task in DB
    task = models.ImageTask(filename=file.filename, status=models.TaskStatus.pending)
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # Publish to NATS
    nc = NATS()
    await nc.connect("nats://nats:4222")
    await nc.publish("image_tasks", str(task.id).encode())
    await nc.drain()

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