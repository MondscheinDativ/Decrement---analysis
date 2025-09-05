import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    DATASETS_DIR = os.environ.get("DATASETS_DIR", os.path.abspath(os.path.join(os.getcwd(), "datasets")))
    MODELS_DIR = os.environ.get("MODELS_DIR", os.path.abspath(os.path.join(os.getcwd(), "models")))
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    DATA_KEY = os.environ.get("DATA_KEY", None)  # if None utils will generate per-run key
    MOCK_MODE = os.environ.get("MOCK_MODE", "true").lower() == "true"  # CI default
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(seconds=0)
