import os
from cryptography.fernet import Fernet

SECRET_ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY").encode()
cipher = Fernet(SECRET_ENCRYPTION_KEY)

def encrypt_token(token: str) -> str:
    return cipher.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    return cipher.decrypt(encrypted_token.encode()).decode()