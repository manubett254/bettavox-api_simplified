import sqlite3
import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def init_db():
    try:
        conn = sqlite3.connect('predictions.db')
        cursor = conn.cursor()

        # Users table (API key based access)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                plan TEXT DEFAULT 'free',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Usage table (tracks daily request counts)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                request_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Predictions table (tracks prediction history)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_file TEXT,
                predicted_gender TEXT,
                predicted_age_group TEXT,
                gender_confidence REAL,
                age_confidence REAL,
                confidence_score REAL,
                is_correct INTEGER DEFAULT -1,
                features TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        raise
