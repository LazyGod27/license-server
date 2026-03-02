import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())
    JWT_SECRET = os.getenv('JWT_SECRET', os.urandom(32).hex())
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', os.urandom(32).hex())
    
    # Use SQLite instead of PostgreSQL
    SQLALCHEMY_DATABASE_URI = 'sqlite:///licenses.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Remove Redis requirement for now
    # REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    RATE_LIMIT = "5 per minute"
    REQUEST_TIMEOUT = 60
    
    MAX_ACTIVATIONS_PER_LICENSE = 1
    TOKEN_EXPIRY_HOURS = 24
    
    ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', 'change-this-in-production')