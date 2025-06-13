import psycopg2
from app.config import POSTGRES_URI
import logging
import os
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def init_db():
    try:
        conn = psycopg2.connect(POSTGRES_URI)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                plan TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                request_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                audio_file TEXT,
                predicted_gender TEXT,
                predicted_age_group TEXT,
                gender_confidence REAL,
                age_confidence REAL,
                confidence_score REAL,
                is_correct INTEGER DEFAULT -1,
                features TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✅ PostgreSQL database initialized.")
    except Exception as e:
        logger.error(f"❌ PostgreSQL init failed: {e}")
        raise
def get_db():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )