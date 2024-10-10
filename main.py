import os
from flask import Flask
from logging.handlers import RotatingFileHandler
import logging
from config import DATA_DIR, APP_LOG_FILE
from models import init_db, close_db
from routes import bp

def create_app():
    app = Flask(__name__)

    # Set up logging
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    handler = RotatingFileHandler(APP_LOG_FILE, maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Initialize database
    with app.app_context():
        init_db()

    # Register blueprint
    app.register_blueprint(bp)

    # Register database close function
    app.teardown_appcontext(close_db)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0')
