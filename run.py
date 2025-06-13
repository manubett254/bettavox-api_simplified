from flask import Flask
from flask_cors import CORS
from app.routes import routes
import os
import logging
import sys
import sqlite3


# Logging Configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Prevent duplicate handlers
if not logger.handlers:
    logger.addHandler(handler)


# Disable Flask's default logger
flask_log = logging.getLogger('werkzeug')
flask_log.setLevel(logging.WARNING)


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.register_blueprint(routes)
    app.secret_key = os.urandom(24)
    app.config.from_object('app.config')
    CORS(app)
    return app

app = create_app()

if __name__ == '__main__':
    logger.info("🚀 Starting Flask application...")
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get("PORT", 5000)), 
        use_reloader=False,    # Avoids multiple reloads manually
        debug=False
    )
