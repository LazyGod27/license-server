from app import create_app
from app.models import db, License
from datetime import datetime, timedelta
import json

def generate_licenses(count=10):
    app = create_app()
    
    with app.app_context():
        print(f"Generating {count} licenses...")
        
        for i in range(count):
            import secrets
            import string
            alphabet = string.ascii_uppercase + string.digits
            random_part = ''.join(secrets.choice(alphabet) for _ in range(16))
            license_key = f"GREED-{random_part[:4]}-{random_part[4:8]}-{random_part[8:12]}-{random_part[12:16]}"
            
            license = License(
                license_key=license_key,
                product_id="GREED-TOOL",
                max_activations=1,
                expires_at=datetime.utcnow() + timedelta(days=365),
                metadata=json.dumps({"features": ["arena_reset", "lobby"]})
            )
            
            db.session.add(license)
            
            if (i + 1) % 10 == 0:
                db.session.commit()
                print(f"Generated {i + 1} licenses...")
        
        db.session.commit()
        print(f"\n✅ Generated {count} licenses!")
        
        # Show first 5
        print("\nSample licenses:")
        for lic in License.query.limit(5).all():
            print(f"  {lic.license_key}")

if __name__ == "__main__":
    generate_licenses(20)