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
import os
from .crypto_utils import decrypt_data, verify_signature, is_new_format
from .security import security_check, rate_limit, log_security_event, detect_automation

def register_routes(app):

    # SIMPLE HOME PAGE - THIS FIXES THE 502 ERROR!
    @app.route('/')
    def home():
        return {"status": "online", "message": "License Server Running"}
    
    @app.route('/api/v1/verify', methods=['POST'])
    @rate_limit(max_requests=10, window_seconds=60)
    def verify_license():
        # Security checks
        security_valid, security_error = security_check()
        if not security_valid:
            log_security_event('SECURITY_BLOCK', security_error, 'WARNING')
            return jsonify({'error': security_error}), 400
        
        # Detect automation
        is_automation, automation_reason = detect_automation()
        if is_automation:
            log_security_event('AUTOMATION_DETECTED', automation_reason, 'WARNING')
            # Don't block immediately, but log for monitoring
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Check if using new encrypted format
        if is_new_format(data):
            # New encrypted format
            try:
                # Verify signature first
                json_str = json.dumps({k: v for k, v in data.items() if k != 'sig'})
                if not verify_signature(json_str, data.get('sig', '')):
                    log_security_event('INVALID_SIGNATURE', f'IP: {request.remote_addr}', 'WARNING')
                    return jsonify({'error': 'Invalid signature'}), 401
                
                # Decrypt sensitive data
                license_key = decrypt_data(data.get('d', ''))
                username = decrypt_data(data.get('u', '')) if data.get('u') else ''
                
                # Get hardware data (not encrypted)
                hardware_data = data.get('h', {})
                
                # Verify session token (basic check)
                session_token = data.get('s', '')
                if not session_token:
                    return jsonify({'error': 'Missing session token'}), 400
                
                log_security_event('ENCRYPTED_REQUEST', f'License: {license_key[:8]}...', 'INFO')
                
            except Exception as e:
                log_security_event('DECRYPTION_FAILED', str(e), 'ERROR')
                return jsonify({'error': f'Decryption failed: {str(e)}'}), 400
        else:
            # Old format for backward compatibility
            license_key = data.get('license_key')
            username = data.get('username', '')
            hardware_data = data.get('hardware_data', {})
            log_security_event('LEGACY_REQUEST', f'License: {license_key[:8]}...', 'INFO')
        
        # Validate username (3-20 chars, alphanumeric)
        if username:
            if len(username) < 3 or len(username) > 20:
                return jsonify({'error': 'Username must be 3-20 characters'}), 400
            if not username.isalnum():
                return jsonify({'error': 'Username can only contain letters and numbers'}), 400
        
        # Find license
        license = License.query.filter_by(license_key=license_key).first()
        if not license:
            log_security_event('INVALID_LICENSE', f'Key: {license_key}', 'WARNING')
            return jsonify({'error': 'Invalid license'}), 401
        
        if not license.is_active:
            log_security_event('DEACTIVATED_LICENSE', f'License: {license_key}', 'WARNING')
            return jsonify({'error': 'License deactivated'}), 401
        
        if datetime.utcnow() > license.expires_at:
            log_security_event('EXPIRED_LICENSE', f'License: {license_key}', 'WARNING')
            return jsonify({'error': 'License expired'}), 401
        
        # Generate hardware ID
        hwid_string = f"{hardware_data.get('c', '')}|{hardware_data.get('m', '')}"
        hardware_id = hashlib.sha256(hwid_string.encode()).hexdigest()
        
        # Check activation
        activation = Activation.query.filter_by(
            license_id=license.id,
            hardware_id=hardware_id
        ).first()
        
        if activation:
            if activation.is_revoked:
                log_security_event('REVOKED_ACTIVATION', f'License: {license_key}', 'WARNING')
                return jsonify({'error': 'Activation revoked'}), 401
            activation.last_seen = datetime.utcnow()
            
            # If license is active, username shouldn't change
            if license.username and license.username != username:
                return jsonify({'error': 'License already assigned to different user'}), 401
                
        else:
            # Check max activations
            current_count = Activation.query.filter_by(
                license_id=license.id,
                is_revoked=False
            ).count()
            
            if current_count >= license.max_activations:
                log_security_event('MAX_ACTIVATIONS', f'License: {license_key}', 'WARNING')
                return jsonify({'error': 'Maximum activations reached'}), 401
            
            activation = Activation(
                license_id=license.id,
                hardware_id=hardware_id,
                ip_address=request.remote_addr
            )
            db.session.add(activation)
            
            # First activation - set username
            if not license.username:
                license.username = username
        
        db.session.commit()
        
        # Generate token
        token = jwt.encode({
            'license': license_key,
            'username': license.username,
            'hwid': hardware_id,
            'exp': datetime.utcnow().timestamp() + 86400
        }, app.config['JWT_SECRET'], algorithm='HS256')
        
        log_security_event('SUCCESSFUL_VERIFICATION', f'License: {license_key}', 'INFO')
        
        return jsonify({
            'valid': True,
            'token': token,
            'username': license.username,
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
                'username': lic.username,
                'activation_count': lic.activations.filter_by(is_revoked=False).count()
            })
        
        return jsonify({'licenses': result})
    
    @app.route('/admin')
    def admin_panel():
        """Serve the admin UI"""
        # Get the absolute path to templates directory
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        return send_from_directory(template_dir, 'admin.html')
