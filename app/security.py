import time
import hashlib
import secrets
from functools import wraps
from flask import request, jsonify
import os

# Rate limiting with in-memory fallback (Redis optional)
try:
    import redis
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, db=0, decode_responses=True)
    r.ping()
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    # In-memory rate limiting fallback
    rate_limit_store = {}

# Rate limiting
def rate_limit(max_requests=10, window_seconds=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            
            if REDIS_AVAILABLE:
                # Redis implementation
                key = f"rate_limit:{client_ip}"
                try:
                    current_requests = r.incr(key)
                    if current_requests == 1:
                        r.expire(key, window_seconds)
                    
                    if current_requests > max_requests:
                        return jsonify({'error': 'Rate limit exceeded'}), 429
                except:
                    pass  # If Redis fails, allow request
            else:
                # In-memory fallback implementation
                import time
                current_time = time.time()
                
                # Clean up old entries
                expired_keys = []
                for key, (count, timestamp) in rate_limit_store.items():
                    if current_time - timestamp > window_seconds:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del rate_limit_store[key]
                
                # Check current rate
                ip_key = f"rate_limit:{client_ip}"
                if ip_key in rate_limit_store:
                    count, timestamp = rate_limit_store[ip_key]
                    if current_time - timestamp < window_seconds:
                        if count >= max_requests:
                            return jsonify({'error': 'Rate limit exceeded'}), 429
                        # Increment count
                        rate_limit_store[ip_key] = (count + 1, timestamp)
                    else:
                        # Reset window
                        rate_limit_store[ip_key] = (1, current_time)
                else:
                    # First request
                    rate_limit_store[ip_key] = (1, current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Request validation
def validate_request_headers():
    """Validate custom headers for enhanced security"""
    # Check for required custom headers in new format
    auth_header = request.headers.get('X-Custom-Auth')
    version_header = request.headers.get('X-Client-Version')
    
    # If using new format, require these headers
    if request.is_json and request.get_json():
        data = request.get_json()
        if 'd' in data:  # New encrypted format
            if auth_header != 'GreedToolSecure':
                return False, 'Missing or invalid authentication header'
            if not version_header:
                return False, 'Missing client version header'
    
    return True, None

# IP reputation check
def check_ip_reputation():
    """Basic IP reputation checking"""
    client_ip = request.remote_addr
    
    # Block common proxy/VPN ranges (basic implementation)
    blocked_ranges = [
        '10.0.0.',  # Private networks
        '172.16.',  # Private networks  
        '192.168.', # Private networks
        '127.0.0.', # Localhost
    ]
    
    for blocked in blocked_ranges:
        if client_ip.startswith(blocked):
            return False, 'Blocked IP range'
    
    return True, None

# Request timing validation
def validate_request_timing():
    """Validate request timing to prevent replay attacks"""
    client_time = request.headers.get('X-Request-Time')
    if client_time:
        try:
            timestamp = float(client_time)
            current_time = time.time()
            
            # Allow 5 minute window
            if abs(current_time - timestamp) > 300:
                return False, 'Request timestamp out of range'
        except:
            return False, 'Invalid timestamp'
    
    return True, None

# Comprehensive security check
def security_check():
    """Perform all security checks"""
    # Check headers
    headers_valid, headers_error = validate_request_headers()
    if not headers_valid:
        return False, headers_error
    
    # Check IP reputation
    ip_valid, ip_error = check_ip_reputation()
    if not ip_valid:
        return False, ip_error
    
    # Check timing
    timing_valid, timing_error = validate_request_timing()
    if not timing_valid:
        return False, timing_error
    
    return True, None

# Audit logging
def log_security_event(event_type, details, severity='INFO'):
    """Log security events"""
    log_entry = {
        'timestamp': time.time(),
        'event_type': event_type,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'details': details,
        'severity': severity
    }
    
    # In production, this would go to a secure logging system
    print(f"SECURITY_LOG: {log_entry}")

# Anti-automation detection
def detect_automation():
    """Detect automated requests/bots"""
    user_agent = request.headers.get('User-Agent', '')
    
    # Basic bot detection
    bot_signatures = ['bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python']
    user_agent_lower = user_agent.lower()
    
    for signature in bot_signatures:
        if signature in user_agent_lower:
            return True, 'Suspicious user agent'
    
    return False, None
