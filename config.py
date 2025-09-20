import os
from datetime import timedelta

class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./url_shortener.db")
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # URL Settings
    BASE_URL = os.getenv("BASE_URL", "http://hostname:port")
    DEFAULT_VALIDITY_MINUTES = 30
    
    # Shortcode Settings
    SHORTCODE_LENGTH = 6
    SHORTCODE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

config = Config()

