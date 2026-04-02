from app import create_app
from app.models import db, License, Activation, AuditLog
from sqlalchemy import text

def init_database():
    """Initialize the database with all tables"""
    print("🚀 Initializing database...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test database connection
            print("🔍 Testing database connection...")
            db.session.execute(text('SELECT 1')).scalar()
            print("✅ Database connected successfully")
            
            # Drop all tables (clean start)
            print("🗑️ Dropping existing tables...")
            db.drop_all()
            print("✅ Tables dropped")
            
            # Create all tables
            print("📦 Creating database tables...")
            db.create_all()
            print("✅ Tables created successfully")
            
            # Verify tables exist
            print("🔍 Verifying tables...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✅ Found tables: {tables}")
            
            print("\n🎉 Database initialization complete!")
            print("📋 Ready to generate licenses!")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    init_database()
