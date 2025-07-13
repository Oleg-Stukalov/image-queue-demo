from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Request, Form
from sqlalchemy.ext.asyncio import AsyncSession
import os
from config import NATS_URL, UPLOADS_DIR, PROCESSED_DIR
from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig
import asyncio
import logging
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from . import db
from . import models  # if you use models in this file

app = FastAPI()

# Serve processed images as static files
app.mount("/processed", StaticFiles(directory=PROCESSED_DIR), name="processed")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs(UPLOADS_DIR, exist_ok=True)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
        <head><title>Upload Image</title></head>
        <body>
            <h1>Upload an Image</h1>
            <form action="/upload" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept="image/*">
                <input type="submit" value="Upload">
            </form>
        </body>
    </html>
    """

@app.post("/upload")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(db.get_db)
):
    logger.info(f"Received upload: {file.filename}")
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
        pass
    await js.publish("image_tasks", str(task.id).encode())
    await nc.drain()
    logger.info(f"Published task {task.id} to NATS JetStream")
    # If browser form, redirect to /result/{filename}
    if request.headers.get("accept", "").find("text/html") != -1:
        return RedirectResponse(url=f"/result/{file.filename}", status_code=303)
    return {"task_id": task.id, "filename": task.filename, "message": "Upload successful"}

@app.get("/result/{filename}", response_class=HTMLResponse)
def show_result(filename: str):
    # Show the processed image if it exists
    processed_url = f"/processed/{filename}"
    return f"""
    <html>
        <head><title>Processed Image</title></head>
        <body>
            <h1>Processed Image</h1>
            <img src='{processed_url}' alt='Processed image' style='max-width:600px;'><br>
            <a href='/'>Upload another image</a>
        </body>
    </html>
    """

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