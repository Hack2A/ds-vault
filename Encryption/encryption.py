import os
import secrets
import hmac as hmac_module
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from hashlib import sha256
from Encryption.crypto_constants import AES_KEY_LENGTH, AES_NONCE_LENGTH


class AESGCMEncryption:
    
    @staticmethod
    def generate_nonce(length: int = AES_NONCE_LENGTH) -> bytes:
        return secrets.token_bytes(length)
    
    @staticmethod
    def encrypt_data(plaintext: bytes, key: bytes, associated_data: bytes = None) -> tuple:
        if len(key) != AES_KEY_LENGTH:
            raise ValueError(f"Key must be {AES_KEY_LENGTH} bytes")
        
        nonce = AESGCMEncryption.generate_nonce()
        cipher = AESGCM(key)
        
        ciphertext = cipher.encrypt(nonce, plaintext, associated_data)
        
        return ciphertext, nonce
    
    @staticmethod
    def decrypt_data(ciphertext: bytes, key: bytes, nonce: bytes, associated_data: bytes = None) -> tuple:
        if len(key) != AES_KEY_LENGTH:
            raise ValueError(f"Key must be {AES_KEY_LENGTH} bytes")
        
        if len(nonce) != AES_NONCE_LENGTH:
            raise ValueError(f"Nonce must be {AES_NONCE_LENGTH} bytes")
        
        cipher = AESGCM(key)
        
        try:
            plaintext = cipher.decrypt(nonce, ciphertext, associated_data)
            return True, plaintext
        except Exception:
            return False, None
    
    @staticmethod
    def encrypt_file(file_path: str, key: bytes) -> tuple:
        with open(file_path, 'rb') as f:
            plaintext = f.read()
        
        ciphertext, nonce = AESGCMEncryption.encrypt_data(plaintext, key)
        
        return ciphertext, nonce
    
    @staticmethod
    def decrypt_file(ciphertext: bytes, key: bytes, nonce: bytes) -> tuple:
        success, plaintext = AESGCMEncryption.decrypt_data(ciphertext, key, nonce)
        
        if not success:
            return False, None
        
        return True, plaintext
    
    @staticmethod
    def compute_file_hash(file_data: bytes) -> bytes:
        return sha256(file_data).digest()


class ConstantTimeComparison:
    
    @staticmethod
    def compare_bytes(a: bytes, b: bytes) -> bool:
        return hmac_module.compare_digest(a, b)
    
    @staticmethod
    def compare_strings(a: str, b: str) -> bool:
        return hmac_module.compare_digest(a.encode(), b.encode())

class FileEncryption:
    
    @staticmethod
    def compute_file_hash(file_data: bytes) -> str:
        return sha256(file_data).hexdigest()
    
    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=AES_KEY_LENGTH,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())

    @staticmethod
    def encrypt_file(file_data: bytes, password: str) -> tuple:
        salt = os.urandom(16)
        key = FileEncryption._derive_key(password, salt)
        
        ciphertext, nonce = AESGCMEncryption.encrypt_data(file_data, key)
        
        # hmac_tag was used to store nonce in v1
        return ciphertext, salt, nonce
    
    @staticmethod
    def decrypt_file(encrypted_data: bytes, password: str, salt: bytes, hmac_tag: bytes) -> tuple:
        key = FileEncryption._derive_key(password, salt)
        # hmac_tag is exactly the nonce
        success, plaintext = AESGCMEncryption.decrypt_data(encrypted_data, key, hmac_tag)
        return success, plaintext
