from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import json
import os
import logging

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try to find .env in the PyInstaller bundle
    import sys
    import os
    
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        env_path = os.path.join(bundle_dir, '.env')
        load_dotenv(env_path)
    else:
        # Running in a normal Python environment
        load_dotenv()
except ImportError:
    # Silent fail if dotenv is not available in compiled program
    pass

# Setup secure logging to avoid leaking sensitive information
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Retrieve the secret key from the environment
_APP_SECRET_KEY = os.environ.get("APP_SECRET_KEY")
if not _APP_SECRET_KEY:
    logging.error("APP_SECRET_KEY environment variable is missing")
    raise ValueError("Required security configuration is missing.")

# Convert key to bytes and validate length
_SECRET_KEY = _APP_SECRET_KEY.encode('utf-8')
if len(_SECRET_KEY) != 32:
    logging.error("APP_SECRET_KEY has incorrect length")
    raise ValueError("Security configuration is invalid.")

# Retrieve the activation salt from the environment
ACTIVATION_SALT = os.environ.get("ACTIVATION_SALT")
if not ACTIVATION_SALT:
    logging.error("ACTIVATION_SALT environment variable is missing")
    raise ValueError("Required security configuration is missing.")

def _pad(data: bytes) -> bytes:
    """Add PKCS#7 padding to data for use with AES."""
    pad_len = AES.block_size - len(data) % AES.block_size
    return data + bytes([pad_len]) * pad_len

def _unpad(data: bytes) -> bytes:
    """Remove PKCS#7 padding from data."""
    pad_len = data[-1]
    return data[:-pad_len]

def encrypt_activation_data(data: dict) -> str:
    """
    Encrypt activation data with AES-GCM.
    """
    try:
        plaintext = json.dumps(data).encode('utf-8')
        plaintext = _pad(plaintext)
        nonce = get_random_bytes(12)
        cipher = AES.new(_SECRET_KEY, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        # Combine nonce, tag, and ciphertext
        encrypted = nonce + tag + ciphertext
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        logging.error(f"Encryption error: {type(e).__name__}")
        raise ValueError("Failed to process activation data")

def decrypt_activation_data(encoded_data: str) -> dict:
    """
    Decrypt activation data with AES-GCM.
    """
    try:
        encrypted = base64.b64decode(encoded_data)
        nonce = encrypted[:12]
        tag = encrypted[12:28]
        ciphertext = encrypted[28:]
        cipher = AES.new(_SECRET_KEY, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        plaintext = _unpad(plaintext)
        return json.loads(plaintext.decode('utf-8'))
    except Exception as e:
        logging.error(f"Decryption error: {type(e).__name__}")
        raise ValueError("Invalid activation data")