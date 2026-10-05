import os
from pathlib import Path
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

# Load environment variables from .env or fallback to .env.example
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv(dotenv_path=BASE_DIR / '.env.example')

class Config:
    # Secret key for Flask sessions
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    # Database URL – MySQL first, SQLite fallback
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or f"sqlite:///{BASE_DIR / 'workforce.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# SQLAlchemy instance to be imported by the app factory
db = SQLAlchemy()
