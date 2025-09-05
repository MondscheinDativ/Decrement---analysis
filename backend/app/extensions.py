import os
import redis
from cryptography.fernet import Fernet

cache = None

def init_extensions(app):
    global cache
    cache = redis.Redis.from_url(app.config["REDIS_URL"]) if app.config["REDIS_URL"] else None
    # ensure folders exist
    os.makedirs(app.config["DATASETS_DIR"], exist_ok=True)
    os.makedirs(app.config["MODELS_DIR"], exist_ok=True)

def get_cipher(app):
    key = app.config.get("DATA_KEY") or Fernet.generate_key()
    return Fernet(key)
