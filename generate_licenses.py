from app import create_app
from app.models import db, License
from datetime import datetime, timedelta
import json
import secrets
import string
from sqlalchemy import text

def generate_licenses(count=10):
    print("🚀 Starting license generation...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test connection first
            db.session.execute(text('SELECT 1')).scalar()
            print("✅ Database connected")
            
            # Create tables if they don't exist
            print("📦 Creating database tables if needed...")
            db.create_all()
            print("✅ Tables ready")
            
            print(f"📝 Generating {count} licenses...")
            
            licenses_generated = 0
            
            for i in range(count):
                # Generate random license key
                random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
                license_key = f"GREED-{random_part[:4]}-{random_part[4:8]}-{random_part[8:12]}-{random_part[12:16]}"
                
                # Create license
                license = License(
                    license_key=license_key,
                    product_id="GREED-TOOL",
                    max_activations=1,
                    expires_at=datetime.utcnow() + timedelta(days=365),
                    license_metadata=json.dumps({
                        "features": ["arena_reset", "lobby"],
                        "version": "1.0.0"
                    })
                )
                
                db.session.add(license)
                licenses_generated += 1
                
                # Commit in batches
                if (i + 1) % 5 == 0:
                    db.session.commit()
                    print(f"  ✅ Generated {i + 1} licenses...")
            
            # Final commit
            db.session.commit()
            
            print(f"\n🎉 Successfully generated {licenses_generated} licenses!")
            
            # Show the first 5 licenses
            print("\n📋 Sample licenses (first 5):")
            print("-" * 50)
            for i, lic in enumerate(License.query.limit(5).all()):
                print(f"{i+1}. {lic.license_key}")
                print(f"   Expires: {lic.expires_at.date()}")
                print()
                
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    generate_licenses(count)