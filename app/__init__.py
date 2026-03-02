from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    CORS(app)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    from .routes import register_routes
    register_routes(app)
    
    return app