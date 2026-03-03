from app import create_app
from app.models import db
from sqlalchemy import text

print("🔍 Testing database connection...")

# Create the app
app = create_app()

# This is the key - we need to push an app context
with app.app_context():
    try:
        # Test connection with text()
        result = db.session.execute(text("SELECT 1")).scalar()
        print(f"✅ Database connected! Result: {result}")
        
        # Check if we can create tables
        print("📦 Creating tables if they don't exist...")
        db.create_all()
        print("✅ Tables created/verified")
        
        # List tables
        tables = db.session.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        ).fetchall()
        
        if tables:
            print(f"📊 Existing tables: {[t[0] for t in tables]}")
        else:
            print("📊 No tables found in information_schema")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()