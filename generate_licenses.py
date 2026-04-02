from app import create_app
from app.models import db, License
from datetime import datetime, timedelta
import json
import secrets
import string
from sqlalchemy import text

def generate_licenses(count=10, product="GREED-TOOL"):
    print(f"🚀 Starting license generation for {product}...")
    
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
            
            print(f"📝 Generating {count} licenses for {product}...")
            
            licenses_generated = 0
            
            for i in range(count):
                # Generate random license key
                random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
                if product == "MAXGreed":
                    license_key = f"MAXG-{random_part[:4]}-{random_part[4:8]}-{random_part[8:12]}-{random_part[12:16]}"
                else:
                    license_key = f"GREED-{random_part[:4]}-{random_part[4:8]}-{random_part[8:12]}-{random_part[12:16]}"
                
                # Set features based on product type
                if product == "MAXGreed":
                    features = ["arena_reset", "lobby", "unlimited_activations"]
                    max_activations = 5
                else:
                    features = ["arena_reset", "lobby"]
                    max_activations = 1
                
                # Create license
                license = License(
                    license_key=license_key,
                    product_id=product,
                    max_activations=max_activations,
                    expires_at=datetime.utcnow() + timedelta(days=365),
                    license_metadata=json.dumps({
                        "features": features,
                        "version": "2.0.0" if product == "MAXGreed" else "1.0.0",
                        "product_name": "MaxGreed" if product == "MAXGreed" else "GreedTool"
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
            
            print(f"\n🎉 Successfully generated {licenses_generated} licenses for {product}!")
            
            # Show first 5 licenses
            print("\n📋 Sample licenses (first 5):")
            print("-" * 50)
            for i, lic in enumerate(License.query.filter_by(product_id=product).limit(5).all()):
                print(f"{i+1}. {lic.license_key}")
                print(f"   Product: {lic.product_id}")
                print(f"   Expires: {lic.expires_at.date()}")
                print()
                
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    product = sys.argv[2] if len(sys.argv) > 2 else "GREED-TOOL"
    generate_licenses(count, product)