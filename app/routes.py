from flask import request, jsonify, current_app, send_from_directory, session, redirect, url_for
from .models import License, Activation, AuditLog
from datetime import datetime, timedelta
from . import db
import time
import json
import hashlib
import hmac
import jwt
from cryptography.fernet import Fernet
from functools import wraps
import os
import redis
from .crypto_utils import decrypt_data, verify_signature, is_new_format
from .security import security_check, rate_limit, log_security_event, detect_automation

def register_routes(app):

    # Initialize Redis for brute force protection
    try:
        # Debug: Print environment variables
        print(f"🔍 DEBUG - REDIS_URL: {os.getenv('REDIS_URL', 'NOT_SET')}")
        print(f"🔍 DEBUG - REDIS_HOST: {os.getenv('REDIS_HOST', 'NOT_SET')}")
        print(f"🔍 DEBUG - REDIS_PORT: {os.getenv('REDIS_PORT', 'NOT_SET')}")
        print(f"🔍 DEBUG - REDIS_PASSWORD: {'SET' if os.getenv('REDIS_PASSWORD') else 'NOT_SET'}")
        
        # Try REDIS_URL first (works with both Railway and Render)
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            print("🔗 Using REDIS_URL format")
            # Render Redis URLs work directly with redis.from_url
            redis_client = redis.from_url(redis_url, decode_responses=True)
        else:
            # Fallback to separate variables
            print("🔧 Using separate Redis variables")
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                password=os.getenv('REDIS_PASSWORD'),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        
        # Test connection
        redis_client.ping()
        print("✅ Redis connected for brute force protection")
    except Exception as e:
        print(f"⚠️ Redis connection failed, falling back to memory: {e}")
        redis_client = None
        # Fallback to in-memory storage
        failed_attempts = {}
    
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check for session authentication
            if 'admin_authenticated' not in session or not session['admin_authenticated']:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated_function

    def check_brute_force(ip_address):
        """Check if IP should be blocked due to too many failed attempts"""
        if redis_client:
            try:
                # Use Redis for tracking
                key = f"failed_login:{ip_address}"
                attempts = redis_client.lrange(key, 0, -1)
                
                # Clean old entries (older than 15 minutes)
                now = datetime.utcnow().timestamp()
                recent_attempts = [
                    attempt_time for attempt_time in attempts
                    if now - float(attempt_time) < 900  # 15 minutes = 900 seconds
                ]
                
                # Update Redis with only recent attempts
                redis_client.delete(key)
                if recent_attempts:
                    redis_client.lpush(key, *recent_attempts)
                    redis_client.expire(key, 900)  # Auto-expire after 15 minutes
                
                # Check if too many attempts (more than 5 in 15 minutes)
                return len(recent_attempts) >= 5
            except Exception as e:
                print(f"Redis error in check_brute_force: {e}")
                # Fallback to allowing request if Redis fails
                return False
        else:
            # Fallback to in-memory storage
            now = datetime.utcnow()
            if ip_address in failed_attempts:
                failed_attempts[ip_address] = [
                    attempt_time for attempt_time in failed_attempts[ip_address]
                    if now - attempt_time < timedelta(minutes=15)
                ]
            
            if ip_address in failed_attempts and len(failed_attempts[ip_address]) >= 5:
                return True
            return False

    def record_failed_attempt(ip_address):
        """Record a failed login attempt"""
        if redis_client:
            try:
                # Use Redis for tracking
                key = f"failed_login:{ip_address}"
                redis_client.lpush(key, str(datetime.utcnow().timestamp()))
                redis_client.expire(key, 900)  # Auto-expire after 15 minutes
            except Exception as e:
                print(f"Redis error in record_failed_attempt: {e}")
                # Fallback - do nothing if Redis fails
                pass
        else:
            # Fallback to in-memory storage
            if ip_address not in failed_attempts:
                failed_attempts[ip_address] = []
            failed_attempts[ip_address].append(datetime.utcnow())

    def get_failed_attempts_count(ip_address):
        """Get current failed attempts count for an IP"""
        if redis_client:
            try:
                key = f"failed_login:{ip_address}"
                attempts = redis_client.lrange(key, 0, -1)
                now = datetime.utcnow().timestamp()
                recent_attempts = [
                    attempt_time for attempt_time in attempts
                    if now - float(attempt_time) < 900
                ]
                return len(recent_attempts)
            except:
                return 0
        else:
            if ip_address not in failed_attempts:
                return 0
            now = datetime.utcnow()
            recent_attempts = [
                attempt_time for attempt_time in failed_attempts[ip_address]
                if now - attempt_time < timedelta(minutes=15)
            ]
            return len(recent_attempts)

    def clear_failed_attempts(ip_address):
        """Clear failed attempts for an IP (on successful login)"""
        if redis_client:
            try:
                key = f"failed_login:{ip_address}"
                redis_client.delete(key)
            except Exception as e:
                print(f"Redis error in clear_failed_attempts: {e}")
        else:
            if ip_address in failed_attempts:
                del failed_attempts[ip_address]

    # SIMPLE HOME PAGE - THIS FIXES THE 502 ERROR!
    @app.route('/')
    def home():
        return {"status": "online", "message": "License Server Running"}
    
    @app.route('/admin/api/login', methods=['POST'])
    def admin_login():
        """Handle admin login with brute force protection"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Get client IP
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Check for brute force
        if check_brute_force(client_ip):
            log_security_event('BRUTE_FORCE_BLOCK', f'IP: {client_ip}', 'WARNING')
            return jsonify({
                'error': 'Too many failed attempts. Please wait 15 minutes before trying again.',
                'retry_after': 900  # 15 minutes in seconds
            }), 429  # Too Many Requests
        
        # Default admin credentials (you should change these)
        ADMIN_USERNAME = 'filbertace'
        ADMIN_PASSWORD = 'eca@09976944805'  # Change this to a secure password
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # Clear failed attempts on successful login
            clear_failed_attempts(client_ip)
            
            # Create session
            session['admin_authenticated'] = True
            session['admin_login_time'] = datetime.utcnow().isoformat()
            
            # Generate token for additional security
            token = jwt.encode({
                'user': username,
                'login_time': session['admin_login_time'],
                'exp': datetime.utcnow().timestamp() + 3600  # 1 hour expiry
            }, app.config['JWT_SECRET'], algorithm='HS256')
            
            log_security_event('ADMIN_LOGIN', f'User: {username} IP: {client_ip}', 'INFO')
            
            return jsonify({
                'success': True,
                'token': token,
                'message': 'Login successful'
            })
        else:
            # Record failed attempt
            record_failed_attempt(client_ip)
            
            remaining_attempts = 5 - get_failed_attempts_count(client_ip)
            log_security_event('ADMIN_LOGIN_FAILED', f'User: {username} IP: {client_ip}', 'WARNING')
            
            return jsonify({
                'error': 'Invalid credentials',
                'remaining_attempts': max(0, remaining_attempts)
            }), 401
    
    @app.route('/admin/api/logout', methods=['POST'])
    def admin_logout():
        """Handle admin logout"""
        session.clear()
        log_security_event('ADMIN_LOGOUT', 'Session cleared', 'INFO')
        return jsonify({'success': True, 'message': 'Logged out successfully'})

    @app.route('/admin/logout')
    def admin_logout_redirect():
        """Direct logout via URL - clears session and redirects to login (escape hatch)"""
        session.clear()
        log_security_event('ADMIN_LOGOUT', 'Session cleared via /admin/logout', 'INFO')
        return redirect(url_for('admin_panel'))
    
    @app.route('/api/v1/verify', methods=['POST'])
    @rate_limit(max_requests=10, window_seconds=60)  # RE-ENABLE RATE LIMITING
    def verify_license():
        # Security checks - RE-ENABLE GRADUALLY
        security_valid, security_error = security_check()
        if not security_valid:
            log_security_event('SECURITY_BLOCK', security_error, 'WARNING')
            return jsonify({'error': security_error}), 400
        
        # Detect automation - TEMPORARILY DISABLED FOR TESTING
        # is_automation, automation_reason = detect_automation()
        # if is_automation:
        #     log_security_event('AUTOMATION_DETECTED', automation_reason, 'WARNING')
        #     # Don't block immediately, but log for monitoring
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Check if using new encrypted format - RE-ENABLE NEW FORMAT
        if is_new_format(data):
            # New encrypted format
            try:
                # Verify signature first
                json_str = json.dumps({k: v for k, v in data.items() if k != 'sig'})
                if not verify_signature(json_str, data.get('sig', '')):
                    log_security_event('INVALID_SIGNATURE', f'IP: {request.remote_addr}', 'WARNING')
                    return jsonify({'error': 'Invalid signature'}), 401
                
                # Get hardware data first for key generation
                hardware_data = data.get('h', {})
                hwid_string = f"{hardware_data.get('c', '')}|{hardware_data.get('m', '')}"
                hardware_id = hashlib.sha256(hwid_string.encode()).hexdigest()
                
                # Decrypt sensitive data with hardware-specific key
                license_key = decrypt_data(data.get('d', ''), hardware_id)
                username = decrypt_data(data.get('u', ''), hardware_id) if data.get('u') else ''
                
                # Verify session token (basic check)
                session_token = data.get('s', '')
                if not session_token:
                    return jsonify({'error': 'Missing session token'}), 400
                
                log_security_event('ENCRYPTED_REQUEST', f'License: {license_key[:8]}...', 'INFO')
                
            except Exception as e:
                log_security_event('DECRYPTION_FAILED', str(e), 'ERROR')
                return jsonify({'error': f'Decryption failed: {str(e)}'}), 400
        else:
            # Old format for backward compatibility (client sends hwid, license_key, username)
            license_key = data.get('license_key')
            username = data.get('username', '')
            hardware_data = data.get('hardware_data') or data.get('hwid', '')
            if hardware_data is None:
                hardware_data = {}
            log_security_event('LEGACY_REQUEST', f'License: {license_key[:8]}...', 'INFO')
        
        # Product validation - clients must send product_id
        product_id = data.get('product_id') if isinstance(data, dict) else None
        if not product_id:
            return jsonify({'error': 'Missing product_id'}), 400
        if product_id not in ('ARENA-RESET', 'GREED-TOOL', 'LOBBY-GREED'):
            return jsonify({'error': 'Invalid product_id'}), 400
        
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
        
        # Product must match - Arena Reset licenses only work in Arena Reset, Greed Tool licenses only in Greed Tool
        if license.product_id != product_id:
            log_security_event('PRODUCT_MISMATCH', f'License: {license_key} expected {license.product_id}, got {product_id}', 'WARNING')
            return jsonify({'error': f'This license is for {license.product_id}, not {product_id}'}), 401
        
        if datetime.utcnow() > license.expires_at:
            log_security_event('EXPIRED_LICENSE', f'License: {license_key}', 'WARNING')
            return jsonify({'error': 'License expired'}), 401
        
        # Generate hardware ID - FIX FOR OLD FORMAT
        if isinstance(hardware_data, str) and hardware_data:
            # Old format: hwid or hardware_data as string
            hwid_string = hardware_data
        elif isinstance(hardware_data, dict):
            # New format: hardware_data is a dict
            hwid_string = f"{hardware_data.get('c', '')}|{hardware_data.get('m', '')}" or 'fallback'
        else:
            hwid_string = 'unknown'
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
    @admin_required
    def create_license():
        # Allow session auth (web UI) or API key (programmatic)
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key != app.config['ADMIN_API_KEY']:
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        
        # Generate license key with product-specific prefix
        import secrets
        import string
        product_id = data.get('product_id', 'GREED-TOOL')
        prefix = 'ARENA-' if product_id == 'ARENA-RESET' else ('LOBBY-' if product_id == 'LOBBY-GREED' else 'GREED-')
        alphabet = string.ascii_uppercase + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(16))
        license_key = f"{prefix}{random_part[:4]}-{random_part[4:8]}-{random_part[8:12]}-{random_part[12:16]}"
        
        from datetime import datetime, timedelta
        expires_at = datetime.fromisoformat(data.get('expires_at', '2025-12-31'))
        
        license = License(
            license_key=license_key,
            product_id=product_id,
            max_activations=data.get('max_activations', 1),
            expires_at=expires_at,
            license_metadata=json.dumps(data.get('features', {}))
        )
        
        db.session.add(license)
        db.session.commit()
        
        return jsonify({'license_key': license_key})
    
    @app.route('/admin/api/stats', methods=['GET'])
    @admin_required
    def get_stats():
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key != app.config['ADMIN_API_KEY']:
            return jsonify({'error': 'Unauthorized'}), 401
        
        stats = {
            'total_licenses': License.query.count(),
            'active_licenses': License.query.filter_by(is_active=True).count(),
            'total_activations': Activation.query.count()
        }
        
        return jsonify(stats)
    
    @app.route('/admin/api/licenses/<license_key>/revoke', methods=['POST'])
    @admin_required
    def revoke_license(license_key):
        """Revoke a license so it can't be used anymore"""
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key != app.config['ADMIN_API_KEY']:
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
    
    @app.route('/admin/api/licenses/<license_key>/delete', methods=['DELETE'])
    @admin_required
    def delete_license(license_key):
        """Delete a revoked license permanently"""
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key != app.config['ADMIN_API_KEY']:
            return jsonify({'error': 'Unauthorized'}), 401
        
        license = License.query.filter_by(license_key=license_key).first()
        if not license:
            return jsonify({'error': 'License not found'}), 404
        
        # Only allow deletion of revoked licenses
        if license.is_active:
            return jsonify({'error': 'Cannot delete active license. Revoke it first.'}), 400
        
        # Delete all activations first
        Activation.query.filter_by(license_id=license.id).delete()
        
        # Delete the license
        db.session.delete(license)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'License deleted permanently'})
    
    @app.route('/admin/api/licenses', methods=['GET'])
    @admin_required
    def list_licenses():
        """List all licenses with activation details"""
        try:
            print("🔍 DEBUG: list_licenses called - fetching licenses...")
            licenses = License.query.all()
            result = []
            
            for lic in licenses:
                # Get activation details
                activations = []
                for activation in lic.activations:
                    if not activation.is_revoked:
                        activations.append({
                            'hardware_id': activation.hardware_id,
                            'ip_address': activation.ip_address,
                            'last_seen': activation.last_seen.isoformat() if activation.last_seen else None
                        })
                
                result.append({
                    'license_key': lic.license_key,
                    'username': lic.username or 'Unassigned',
                    'product_id': lic.product_id or 'GREED-TOOL',
                    'max_activations': lic.max_activations,
                    'activation_count': len([a for a in lic.activations if not a.is_revoked]),
                    'expires_at': lic.expires_at.isoformat(),
                    'is_active': lic.is_active,
                    'activations': activations
                })
            
            print(f"🔍 DEBUG: Returning {len(result)} licenses")
            return jsonify({'licenses': result})
        except Exception as e:
            print(f"🔍 ERROR in list_licenses: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Failed to load licenses'}), 500
    
    @app.route('/admin')
    def admin_panel():
        """Redirect to login or serve admin dashboard"""
        # Check if authenticated via session
        print(f"🔍 DEBUG - Session data: {dict(session)}")
        print(f"🔍 DEBUG - admin_authenticated in session: {'admin_authenticated' in session}")
        print(f"🔍 DEBUG - admin_authenticated value: {session.get('admin_authenticated')}")
        
        if 'admin_authenticated' in session and session['admin_authenticated']:
            print("🔍 DEBUG - User is authenticated, serving admin.html")
            # Serve the admin dashboard
            template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
            return send_from_directory(template_dir, 'admin.html')
        else:
            print("🔍 DEBUG - User not authenticated, serving login page")
            # Redirect to login page
            template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
            return send_from_directory(template_dir, 'admin_login.html')
    
    @app.route('/admin/dashboard')
    def admin_dashboard():
        """Serve the admin UI (protected route)"""
        # Check if authenticated via session
        if 'admin_authenticated' not in session or not session['admin_authenticated']:
            # Redirect to login
            template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
            return send_from_directory(template_dir, 'admin_login.html')
        
        # Serve the admin dashboard
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        return send_from_directory(template_dir, 'admin.html')
