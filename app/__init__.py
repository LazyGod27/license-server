from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    CORS(app)
    db.init_app(app)
    limiter.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    from .routes import register_routes
    register_routes(app)
    
    return app