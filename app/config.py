import os
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "m4a"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
