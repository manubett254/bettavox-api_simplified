import os

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "m4a"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

# ✅ This format is for psycopg2
POSTGRES_URI = (
    f"dbname={os.getenv('POSTGRES_DB')} "
    f"user={os.getenv('POSTGRES_USER')} "
    f"password={os.getenv('POSTGRES_PASSWORD')} "
    f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
    f"port={os.getenv('POSTGRES_PORT', '5432')}"
)
