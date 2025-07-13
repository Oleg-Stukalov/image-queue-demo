import os
try:
    import tomllib
except ImportError:
    import tomli as tomllib

def load_secrets():
    secrets_path = os.path.join(os.path.dirname(__file__), '.secrets.toml')
    if os.path.exists(secrets_path):
        with open(secrets_path, 'rb') as f:
            return tomllib.load(f)
    # fallback if file missing (e.g. in CI)
    return {}

secrets = load_secrets()

# or for pytest case
DATABASE_URL = os.getenv("DATABASE_URL") or secrets.get("database", {}).get("url")
NATS_URL = os.getenv("NATS_URL") or secrets.get("nats", {}).get("url")
UPLOADS_DIR = os.getenv("UPLOADS_DIR") or secrets.get("paths", {}).get("uploads_dir", "/app/uploads")
PROCESSED_DIR = os.getenv("PROCESSED_DIR") or secrets.get("paths", {}).get("processed_dir", "/app/processed")