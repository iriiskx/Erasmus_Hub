import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "change-me-in-production-please-use-env-variable"
    UPLOAD_FOLDER = os.path.join("static", "uploads")
    MAX_UPLOAD_SIZE = 16 * 1024 * 1024
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}





