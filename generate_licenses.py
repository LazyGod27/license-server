from app import create_app, db
from app.models import License
from datetime import datetime, timedelta, timezone
import secrets
import string
import json

app = create_app()


def generate_licenses(count=10):

    with app.app_context():

        print(f"Generating {count} licenses...")

        alphabet = string.ascii_uppercase + string.digits

        for _ in range(count):

            random_part = ''.join(
                secrets.choice(alphabet) for _ in range(16)
            )

            license_key = f"GREED-{random_part[:4]}-{random_part[4:8]}-{random_part[8:12]}-{random_part[12:16]}"

            license_obj = License(
                license_key=license_key,
                product_id="GREED-TOOL",
                max_activations=1,
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                license_metadata=json.dumps({
                    "features": ["arena_reset", "lobby"]
                })
            )

            db.session.add(license_obj)

        db.session.commit()

        print("✅ Licenses generated!")


if __name__ == "__main__":
    generate_licenses(20)