import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('8FvQmT6YyH2pRz9Ls4WjXkNc3DvUa1Gt5So8BhJm7Re0Yz', os.urandom(32).hex())
    JWT_SECRET = os.getenv('3KsH9LpQ4Zf2WvC7Nx8JdY5Gt8UaR6VmPo1YhTqE', os.urandom(32).hex())
    ENCRYPTION_KEY = os.getenv('Q9x2Bv7Lm4Yz8Nc3FdH6PjK1RtW0Sa', os.urandom(32).hex())
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///licenses.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    RATE_LIMIT = "5 per minute"
    REQUEST_TIMEOUT = 60
    
    MAX_ACTIVATIONS_PER_LICENSE = 1
    TOKEN_EXPIRY_HOURS = 24
    
    ADMIN_API_KEY = os.getenv('5ZfR2Vn8QmL3YpJ6HsT4Wc9KdX0Ea', 'change-this-in-production')