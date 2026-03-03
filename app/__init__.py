from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()


def create_app():

    app = Flask(__name__)
    app.config.from_object("config.Config")

    CORS(app)

    db.init_app(app)

    # ? Register routes BEFORE DB operations
    from .routes import register_routes
    register_routes(app)

    # ? Create tables safely
    with app.app_context():
        try:
            db.create_all()
            print("? Database tables ready")
        except Exception as e:
            print("? Database initialization warning:", e)

    return app