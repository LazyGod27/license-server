import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Security Keys
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())
    JWT_SECRET = os.getenv('JWT_SECRET', os.urandom(32).hex())
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', os.urandom(32).hex())
    ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', 'change-this-in-production')

    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Fix Railway's postgres:// URL (must be postgresql://)
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        print(f"✅ Fixed DATABASE_URL format")  # This will show in logs
    
    # Use PostgreSQL if available, otherwise SQLite
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        print(f"✅ Using PostgreSQL database")
    else:
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'licenses.db')}"
        print(f"⚠️ Using SQLite database (no DATABASE_URL found)")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    # App Settings
    RATE_LIMIT = "5 per minute"
    REQUEST_TIMEOUT = 60
    MAX_ACTIVATIONS_PER_LICENSE = 1
    TOKEN_EXPIRY_HOURS = 24
