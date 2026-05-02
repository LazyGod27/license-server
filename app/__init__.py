from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text

# Create db instance HERE (outside the function)
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    CORS(app)
    
    # THIS IS CRITICAL - initialize db with app
    db.init_app(app)
    
    # Create tables within app context with error handling
    with app.app_context():
        try:
            # Test database connection first
            db.session.execute(text('SELECT 1'))
            print("✅ Database connected")
            
            # Create tables if they don't exist
            db.create_all()
            print("✅ Database tables ready")
            
        except Exception as e:
            print(f"⚠️ Database connection issue: {e}")
            print("🔄 App will continue, but database features may not work")
    
    # Register routes
    from .routes import register_routes
    register_routes(app)
    
    return app