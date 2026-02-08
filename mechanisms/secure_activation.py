"""
Secure activation data encryption/decryption module.

Uses AES-256-GCM for authenticated encryption of activation data.
Secrets are loaded from environment variables (injected at build time).
"""

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import json
import logging
import os
import sys

logger = logging.getLogger("watermark_app.crypto")

# Try to load environment variables from .env file (dev mode fallback)
try:
    from dotenv import load_dotenv

    if getattr(sys, 'frozen', False):
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
        env_path = os.path.join(bundle_dir, '.env')
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass

# Import secrets via _secrets module (XOR-obfuscated in prod, env-var in dev)
from mechanisms._secrets import get_app_secret_key, get_activation_salt

_APP_SECRET_KEY = get_app_secret_key()
if not _APP_SECRET_KEY:
    logger.error("APP_SECRET_KEY is missing")
    raise ValueError("Required security configuration is missing.")

_SECRET_KEY: bytes = _APP_SECRET_KEY.encode('utf-8')
if len(_SECRET_KEY) != 32:
    logger.error("APP_SECRET_KEY has incorrect length")
    raise ValueError("Security configuration is invalid.")

ACTIVATION_SALT: str = get_activation_salt()
if not ACTIVATION_SALT:
    logger.error("ACTIVATION_SALT is missing")
    raise ValueError("Required security configuration is missing.")


def _has_pkcs7_padding(data: bytes) -> bool:
    """Detect whether *data* has valid PKCS#7 padding.

    Used only for backward-compatible decryption of files that were
    encrypted with the previous version which applied unnecessary padding.
    """
    if not data:
        return False
    pad_len = data[-1]
    if pad_len < 1 or pad_len > AES.block_size:
        return False
    return data[-pad_len:] == bytes([pad_len]) * pad_len


def encrypt_activation_data(data: dict) -> str:
    """Encrypt activation data with AES-256-GCM.

    AES-GCM is a stream-based authenticated encryption mode and does
    not require padding.  Previous versions incorrectly applied
    PKCS#7 padding; this has been removed for new encryptions while
    decryption retains backward compatibility (see decrypt_activation_data).

    Args:
        data: Dictionary of activation fields (machine_id, expiry_date, etc.).

    Returns:
        Base64-encoded string of nonce + tag + ciphertext.
    """
    try:
        plaintext = json.dumps(data).encode('utf-8')
        nonce = get_random_bytes(12)
        cipher = AES.new(_SECRET_KEY, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        encrypted = nonce + tag + ciphertext
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as exc:
        logger.error("Encryption error: %s", type(exc).__name__)
        raise ValueError("Failed to process activation data") from exc


def decrypt_activation_data(encoded_data: str) -> dict:
    """Decrypt activation data with AES-256-GCM.

    Handles backward compatibility: if the decrypted plaintext has
    valid PKCS#7 padding (from the old encryption code), it is stripped
    automatically.

    Args:
        encoded_data: Base64-encoded encrypted string.

    Returns:
        Parsed activation data dictionary.
    """
    try:
        encrypted = base64.b64decode(encoded_data)
        nonce = encrypted[:12]
        tag = encrypted[12:28]
        ciphertext = encrypted[28:]
        cipher = AES.new(_SECRET_KEY, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        # Strip legacy PKCS#7 padding if present
        if _has_pkcs7_padding(plaintext):
            plaintext = plaintext[:-plaintext[-1]]
        return json.loads(plaintext.decode('utf-8'))
    except Exception as exc:
        logger.error("Decryption error: %s", type(exc).__name__)
        raise ValueError("Invalid activation data") from exc
