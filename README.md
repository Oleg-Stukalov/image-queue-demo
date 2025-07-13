PYTEST:
(venv) linuxuser@lena-olia:~/python/image-queue-demo$ PYTHONPATH=. \
> UPLOADS_DIR=uploads \
> PROCESSED_DIR=processed \
> DATABASE_URL="postgresql+asyncpg://postgres:postgres@172.17.0.1:5432/imagequeue" \
> NATS_URL="nats://172.17.0.1:4222" \
> pytest tests/