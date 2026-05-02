#!/usr/bin/env python3
"""
Remote Database Initialization Script
This script connects to your remote Render database and creates the required tables
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_remote_database():
    """Initialize the remote database with all tables"""
    print("🚀 Initializing REMOTE database...")
    print(f"📍 Database URL: {os.getenv('DATABASE_URL', 'Not set!')}")
    
    # Set the database URL to your remote database
    os.environ['DATABASE_URL'] = 'postgresql://license_db_new_ntwx_user:zuDku3V3lGGsWFPJyXVYEbKcSbOV2TBL@dpg-d7qshavavr4c73f5nsdg-a/license_db_new_ntwx'
    
    try:
        from app import create_app
        from app.models import db, License, Activation, AuditLog
        from sqlalchemy import text
        
        app = create_app()
        
        with app.app_context():
            try:
                # Test database connection
                print("🔍 Testing remote database connection...")
                result = db.session.execute(text('SELECT 1')).scalar()
                print("✅ Remote database connected successfully")
                
                # Check if tables already exist
                print("🔍 Checking existing tables...")
                inspector = db.inspect(db.engine)
                existing_tables = inspector.get_table_names()
                print(f"📋 Current tables: {existing_tables}")
                
                # Create all tables
                print("📦 Creating database tables...")
                db.create_all()
                print("✅ Tables created successfully")
                
                # Verify tables exist
                print("🔍 Verifying tables...")
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                print(f"✅ Found tables: {tables}")
                
                # Check if license table exists and has structure
                if 'licenses' in tables:
                    print("🔍 Checking licenses table structure...")
                    columns = inspector.get_columns('licenses')
                    print(f"📋 License table columns: {[col['name'] for col in columns]}")
                
                print("\n🎉 Remote database initialization complete!")
                print("📋 Database is ready for license generation!")
                
                return True
                
            except Exception as e:
                print(f"❌ Error initializing database: {e}")
                print(f"❌ Error type: {type(e).__name__}")
                db.session.rollback()
                return False
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("❌ Make sure you're in the correct directory with virtual environment activated")
        return False

def generate_test_licenses():
    """Generate some test licenses after initialization"""
    print("\n🎯 Generating test licenses...")
    
    try:
        from app import create_app
        from app.models import db, License
        from datetime import datetime, timedelta
        import json
        import secrets
        import string
        
        app = create_app()
        
        with app.app_context():
            # Generate 5 test licenses
            print("📝 Generating 5 test licenses...")
            
            for i in range(5):
                random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
                license_key = f"GREED-{random_part[:4]}-{random_part[4:8]}-{random_part[8:12]}-{random_part[12:16]}"
                
                license = License(
                    license_key=license_key,
                    product_id="GREED-TOOL",
                    max_activations=1,
                    expires_at=datetime.utcnow() + timedelta(days=365),
                    license_metadata=json.dumps({
                        "features": ["arena_reset", "lobby"],
                        "version": "1.0.0",
                        "product_name": "GreedTool"
                    })
                )
                
                db.session.add(license)
            
            db.session.commit()
            print("✅ 5 test licenses created successfully!")
            
            # Show the licenses
            licenses = License.query.all()
            print("\n📋 Generated licenses:")
            for i, lic in enumerate(licenses, 1):
                print(f"{i}. {lic.license_key}")
                print(f"   Product: {lic.product_id}")
                print(f"   Expires: {lic.expires_at.date()}")
                print()
                
    except Exception as e:
        print(f"❌ Error generating test licenses: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("REMOTE DATABASE INITIALIZATION")
    print("=" * 60)
    
    # Initialize database
    success = init_remote_database()
    
    if success:
        # Ask if user wants to generate test licenses
        response = input("\n🤔 Generate 5 test licenses? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            generate_test_licenses()
        
        print("\n🎉 All done! Your remote database is ready!")
        print("🌐 You can now use your license server web interface!")
    else:
        print("\n❌ Database initialization failed!")
        print("🔧 Check your database connection and try again.")
        sys.exit(1)
