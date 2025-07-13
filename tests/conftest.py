import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def override_upload_dirs():
    # Override only if not running inside Docker
    if not os.getenv("RUNNING_IN_DOCKER"):
        os.environ["UPLOADS_DIR"] = os.path.abspath("uploads")
        os.environ["PROCESSED_DIR"] = os.path.abspath("processed")
        os.makedirs(os.environ["UPLOADS_DIR"], exist_ok=True)
        os.makedirs(os.environ["PROCESSED_DIR"], exist_ok=True)