import asyncio
from nats.aio.client import Client as NATS
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from PIL import Image, ImageDraw, ImageFont
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from api.models import ImageTask

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/imagequeue"
UPLOADS_DIR = "/app/uploads"
PROCESSED_DIR = "/app/processed"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def process_image(task_id):
    async with AsyncSessionLocal() as session:
        #  Get task info
        result = await session.execute(
            select(ImageTask).where(ImageTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            print(f"Task {task_id} not found")
            return

        filename = task.filename
        input_path = os.path.join(UPLOADS_DIR, filename)
        output_path = os.path.join(PROCESSED_DIR, filename)

        # Open and process image
        try:
            with Image.open(input_path) as im:
                draw = ImageDraw.Draw(im)
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=40)
                draw.text((10, 10), "AI magic added!", fill="red", font=font)
                im.save(output_path)
        except Exception as e:
            print(f"Error processing image: {e}")
            return

        # Update status in DB
        await session.execute(
            update(ImageTask).where(ImageTask.id == task_id).values(status="done")
        )
        await session.commit()
        print(f"Processed and updated task {task_id}")

async def main():
    nc = NATS()
    await nc.connect("nats://nats:4222")

    async def message_handler(msg):
        task_id = int(msg.data.decode())
        print(f"Received task: {task_id}")
        await process_image(task_id)

    await nc.subscribe("image_tasks", cb=message_handler)
    print("Worker listening for tasks...")
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    asyncio.run(main())