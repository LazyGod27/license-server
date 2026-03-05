import hashlib
import time
import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

def generate_encryption_key():
    """Generate encryption key similar to client implementation"""
    # Use server-side seed + time for key generation
    server_seed = "GREEDTOOL_SERVER_V2"
    time_seed = str(int(time.time()))
    hw_seed = server_seed + time_seed
    
    # Generate hash similar to client
    hash_obj = hashlib.sha256(hw_seed.encode()).digest()
    key = bytes(b ^ 0x5A for b in hash_obj[:32])
    return key

def decrypt_data(encrypted_data):
    """Decrypt data from client"""
    if not encrypted_data:
        return encrypted_data
    
    try:
        # Convert from base64 if needed
        if isinstance(encrypted_data, str):
            try:
                encrypted_bytes = base64.b64decode(encrypted_data)
            except:
                encrypted_bytes = encrypted_data.encode('latin1')
        else:
            encrypted_bytes = encrypted_data
        
        # Remove padding (last byte indicates padding size)
        if len(encrypted_bytes) > 0:
            padding_size = encrypted_bytes[-1]
            if padding_size > 0 and padding_size <= len(encrypted_bytes):
                encrypted_bytes = encrypted_bytes[:-padding_size]
        
        # Generate key and decrypt
        key = generate_encryption_key()
        data = bytearray(encrypted_bytes)
        
        # Reverse encryption rounds (3 rounds)
        for round_num in range(2, -1, -1):
            for i in range(len(data)):
                # Reverse bit shifting
                data[i] = (data[i] >> 2) | (data[i] << 6) & 0xFF
                data[i] ^= key[i % len(key)] ^ (round_num + 1)
        
        return data.decode('utf-8')
    except Exception as e:
        # If decryption fails, return original data (might be old format)
        return encrypted_data

def verify_signature(data, signature):
    """Verify request signature"""
    try:
        expected_signature = hashlib.sha256((data + "GREEDTOOL_SECRET").encode()).hexdigest()
        return secrets.compare_digest(expected_signature, signature)
    except:
        return False

def is_new_format(data):
    """Check if request is using new encrypted format"""
    return 'd' in data and 's' in data and 'sig' in data
