# test_db.py
from app import create_app
from app.models import db

app = create_app()
with app.app_context():
    # Test connection
    result = db.session.execute('SELECT 1').scalar()
    print(f"✅ Database connected! Result: {result}")
    
    # Check if tables exist
    tables = db.session.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    ).fetchall()
    print(f"📊 Existing tables: {[t[0] for t in tables]}")