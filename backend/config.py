import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

class Config:
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
    PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:5006").rstrip("/")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGIN_USERNAME = os.getenv("LOGIN_USERNAME")
    LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")
    # Stable across restarts (no extra secret to manage), derived from the credentials above.
    AUTH_TOKEN = hashlib.sha256(f"{LOGIN_USERNAME}:{LOGIN_PASSWORD}".encode()).hexdigest()
    