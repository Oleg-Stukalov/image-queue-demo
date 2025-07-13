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

secrets = load_secrets()
DATABASE_URL = secrets["database"]["url"]
NATS_URL = secrets["nats"]["url"]