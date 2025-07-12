from fastapi import FastAPI, File, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import os

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

    return {"task_id": task.id, "filename": task.filename, "message": "Upload successful"}