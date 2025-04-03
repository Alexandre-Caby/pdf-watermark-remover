from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import json
from dotenv import load_dotenv
import os

# Load variables
load_dotenv()

# Retrieve and validate the secret key from the environment
_APP_SECRET_KEY = os.environ.get("APP_SECRET_KEY")
if not _APP_SECRET_KEY:
    raise ValueError("APP_SECRET_KEY environment variable must be set.")
_SECRET_KEY = _APP_SECRET_KEY.encode('utf-8')
if len(_SECRET_KEY) != 32:
    raise ValueError("APP_SECRET_KEY must be 32 bytes long.")

# Retrieve the activation salt from the environment
ACTIVATION_SALT = os.environ.get("ACTIVATION_SALT", "DefaultSalt1234")

def _pad(data: bytes) -> bytes:
    pad_len = AES.block_size - len(data) % AES.block_size
    return data + bytes([pad_len]) * pad_len

def _unpad(data: bytes) -> bytes:
    pad_len = data[-1]
    return data[:-pad_len]

def encrypt_activation_data(data: dict) -> str:
    plaintext = json.dumps(data).encode('utf-8')
    plaintext = _pad(plaintext)
    nonce = get_random_bytes(12)  # Recommended nonce size for GCM
    cipher = AES.new(_SECRET_KEY, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    # Combine nonce, tag, and ciphertext
    encrypted = nonce + tag + ciphertext
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_activation_data(encoded_data: str) -> dict:
    encrypted = base64.b64decode(encoded_data)
    nonce = encrypted[:12]
    tag = encrypted[12:28]
    ciphertext = encrypted[28:]
    cipher = AES.new(_SECRET_KEY, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    plaintext = _unpad(plaintext)
    return json.loads(plaintext.decode('utf-8'))