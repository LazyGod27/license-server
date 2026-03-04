from flask import request, jsonify, current_app, send_from_directory
from .models import License, Activation, AuditLog
from datetime import datetime
from . import db
import time
import json
import hashlib
import hmac
import jwt
from cryptography.fernet import Fernet
from functools import wraps

def register_routes(app):

    # SIMPLE HOME PAGE - THIS FIXES THE 502 ERROR!
    @app.route('/')
    def home():
        return {"status": "online", "message": "License Server Running"}
    
    @app.route('/api/v1/verify', methods=['POST'])
    def verify_license():
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        license_key = data.get('license_key')
        hardware_data = data.get('hardware_data', {})
        
        # Find license
        license = License.query.filter_by(license_key=license_key).first()
        if not license:
            return jsonify({'error': 'Invalid license'}), 401
        
        if not license.is_active:
            return jsonify({'error': 'License deactivated'}), 401
        
        if datetime.utcnow() > license.expires_at:
            return jsonify({'error': 'License expired'}), 401
        
        # Generate hardware ID
        hwid_string = f"{hardware_data.get('cpu_id', '')}|{hardware_data.get('mac', '')}"
        hardware_id = hashlib.sha256(hwid_string.encode()).hexdigest()
        
        # Check activation
        activation = Activation.query.filter_by(
            license_id=license.id,
            hardware_id=hardware_id
        ).first()
        
        if activation:
            if activation.is_revoked:
                return jsonify({'error': 'Activation revoked'}), 401
            activation.last_seen = datetime.utcnow()
        else:
            # Check max activations
            current_count = Activation.query.filter_by(
                license_id=license.id,
                is_revoked=False
            ).count()
            
            if current_count >= license.max_activations:
                return jsonify({'error': 'Maximum activations reached'}), 401
            
            activation = Activation(
                license_id=license.id,
                hardware_id=hardware_id,
                ip_address=request.remote_addr
            )
            db.session.add(activation)
        
        # Generate token
        token = jwt.encode({
            'license': license_key,
            'hwid': hardware_id,
            'exp': datetime.utcnow().timestamp() + 86400
        }, app.config['JWT_SECRET'], algorithm='HS256')
        
        db.session.commit()
        
        return jsonify({
            'valid': True,
            'token': token,
            'features': json.loads(license.license_metadata or '{}'),
            'expires_at': license.expires_at.isoformat()
        })
    
    @app.route('/api/v1/heartbeat', methods=['POST'])
    def heartbeat():
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            return jsonify({'status': 'active'})
        except:
            return jsonify({'status': 'invalid'}), 401
    
    # Admin routes
    @app.route('/admin/api/licenses', methods=['POST'])
    def create_license():
        api_key = request.headers.get('X-API-Key')
        if api_key != app.config['ADMIN_API_KEY']:
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        
        # Generate license key
        import secrets
        import string
        alphabet = string.ascii_uppercase + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(16))
        license_key = f"GREED-{random_part[:4]}-{random_part[4:8]}-{random_part[8:12]}-{random_part[12:16]}"
        
        from datetime import datetime, timedelta
        expires_at = datetime.fromisoformat(data.get('expires_at', '2025-12-31'))
        
        license = License(
            license_key=license_key,
            product_id=data.get('product_id', 'GREED-TOOL'),
            max_activations=data.get('max_activations', 1),
            expires_at=expires_at,
            license_metadata=json.dumps(data.get('features', {}))
        )
        
        db.session.add(license)
        db.session.commit()
        
        return jsonify({'license_key': license_key})
    
    @app.route('/admin/api/stats', methods=['GET'])
    def get_stats():
        api_key = request.headers.get('X-API-Key')
        if api_key != app.config['ADMIN_API_KEY']:
            return jsonify({'error': 'Unauthorized'}), 401
        
        stats = {
            'total_licenses': License.query.count(),
            'active_licenses': License.query.filter_by(is_active=True).count(),
            'total_activations': Activation.query.count()
        }
        
        return jsonify(stats)
    
    @app.route('/admin/api/licenses/<license_key>/revoke', methods=['POST'])
    def revoke_license(license_key):
        """Revoke a license so it can't be used anymore"""
        api_key = request.headers.get('X-API-Key')
        if api_key != app.config['ADMIN_API_KEY']:
            return jsonify({'error': 'Unauthorized'}), 401
        
        license = License.query.filter_by(license_key=license_key).first()
        if not license:
            return jsonify({'error': 'License not found'}), 404
        
        # Mark as inactive
        license.is_active = False
        
        # Also revoke all activations
        for activation in license.activations:
            activation.is_revoked = True
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'License revoked'})
    
    @app.route('/admin/api/licenses', methods=['GET'])
    def list_licenses():
        """Get all licenses for admin panel"""
        api_key = request.headers.get('X-API-Key')
        if api_key != app.config['ADMIN_API_KEY']:
            return jsonify({'error': 'Unauthorized'}), 401
        
        licenses = License.query.all()
        result = []
        for lic in licenses:
            result.append({
                'license_key': lic.license_key,
                'product_id': lic.product_id,
                'max_activations': lic.max_activations,
                'expires_at': lic.expires_at.isoformat(),
                'is_active': lic.is_active,
                'activation_count': lic.activations.filter_by(is_revoked=False).count()
            })
        
        return jsonify({'licenses': result})
    
    @app.route('/admin')
    def admin_panel():
        """Serve the admin UI"""
        return send_from_directory('templates', 'admin.html')
