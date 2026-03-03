from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Create db instance HERE (outside the function)
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    CORS(app)
    
    # THIS IS CRITICAL - initialize db with app
    db.init_app(app)
    
    # Create tables within app context
    with app.app_context():
        db.create_all()
    
    # Register routes
    from .routes import register_routes
    register_routes(app)
    
    return app