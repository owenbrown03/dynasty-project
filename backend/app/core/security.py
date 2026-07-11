from cryptography.fernet import Fernet
from app.core.config import settings

cipher = Fernet(settings.encryption_key_bytes)

def encrypt_token(token: str) -> str:
    return cipher.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    return cipher.decrypt(encrypted_token.encode()).decode()
